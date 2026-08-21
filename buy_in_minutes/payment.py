import base64
import hashlib
import hmac
import json
from urllib.parse import urlencode, urlparse
from urllib.error import HTTPError
from urllib.request import Request, urlopen

import frappe
from frappe import _
from frappe.utils import flt, get_url, getdate, nowdate
from erpnext.setup.doctype.brand.brand import get_brand_defaults
from erpnext.setup.doctype.item_group.item_group import get_item_group_defaults
from erpnext.stock.doctype.item.item import get_item_defaults
from buy_in_minutes.config import adaptive_pricing


STRIPE_API_BASE_URL = "https://api.stripe.com/v1"
DEFAULT_CURRENCY = "aed"
DELIVERY_FEE = 6
DELIVERY_FEE_ITEM_CODE = "delivery-fee"
FREE_DELIVERY_MINIMUM = 60
SELLING_PRICE_LIST = "Selling Price"
STRIPE_SETTINGS_DOCTYPE = "Stripe Settings"
CHECKOUT_RESUME_TOKEN_TTL_SECONDS = 3 * 60 * 60
DELIVERY_CHARGE_TAX_TEMPLATE = "Delivery Charge"


def _error(message, status_code=400):
	frappe.local.response["http_status_code"] = status_code
	return {"success": False, "message": message}


def _get_conf_value(key):
	value = frappe.conf.get(key)
	return value.strip() if isinstance(value, str) else value


def _get_checkout_resume_token_key(checkout_resume_token):
	return frappe.cache.make_key(f"buy_in_minutes:checkout_resume:{checkout_resume_token}")


def _create_checkout_resume_token(user_name, sales_order_name):
	checkout_resume_token = frappe.generate_hash(length=32)
	frappe.cache.setex(
		_get_checkout_resume_token_key(checkout_resume_token),
		CHECKOUT_RESUME_TOKEN_TTL_SECONDS,
		json.dumps(
			{
				"user": user_name,
				"sales_order": sales_order_name,
			}
		),
	)
	return checkout_resume_token


def _read_checkout_resume_token(checkout_resume_token):
	checkout_resume_token = _clean_text(checkout_resume_token)
	if not checkout_resume_token:
		frappe.throw(_("Missing checkout resume token."), frappe.AuthenticationError)

	cache_key = _get_checkout_resume_token_key(checkout_resume_token)
	payload = frappe.cache.get_value(cache_key)
	if isinstance(payload, bytes):
		payload = payload.decode()

	try:
		payload = json.loads(payload or "{}")
	except Exception:
		payload = {}

	if not payload.get("user") or not payload.get("sales_order"):
		frappe.throw(_("Checkout session expired. Please sign in again."), frappe.AuthenticationError)

	frappe.cache.delete_value(cache_key)
	return payload


def _get_user_payload(user_name):
	user = frappe.get_doc("User", user_name)
	return {
		"name": user.name,
		"email": user.email,
		"mobile_no": user.mobile_no,
		"full_name": user.full_name,
		"user_type": user.user_type,
		"user_image": user.user_image,
	}


def _restore_checkout_user(user_name, sales_order_name):
	user_name = _normalize_user_name(user_name)
	sales_order_name = _clean_text(sales_order_name)
	if user_name == "Guest" or not sales_order_name:
		frappe.throw(_("Unable to restore checkout session."), frappe.AuthenticationError)

	if not frappe.db.exists("User", user_name):
		frappe.throw(_("Checkout user was not found."), frappe.AuthenticationError)

	if frappe.db.get_value("User", user_name, "enabled") != 1:
		frappe.throw(_("Checkout user is disabled."), frappe.AuthenticationError)

	sales_order_owner = frappe.db.get_value("Sales Order", sales_order_name, "owner")
	if sales_order_owner != user_name:
		frappe.throw(_("Checkout session does not match this order."), frappe.AuthenticationError)

	if _normalize_user_name(frappe.session.user) != user_name:
		from buy_in_minutes.auth import _login_user

		_login_user(user_name)

	return _get_user_payload(user_name)


def _get_stripe_settings():
	if frappe.db.exists("DocType", STRIPE_SETTINGS_DOCTYPE):
		settings = frappe.get_single(STRIPE_SETTINGS_DOCTYPE)
		secret_key = settings.get_password("secret_key") if settings.secret_key else None
		webhook_secret = settings.get_password("webhook_secret") if settings.webhook_secret else None
		if settings.enabled and secret_key:
			stripe_currency = (
				settings.get("currency")
				or settings.get("default_currency")
				or DEFAULT_CURRENCY
			)
			return {
				"publishable_key": settings.publishable_key,
				"secret_key": secret_key,
				"webhook_secret": webhook_secret,
				"currency": stripe_currency.strip().lower(),
			}

	return {
		"publishable_key": _get_conf_value("stripe_publishable_key"),
		"secret_key": _get_conf_value("stripe_secret_key"),
		"webhook_secret": _get_conf_value("stripe_webhook_secret"),
		"currency": DEFAULT_CURRENCY,
	}


def _get_stripe_secret_key():
	secret_key = _get_stripe_settings().get("secret_key")
	if secret_key and not str(secret_key).startswith(("sk_test_", "sk_live_")):
		frappe.throw(
			_("Stripe secret key is invalid. Use a key that starts with sk_test_ or sk_live_.")
		)

	return secret_key


def _get_stripe_webhook_secret():
	return _get_stripe_settings().get("webhook_secret")


def _stripe_request(path, params):
	secret_key = _get_stripe_secret_key()
	if not secret_key:
		frappe.throw(_("Stripe secret key is not configured."))

	body = urlencode(params, doseq=True).encode()
	auth = base64.b64encode(f"{secret_key}:".encode()).decode()
	request = Request(
		f"{STRIPE_API_BASE_URL}{path}",
		data=body,
		headers={
			"Authorization": f"Basic {auth}",
			"Content-Type": "application/x-www-form-urlencoded",
		},
		method="POST",
	)

	try:
		with urlopen(request, timeout=30) as response:
			return json.loads(response.read().decode())
	except HTTPError as exc:
		error_body = exc.read().decode()
		frappe.log_error(title="Stripe Checkout Request Failed", message=frappe.get_traceback())
		try:
			error_data = json.loads(error_body)
			error_message = error_data.get("error", {}).get("message")
		except ValueError:
			error_message = None

		frappe.throw(error_message or _("Unable to start Stripe checkout. Please try again."))
	except Exception:
		frappe.log_error(title="Stripe Checkout Request Failed", message=frappe.get_traceback())
		frappe.throw(_("Unable to start Stripe checkout. Please try again."))


def _stripe_get_request(path):
	secret_key = _get_stripe_secret_key()
	if not secret_key:
		frappe.throw(_("Stripe secret key is not configured."))

	auth = base64.b64encode(f"{secret_key}:".encode()).decode()
	request = Request(
		f"{STRIPE_API_BASE_URL}{path}",
		headers={
			"Authorization": f"Basic {auth}",
		},
		method="GET",
	)

	try:
		with urlopen(request, timeout=30) as response:
			return json.loads(response.read().decode())
	except HTTPError as exc:
		error_body = exc.read().decode()
		frappe.log_error(title="Stripe Checkout Session Fetch Failed", message=frappe.get_traceback())
		try:
			error_data = json.loads(error_body)
			error_message = error_data.get("error", {}).get("message")
		except ValueError:
			error_message = None

		frappe.throw(error_message or _("Unable to verify Stripe payment. Please try again."))
	except Exception:
		frappe.log_error(title="Stripe Checkout Session Fetch Failed", message=frappe.get_traceback())
		frappe.throw(_("Unable to verify Stripe payment. Please try again."))


def _normalize_cart_items(cart_items):
	if isinstance(cart_items, str):
		cart_items = json.loads(cart_items)

	if not isinstance(cart_items, list) or not cart_items:
		frappe.throw(_("Cart is empty."))

	normalized_items = []
	for cart_item in cart_items:
		item_code = (cart_item.get("item_code") or cart_item.get("itemCode") or cart_item.get("id") or "").strip()
		quantity = frappe.utils.cint(cart_item.get("quantity"))
		supplier = _resolve_supplier_name(
			cart_item.get("supplier"),
			cart_item.get("supplier_name") or cart_item.get("supplierName"),
		)
		size = _clean_text(
			cart_item.get("size")
			or cart_item.get("selectedSize")
			or cart_item.get("custom_size")
			or cart_item.get("customSize")
		)

		if not item_code or quantity <= 0:
			frappe.throw(_("Cart contains an invalid item."))

		normalized_items.append(
			{
				"item_code": item_code,
				"quantity": quantity,
				"supplier": supplier,
				"size": size,
			}
		)

	return normalized_items


def _resolve_supplier_name(supplier=None, supplier_name=None):
	for value in (supplier, supplier_name):
		value = str(value or "").strip()
		if not value or value == "Supplier not set":
			continue

		if frappe.db.exists("Supplier", value):
			return value

		matched_supplier = frappe.db.get_value("Supplier", {"supplier_name": value}, "name")
		if matched_supplier:
			return matched_supplier

	return ""


def _clean_text(value):
	return str(value or "").strip()


def _normalize_delivery_fee(delivery_fee):
	if delivery_fee in (None, ""):
		return None

	return max(flt(delivery_fee), 0)


def _normalize_user_name(user_name, default="Guest"):
	user_name = _clean_text(user_name)
	if not user_name or user_name.lower() in {"guest", "none", "null"}:
		return default

	return user_name


def _get_item_selling_price(item_code, fallback_rate=0):
	price_record = frappe.db.get_value(
		"Item Price",
		{
			"item_code": item_code,
			"price_list": SELLING_PRICE_LIST,
			"selling": 1,
		},
		["price_list_rate"],
		as_dict=True,
	)

	if not price_record:
		price_record = frappe.db.get_value(
			"Item Price",
			{
				"item_code": item_code,
				"selling": 1,
			},
			["price_list_rate"],
			as_dict=True,
		)

	return flt(price_record.price_list_rate if price_record else fallback_rate)


def _get_default_company():
	company = frappe.defaults.get_user_default("Company") or frappe.defaults.get_global_default("company")
	if company:
		return company

	company = frappe.db.get_value("Company", {}, "name")
	if not company:
		frappe.throw(_("Please configure a default Company before checkout."))

	return company


def _get_non_group_default(doctype, setting_key, label):
	configured_value = frappe.defaults.get_global_default(setting_key)
	if configured_value:
		is_group = frappe.db.get_value(doctype, {"name": configured_value}, "is_group")
		if not is_group:
			return configured_value

	leaf_values = frappe.get_all(
		doctype,
		fields=["name"],
		filters={"is_group": 0},
		order_by="modified desc",
		limit_page_length=1,
	)
	if leaf_values:
		return leaf_values[0].name

	frappe.throw(_("Please configure a non-group {0} before checkout.").format(label))


def _get_default_customer_group():
	for candidate in ("Commercial", "Individual", "Non Profit", "Government"):
		if frappe.db.exists("Customer Group", {"name": candidate, "is_group": 0}):
			return candidate

	return _get_non_group_default("Customer Group", "customer_group", "Customer Group")


def _get_default_territory():
	return _get_non_group_default("Territory", "territory", "Territory")


def _get_default_supplier_for_item(item_code, company, preferred_supplier=None):
	preferred_supplier = _resolve_supplier_name(preferred_supplier)
	if preferred_supplier:
		return preferred_supplier

	for resolver in (get_item_defaults, get_item_group_defaults, get_brand_defaults):
		defaults = resolver(item_code, company) or {}
		supplier = defaults.get("default_supplier")
		if supplier:
			return supplier

	item_suppliers = frappe.get_all(
		"Item Supplier",
		filters={"parent": item_code, "parenttype": "Item"},
		fields=["supplier"],
		order_by="idx asc",
		limit_page_length=1,
	)
	if item_suppliers and item_suppliers[0].supplier:
		return item_suppliers[0].supplier

	return None


def _is_guest_user(user_name=None):
	user_name = frappe.session.user if user_name is None else user_name
	return _normalize_user_name(user_name) == "Guest"


def _require_checkout_user():
	if _is_guest_user():
		frappe.throw(_("Please sign in before checkout."), frappe.AuthenticationError)

	return frappe.session.user


def _get_or_create_customer_for_user(user_name):
	user_name = _normalize_user_name(user_name)
	if _is_guest_user(user_name):
		frappe.throw(_("Please sign in before checkout."), frappe.AuthenticationError)

	user = frappe.get_doc("User", user_name)
	customer_name = None
	if user.email:
		customer_name = frappe.db.get_value("Customer", {"email_id": user.email}, "name")
	if not customer_name and user.mobile_no:
		customer_name = frappe.db.get_value("Customer", {"mobile_no": user.mobile_no}, "name")

	if customer_name:
		return customer_name

	customer_doc = frappe.get_doc(
		{
			"doctype": "Customer",
			"customer_name": user.full_name or user.email or user.mobile_no or user.name,
			"customer_type": "Individual",
			"customer_group": _get_default_customer_group(),
			"territory": _get_default_territory(),
			"email_id": user.email,
			"mobile_no": user.mobile_no,
		}
	)
	customer_doc.insert(ignore_permissions=True)

	return customer_doc.name


def _normalize_delivery_address(delivery_address):
	if isinstance(delivery_address, str):
		delivery_address = json.loads(delivery_address) if delivery_address else None

	if not isinstance(delivery_address, dict):
		return {}

	return {
		"label": _clean_text(delivery_address.get("label") or "Home") or "Home",
		"contact_name": _clean_text(delivery_address.get("contactName") or delivery_address.get("contact_name")),
		"phone": _clean_text(delivery_address.get("phone")),
		"area": _clean_text(delivery_address.get("area")),
		"apartment_office_name": _clean_text(
			delivery_address.get("apartmentOfficeName")
			or delivery_address.get("apartment_office_name")
		),
		"apartment_office_no": _clean_text(
			delivery_address.get("apartmentOfficeNo")
			or delivery_address.get("apartment_office_no")
		),
		"building": _clean_text(delivery_address.get("building")),
		"street": _clean_text(delivery_address.get("street")),
		"landmark": _clean_text(delivery_address.get("landmark")),
		"emirate": _clean_text(delivery_address.get("emirate")),
		"latitude": _clean_text(delivery_address.get("latitude")),
		"longitude": _clean_text(delivery_address.get("longitude")),
	}


def _build_delivery_address_display(delivery_address):
	address = _normalize_delivery_address(delivery_address)
	if not address:
		return ""

	lines = []
	if address.get("label"):
		lines.append(address["label"])

	contact_line = ", ".join(filter(None, [address.get("contact_name"), address.get("phone")]))
	if contact_line:
		lines.append(contact_line)

	apartment_line = ", ".join(
		filter(
			None,
			[
				address.get("apartment_office_name"),
				address.get("apartment_office_no"),
			],
		)
	)
	if apartment_line:
		lines.append(apartment_line)

	building_line = ", ".join(
		filter(
			None,
			[
				address.get("building"),
				address.get("street"),
			],
		)
	)
	if building_line:
		lines.append(building_line)

	area_line = ", ".join(
		filter(
			None,
			[
				address.get("area"),
				address.get("emirate"),
			],
		)
	)
	if area_line:
		lines.append(area_line)

	if address.get("landmark"):
		lines.append(address["landmark"])

	return "\n".join(lines)


def _get_linked_customer_address(customer, address):
	if not customer or not address.get("building") or not address.get("area"):
		return None

	linked_addresses = frappe.get_all(
		"Dynamic Link",
		filters={
			"link_doctype": "Customer",
			"link_name": customer,
			"parenttype": "Address",
		},
		pluck="parent",
		ignore_permissions=True,
		limit_page_length=100,
	)
	if not linked_addresses:
		return None

	return frappe.db.get_value(
		"Address",
		{
			"name": ["in", linked_addresses],
			"address_line1": address["building"],
			"address_line2": address["area"],
		},
		"name",
	)


def _set_optional_doc_value(doc, fieldname, value):
	if value and doc.meta.has_field(fieldname):
		doc.set(fieldname, value)


def _get_or_create_customer_address(customer, delivery_address):
	address = _normalize_delivery_address(delivery_address)
	if not address:
		return None

	if not address.get("building") or not address.get("area"):
		frappe.throw(_("Please add a complete delivery address before checkout."))

	existing_address = _get_linked_customer_address(customer, address)
	if existing_address:
		return existing_address

	address_doc = frappe.get_doc(
		{
			"doctype": "Address",
			"address_title": address.get("contact_name") or customer,
			"address_type": address.get("label") if address.get("label") in ("Billing", "Shipping", "Office", "Personal") else "Shipping",
			"address_line1": ", ".join(
				filter(
					None,
					[
						address.get("apartment_office_name"),
						address.get("apartment_office_no"),
						address["building"],
					],
				)
			),
			"address_line2": ", ".join(
				filter(
					None,
					[
						address.get("street"),
						address["area"],
					],
				)
			),
			"city": address["area"],
			"country": "United Arab Emirates",
			"phone": address.get("phone"),
			"links": [
				{
					"link_doctype": "Customer",
					"link_name": customer,
				}
			],
		}
	)
	_set_optional_doc_value(address_doc, "address_line3", address.get("landmark"))
	_set_optional_doc_value(address_doc, "latitude", address.get("latitude"))
	_set_optional_doc_value(address_doc, "longitude", address.get("longitude"))
	address_doc.insert(ignore_permissions=True)

	return address_doc.name


def _get_or_create_customer_contact(customer, delivery_address):
	address = _normalize_delivery_address(delivery_address)
	if not address:
		return None

	contact_name = address.get("contact_name")
	phone = address.get("phone")
	if not contact_name and not phone:
		return None

	linked_contacts = frappe.get_all(
		"Dynamic Link",
		filters={
			"link_doctype": "Customer",
			"link_name": customer,
			"parenttype": "Contact",
		},
		pluck="parent",
		ignore_permissions=True,
		limit_page_length=100,
	)
	if linked_contacts and phone:
		existing_contact = frappe.db.get_value(
			"Contact Phone",
			{
				"parent": ["in", linked_contacts],
				"phone": phone,
			},
			"parent",
		)
		if existing_contact:
			return existing_contact

	contact_doc = frappe.get_doc(
		{
			"doctype": "Contact",
			"first_name": contact_name or phone or customer,
			"is_primary_contact": 1,
			"is_billing_contact": 1,
			"links": [
				{
					"link_doctype": "Customer",
					"link_name": customer,
				}
			],
		}
	)
	if phone:
		contact_doc.append(
			"phone_nos",
			{
				"phone": phone,
				"is_primary_phone": 1,
				"is_primary_mobile_no": 1,
			},
		)
	contact_doc.insert(ignore_permissions=True)

	return contact_doc.name


def _get_checkout_return_origin(return_origin=None):
	return_origin = _clean_text(return_origin)
	request_origin = (getattr(frappe.local, "request", None) and frappe.local.request.host_url or "").rstrip("/")

	if return_origin:
		parsed_return_origin = urlparse(return_origin)
		parsed_request_origin = urlparse(request_origin)
		configured_origins = _get_conf_value("buy_in_minutes_checkout_return_origins")
		if isinstance(configured_origins, str):
			allowed_origins = {
				origin.strip().rstrip("/")
				for origin in configured_origins.split(",")
				if origin.strip()
			}
		else:
			allowed_origins = {
				str(origin).strip().rstrip("/")
				for origin in configured_origins or []
				if str(origin).strip()
			}

		if (
			parsed_return_origin.scheme in {"http", "https"}
			and parsed_return_origin.netloc
			and (
				parsed_return_origin.netloc == parsed_request_origin.netloc
				or return_origin.rstrip("/") in allowed_origins
			)
		):
			return return_origin.rstrip("/")

	return get_url("").rstrip("/")


def _apply_delivery_address_to_sales_order(
	sales_order,
	customer,
	delivery_address,
	address_display=None,
):
	if not delivery_address:
		return

	customer_address = _get_or_create_customer_address(customer, delivery_address)
	contact_person = _get_or_create_customer_contact(customer, delivery_address)

	if customer_address:
		sales_order.customer_address = customer_address
		sales_order.shipping_address_name = customer_address

	if contact_person:
		sales_order.contact_person = contact_person

	sales_order.set_missing_values()

	address_display = _clean_text(address_display) or _build_delivery_address_display(
		delivery_address
	)
	if address_display:
		_set_doc_value_if_field_exists(sales_order, "address_display", address_display)
		_set_doc_value_if_field_exists(sales_order, "shipping_address", address_display)


def _get_checkout_items(cart_items, delivery_fee=None, include_delivery_fee_item=True):
	checkout_items = []
	for cart_item in _normalize_cart_items(cart_items):
		item = frappe.db.get_value(
			"Item",
			{"name": cart_item["item_code"], "disabled": 0},
			["name", "item_name", "standard_rate"],
			as_dict=True,
		)
		if not item:
			frappe.throw(_("Item {0} is not available.").format(cart_item["item_code"]))

		rate = _get_item_selling_price(item.name, item.standard_rate)
		if rate <= 0:
			frappe.throw(_("Item {0} does not have a valid price.").format(item.item_name or item.name))

		checkout_items.append(
			{
				"item_code": item.name,
				"item_name": item.item_name or item.name,
				"quantity": cart_item["quantity"],
				"rate": rate,
				"amount": rate * cart_item["quantity"],
				"supplier": cart_item.get("supplier"),
				"size": cart_item.get("size"),
			}
		)

	normalized_delivery_fee = _normalize_delivery_fee(delivery_fee)
	subtotal = sum(item["amount"] for item in checkout_items)
	effective_delivery_fee = normalized_delivery_fee
	if effective_delivery_fee is None and checkout_items and subtotal < FREE_DELIVERY_MINIMUM:
		effective_delivery_fee = DELIVERY_FEE

	if (
		include_delivery_fee_item
		and checkout_items
		and effective_delivery_fee
		and effective_delivery_fee > 0
	):
		checkout_items.append(
			{
				"item_code": DELIVERY_FEE_ITEM_CODE,
				"item_name": _("Delivery charge"),
				"quantity": 1,
				"rate": effective_delivery_fee,
				"amount": effective_delivery_fee,
			}
		)

	return checkout_items


def _get_delivery_charge_tax_template():
	if not frappe.db.exists("DocType", "Sales Taxes and Charges Template"):
		return None

	if not frappe.db.exists("Sales Taxes and Charges Template", DELIVERY_CHARGE_TAX_TEMPLATE):
		matching_templates = frappe.get_all(
			"Sales Taxes and Charges Template",
			filters={
				"name": ["like", f"{DELIVERY_CHARGE_TAX_TEMPLATE}%"],
			},
			fields=["name"],
			order_by="name asc",
			limit_page_length=1,
			ignore_permissions=True,
		)
		if not matching_templates:
			return None

		return frappe.get_doc(
			"Sales Taxes and Charges Template",
			matching_templates[0].name,
		)

	return frappe.get_doc("Sales Taxes and Charges Template", DELIVERY_CHARGE_TAX_TEMPLATE)


def _get_delivery_charge_tax_template_name():
	template = _get_delivery_charge_tax_template()
	return template.name if template else ""


def _build_sales_order_delivery_tax_rows(delivery_fee):
	template = _get_delivery_charge_tax_template()
	if not template:
		return []

	sales_tax_meta = frappe.get_meta("Sales Taxes and Charges")
	normalized_delivery_fee = _normalize_delivery_fee(delivery_fee) or 0
	tax_rows = []
	actual_row_applied = False

	for template_row in template.get("taxes") or []:
		row_data = {
			fieldname: template_row.get(fieldname)
			for fieldname in sales_tax_meta.get_valid_columns()
			if fieldname not in {"name", "parent", "parentfield", "parenttype", "idx", "owner", "creation", "modified", "modified_by", "docstatus"}
		}

		if row_data.get("charge_type") == "Actual":
			row_data["tax_amount"] = normalized_delivery_fee
			row_data["base_tax_amount"] = normalized_delivery_fee
			row_data["rate"] = 0
			actual_row_applied = True

		tax_rows.append(row_data)

	if normalized_delivery_fee > 0 and tax_rows and not actual_row_applied:
		tax_rows[0]["charge_type"] = "Actual"
		tax_rows[0]["tax_amount"] = normalized_delivery_fee
		tax_rows[0]["base_tax_amount"] = normalized_delivery_fee
		tax_rows[0]["rate"] = 0

	return tax_rows


def _build_sales_order_item_rows(checkout_items, company, delivery_date=None):
	order_items = []
	delivery_date = delivery_date or nowdate()
	sales_order_item_meta = frappe.get_meta("Sales Order Item")
	for item in checkout_items:
		if not frappe.db.exists("Item", item["item_code"]):
			continue

		supplier = _get_default_supplier_for_item(
			item["item_code"],
			company,
			item.get("supplier"),
		)
		if not supplier and item["item_code"] != DELIVERY_FEE_ITEM_CODE:
			frappe.throw(
				_("Item {0} does not have a Supplier. Configure a default Supplier or Item Supplier before checkout.").format(
					item["item_name"] or item["item_code"]
				)
			)

		row = {
			"item_code": item["item_code"],
			"item_name": item["item_name"],
			"qty": item["quantity"],
			"rate": item["rate"],
			"delivery_date": delivery_date,
		}
		if item.get("size"):
			row["custom_size"] = item["size"]
			row["size"] = item["size"]
		if supplier:
			row["supplier"] = supplier
			row["delivered_by_supplier"] = 1

		row = {
			fieldname: value
			for fieldname, value in row.items()
			if sales_order_item_meta.has_field(fieldname)
		}

		order_items.append(row)

	return order_items


def _get_checkout_items_from_sales_order(sales_order):
	checkout_items = []

	for item in sales_order.items:
		if not item.item_code or flt(item.qty) <= 0:
			continue

		checkout_items.append(
			{
				"item_code": item.item_code,
				"item_name": item.item_name or item.item_code,
				"quantity": flt(item.qty),
				"rate": flt(item.rate),
				"amount": flt(item.amount),
				"supplier": getattr(item, "supplier", None),
				"size": getattr(item, "custom_size", None) or getattr(item, "size", None),
			}
		)

	return checkout_items


def _build_cart_totals_summary(sales_order, checkout_items):
	original_total = sum(flt(item.get("amount")) for item in checkout_items or [])
	discounted_total = sum(flt(item.get("amount")) for item in _get_checkout_items_from_sales_order(sales_order))
	discount_amount = max(original_total - discounted_total, 0)

	return {
		"coupon_code": _clean_text(getattr(sales_order, "coupon_code", "")),
		"original_total": original_total,
		"discount_amount": discount_amount,
		"discounted_total": discounted_total,
		"grand_total": flt(sales_order.grand_total or discounted_total),
	}


def _resolve_sales_order_item_suppliers(sales_order):
	company = sales_order.company or _get_default_company()
	for item in sales_order.items:
		if item.supplier or not item.item_code:
			continue

		supplier = _get_default_supplier_for_item(item.item_code, company)
		if not supplier:
			continue

		item.supplier = supplier
		item.delivered_by_supplier = 1
		frappe.db.set_value(
			item.doctype,
			item.name,
			{
				"supplier": supplier,
				"delivered_by_supplier": 1,
			},
			update_modified=False,
		)


def _get_purchase_orders_for_sales_order(sales_order_name):
	purchase_order_names = frappe.get_all(
		"Purchase Order Item",
		filters={"sales_order": sales_order_name, "docstatus": ["<", 2]},
		pluck="parent",
		ignore_permissions=True,
	)

	return [
		frappe.get_doc("Purchase Order", purchase_order_name)
		for purchase_order_name in dict.fromkeys(purchase_order_names)
		if purchase_order_name
	]


def _get_purchase_order_names_for_sales_order(sales_order_name):
	return [
		purchase_order.name
		for purchase_order in _get_purchase_orders_for_sales_order(sales_order_name)
	]


def _get_purchased_sales_order_item_names(sales_order_name):
	if not frappe.get_meta("Purchase Order Item").has_field("sales_order_item"):
		return set()

	return set(
		filter(
			None,
			frappe.get_all(
				"Purchase Order Item",
				filters={
					"sales_order": sales_order_name,
					"docstatus": ["<", 2],
				},
				pluck="sales_order_item",
				ignore_permissions=True,
			),
		)
	)


def _get_purchase_orderable_sales_order_items(sales_order):
	purchased_sales_order_items = _get_purchased_sales_order_item_names(sales_order.name)

	return [
		{
			"item_code": item.item_code,
			"sales_order_item": item.name,
			"supplier": item.supplier,
		}
		for item in sales_order.items
		if item.item_code
		and item.supplier
		and item.name not in purchased_sales_order_items
		and flt(item.ordered_qty) < flt(item.stock_qty)
	]


def _set_doc_value_if_field_exists(doc, fieldname, value):
	if doc.meta.has_field(fieldname):
		doc.set(fieldname, value)


def _build_manual_purchase_orders_for_sales_order(sales_order, selected_items):
	selected_item_names = {
		item.get("sales_order_item")
		for item in selected_items
		if item.get("sales_order_item")
	}
	items_by_supplier = {}

	for item in sales_order.items:
		if item.name not in selected_item_names:
			continue

		qty = flt(item.qty) - (flt(item.ordered_qty) / (flt(item.conversion_factor) or 1))
		if qty <= 0:
			continue

		items_by_supplier.setdefault(item.supplier, []).append((item, qty))

	purchase_orders = []
	purchase_order_item_meta = frappe.get_meta("Purchase Order Item")
	for supplier, supplier_items in items_by_supplier.items():
		purchase_order = frappe.new_doc("Purchase Order")
		purchase_order.supplier = supplier
		purchase_order.company = sales_order.company
		purchase_order.transaction_date = nowdate()
		_set_doc_value_if_field_exists(purchase_order, "schedule_date", sales_order.delivery_date or nowdate())
		_set_doc_value_if_field_exists(purchase_order, "buying_price_list", "")
		_set_doc_value_if_field_exists(purchase_order, "ignore_pricing_rule", 1)

		if any(item.delivered_by_supplier for item, _qty in supplier_items):
			_set_doc_value_if_field_exists(purchase_order, "customer", sales_order.customer)
			_set_doc_value_if_field_exists(purchase_order, "customer_name", sales_order.customer_name)
			_set_doc_value_if_field_exists(
				purchase_order,
				"shipping_address",
				sales_order.shipping_address_name or sales_order.customer_address,
			)
			_set_doc_value_if_field_exists(
				purchase_order,
				"shipping_address_display",
				sales_order.shipping_address or sales_order.address_display,
			)
			_set_doc_value_if_field_exists(purchase_order, "customer_contact_person", sales_order.contact_person)
			_set_doc_value_if_field_exists(purchase_order, "customer_contact_display", sales_order.contact_display)
			_set_doc_value_if_field_exists(purchase_order, "customer_contact_mobile", sales_order.contact_mobile)
			_set_doc_value_if_field_exists(purchase_order, "customer_contact_email", sales_order.contact_email)

		for item, qty in supplier_items:
			amount = flt(qty) * flt(item.rate)
			row = {
				"item_code": item.item_code,
				"item_name": item.item_name,
				"description": item.description,
				"qty": qty,
				"schedule_date": item.delivery_date or sales_order.delivery_date or nowdate(),
				"uom": item.uom,
				"stock_uom": item.stock_uom,
				"conversion_factor": item.conversion_factor or 1,
				"rate": item.rate,
				"price_list_rate": item.rate,
				"amount": amount,
				"base_rate": item.rate,
				"base_amount": amount,
				"sales_order": sales_order.name,
				"sales_order_item": item.name,
				"project": sales_order.project,
			}
			row = {
				fieldname: value
				for fieldname, value in row.items()
				if purchase_order_item_meta.has_field(fieldname)
			}
			purchase_order.append("items", row)

		total_amount = sum(flt(item.amount) for item in purchase_order.items)
		_set_doc_value_if_field_exists(purchase_order, "net_total", total_amount)
		_set_doc_value_if_field_exists(purchase_order, "grand_total", total_amount)
		_set_doc_value_if_field_exists(purchase_order, "base_net_total", total_amount)
		_set_doc_value_if_field_exists(purchase_order, "base_grand_total", total_amount)
		_set_doc_value_if_field_exists(purchase_order, "total", total_amount)
		_set_doc_value_if_field_exists(purchase_order, "rounded_total", total_amount)
		_set_doc_value_if_field_exists(purchase_order, "base_rounded_total", total_amount)

		purchase_order.flags.ignore_validate = True
		purchase_order.flags.ignore_mandatory = True
		purchase_order.flags.ignore_permissions = True
		purchase_order.insert(ignore_permissions=True)
		purchase_order.flags.ignore_validate = True
		purchase_order.flags.ignore_mandatory = True
		purchase_orders.append(purchase_order)

	frappe.db.commit()
	return purchase_orders


def _make_purchase_orders_for_sales_order(sales_order, selected_items):
	try:
		from erpnext.selling.doctype.sales_order import sales_order as sales_order_module

		make_purchase_order_for_default_supplier = getattr(
			sales_order_module,
			"make_purchase_order_for_default_supplier",
			None,
		)
		if make_purchase_order_for_default_supplier:
			return make_purchase_order_for_default_supplier(
				sales_order.name,
				selected_items=selected_items,
			) or []
	except ImportError:
		pass

	frappe.logger("buy_in_minutes.payment").info(
		f"Using manual Purchase Order creation fallback for {sales_order.name}"
	)
	return _build_manual_purchase_orders_for_sales_order(sales_order, selected_items)


def _create_purchase_orders_for_sales_order(sales_order):
	if not sales_order or sales_order.docstatus != 1:
		frappe.logger("buy_in_minutes.payment").info(
			f"Skipping purchase order creation for {getattr(sales_order, 'name', None)}: "
			f"not submitted (docstatus={getattr(sales_order, 'docstatus', None)})"
		)
		return []

	_resolve_sales_order_item_suppliers(sales_order)

	linked_purchase_orders = _get_purchase_orders_for_sales_order(sales_order.name)
	_submit_purchase_orders(linked_purchase_orders, sales_order.name)

	if linked_purchase_orders:
		sales_order.reload()
		_resolve_sales_order_item_suppliers(sales_order)

	selected_items = _get_purchase_orderable_sales_order_items(sales_order)

	if not selected_items:
		missing_supplier_items = [item.item_code for item in sales_order.items if not item.supplier]
		frappe.logger("buy_in_minutes.payment").info(
			f"Skipping purchase order creation for {sales_order.name}: "
			f"no remaining item needs a Purchase Order "
			f"(items without a supplier: {missing_supplier_items})"
		)
		return linked_purchase_orders

	try:
		purchase_orders = _make_purchase_orders_for_sales_order(sales_order, selected_items)
	except Exception:
		frappe.log_error(
			title="Purchase Order Creation Failed",
			message=f"Sales Order: {sales_order.name}\n\n{frappe.get_traceback()}",
		)
		raise

	_submit_purchase_orders(purchase_orders, sales_order.name)

	frappe.logger("buy_in_minutes.payment").info(
		f"Created {len(purchase_orders)} purchase order(s) for {sales_order.name}: "
		f"{[po.name for po in purchase_orders]}"
	)

	return linked_purchase_orders + purchase_orders


def _submit_purchase_orders(purchase_orders, sales_order_name):
	for purchase_order in purchase_orders or []:
		if not purchase_order or purchase_order.docstatus != 0:
			continue

		try:
			purchase_order.flags.ignore_permissions = True
			purchase_order.submit()
		except Exception:
			frappe.log_error(
				title="Purchase Order Submission Failed",
				message=(
					f"Sales Order: {sales_order_name}\n"
					f"Purchase Order: {getattr(purchase_order, 'name', None)}\n\n"
					f"{frappe.get_traceback()}"
				),
			)
			raise


def on_sales_order_submit(doc, method=None):
	_create_purchase_orders_for_sales_order(doc)


def _normalize_payment_schedule_dates(sales_order):
	transaction_date = sales_order.transaction_date or nowdate()
	transaction_date_value = getdate(transaction_date)

	for payment_row in sales_order.get("payment_schedule") or []:
		if not payment_row.due_date or getdate(payment_row.due_date) < transaction_date_value:
			payment_row.due_date = transaction_date


def _persist_sales_order_address_display(sales_order, address_display):
	address_display = _clean_text(address_display)
	if not address_display:
		return

	updates = {}
	if sales_order.meta.has_field("address_display"):
		updates["address_display"] = address_display
	if sales_order.meta.has_field("shipping_address"):
		updates["shipping_address"] = address_display

	if not updates:
		return

	for fieldname, value in updates.items():
		sales_order.set(fieldname, value)

	if sales_order.name:
		frappe.db.set_value(
			sales_order.doctype,
			sales_order.name,
			updates,
			update_modified=False,
		)


def _upsert_sales_order(
	checkout_items,
	sales_order_name=None,
	submit=False,
	delivery_address=None,
	delivery_date=None,
	delivery_slot=None,
	customer_location=None,
	address_display=None,
	coupon_code=None,
	delivery_fee=None,
	use_delivery_charge_tax_template=False,
):
	checkout_user = frappe.session.user
	customer = _get_or_create_customer_for_user(checkout_user)
	company = _get_default_company()
	order_date = nowdate()
	delivery_date = _clean_text(delivery_date) or order_date
	order_items = _build_sales_order_item_rows(checkout_items, company, delivery_date)

	if not order_items:
		frappe.throw(_("Cart does not contain orderable items."))

	if sales_order_name and frappe.db.exists("Sales Order", sales_order_name):
		sales_order_owner = frappe.db.sql(
			"select owner from tabSales Order where name = %s",
			(sales_order_name,),
			as_dict=True,
		)

		if not sales_order_owner or sales_order_owner[0].owner != checkout_user:
			frappe.throw(_("The linked Sales Order is no longer editable."))

		sales_order = frappe.get_doc("Sales Order", sales_order_name)

		if sales_order.docstatus != 0:
			frappe.throw(_("The linked Sales Order is no longer editable."))

		sales_order.set("items", [])
		sales_order.set("taxes", [])
		sales_order.set("payment_schedule", [])
		if sales_order.meta.has_field("pricing_rules"):
			sales_order.set("pricing_rules", [])
	else:
		sales_order = frappe.get_doc({"doctype": "Sales Order"})

	sales_order.update(
		{
			"customer": customer,
			"company": company,
			"transaction_date": order_date,
			"delivery_date": delivery_date,
			"order_type": "Sales",
		}
	)
	_set_doc_value_if_field_exists(
		sales_order,
		"custom_delivery_slot",
		_clean_text(delivery_slot),
	)
	_set_doc_value_if_field_exists(
		sales_order,
		"custom_customer_location",
		_clean_text(customer_location),
	)
	_set_doc_value_if_field_exists(
		sales_order,
		"coupon_code",
		_clean_text(coupon_code),
	)
	if use_delivery_charge_tax_template:
		delivery_charge_tax_template_name = _get_delivery_charge_tax_template_name()
		_set_doc_value_if_field_exists(
			sales_order,
			"taxes_and_charges",
			delivery_charge_tax_template_name,
		)
	else:
		_set_doc_value_if_field_exists(sales_order, "taxes_and_charges", "")

	for item in order_items:
		sales_order.append("items", item)

	if use_delivery_charge_tax_template:
		for tax_row in _build_sales_order_delivery_tax_rows(delivery_fee):
			sales_order.append("taxes", tax_row)

	_apply_delivery_address_to_sales_order(
		sales_order,
		customer,
		delivery_address,
		address_display=address_display,
	)
	address_display = _clean_text(address_display) or _build_delivery_address_display(
		delivery_address
	)
	_normalize_payment_schedule_dates(sales_order)

	if sales_order.is_new():
		sales_order.owner = checkout_user
		sales_order.insert(ignore_permissions=True)
	else:
		sales_order.save(ignore_permissions=True)

	_persist_sales_order_address_display(sales_order, address_display)

	if submit:
		sales_order.flags.ignore_permissions = True
		sales_order.submit()
		_persist_sales_order_address_display(sales_order, address_display)

		# The on_submit hook creates the Purchase Orders.
		sales_order.purchase_orders = _get_purchase_orders_for_sales_order(
			sales_order.name
		)

	return sales_order


def _build_checkout_params(checkout_items, sales_order_name=None, return_origin=None):
	return_origin = _get_checkout_return_origin(return_origin)
	success_url = f"{return_origin}/buy-in-minutes#/payment/success?method=stripe&session_id={{CHECKOUT_SESSION_ID}}"
	cancel_url = f"{return_origin}/buy-in-minutes#/payment/cancel"
	stripe_currency = _get_stripe_settings().get("currency") or DEFAULT_CURRENCY
	checkout_user = _normalize_user_name(frappe.session.user)
	adaptive_pricing_enabled = bool((adaptive_pricing or {}).get("enabled"))
	params = {
		"mode": "payment",
		"success_url": success_url,
		"cancel_url": cancel_url,
		"client_reference_id": checkout_user,
		"metadata[user]": checkout_user,
		"metadata[payment_method]": "stripe",
		"adaptive_pricing[enabled]": "true" if adaptive_pricing_enabled else "false",
	}
	if sales_order_name:
		params["metadata[sales_order]"] = sales_order_name

	for index, item in enumerate(checkout_items):
		unit_amount = int(round(item["rate"] * 100))
		params[f"line_items[{index}][quantity]"] = item["quantity"]
		params[f"line_items[{index}][price_data][currency]"] = stripe_currency
		params[f"line_items[{index}][price_data][unit_amount]"] = unit_amount
		params[f"line_items[{index}][price_data][product_data][name]"] = item["item_name"]
		params[f"line_items[{index}][price_data][product_data][metadata][item_code]"] = item["item_code"]

	return params


# def _submit_sales_order(sales_order_name):
# 	if not sales_order_name or not frappe.db.exists("Sales Order", sales_order_name):
# 		return None

# 	with _as_administrator():
# 		sales_order = frappe.get_doc("Sales Order", sales_order_name)
# 		if sales_order.docstatus != 0:
# 			return sales_order

# 		sales_order.submit()
# 		_create_purchase_orders_for_sales_order(sales_order)
# 	return sales_order

def _submit_sales_order(sales_order_name):
	if not sales_order_name:
		frappe.throw(_("Sales Order is missing from Stripe payment."))

	if not frappe.db.exists("Sales Order", sales_order_name):
		frappe.throw(
			_("Sales Order {0} does not exist.").format(sales_order_name)
		)

	sales_order = frappe.get_doc("Sales Order", sales_order_name)

	if sales_order.docstatus == 2:
		frappe.throw(
			_("Sales Order {0} is cancelled.").format(sales_order_name)
		)

	was_draft = sales_order.docstatus == 0

	# Submit the Sales Order after successful Stripe payment.
	if sales_order.docstatus == 0:
		sales_order.flags.ignore_permissions = True
		sales_order.submit()

	# Submitted orders may come from a previous callback, so keep this path idempotent.
	if not was_draft:
		_create_purchase_orders_for_sales_order(sales_order)

	# Force the status after ERPNext completes its submit processing.
	if sales_order.docstatus == 1:
		frappe.db.set_value(
			"Sales Order",
			sales_order.name,
			{
				"status": "To Deliver",
				"billing_status": "Fully Billed",
				"per_billed": 100,
			},
			update_modified=False,
		)

		frappe.db.commit()
		sales_order.reload()

	return sales_order


# @frappe.whitelist(methods=["POST"])
# def finalize_stripe_checkout(session_id=None):
# 	if frappe.session.user == "Guest":
# 		frappe.throw(_("Please sign in before checkout."), frappe.AuthenticationError)

# 	if not session_id:
# 		frappe.throw(_("Missing Stripe session id."))

# 	session = _stripe_get_request(f"/checkout/sessions/{session_id}")
# 	if session.get("payment_status") != "paid":
# 		frappe.throw(_("Stripe payment is not complete yet."))

# 	sales_order_name = session.get("metadata", {}).get("sales_order")
# 	sales_order = _submit_sales_order(sales_order_name)

# 	return {
# 		"success": True,
# 		"sales_order": sales_order.name if sales_order else sales_order_name,
# 		"payment_status": session.get("payment_status"),
# 	}

def _get_sales_order_item_summary(sales_order):
	return [
		{
			"item_code": row.item_code,
			"item_name": row.item_name or row.item_code,
			"description": row.description,
			"qty": flt(row.qty),
			"rate": flt(row.rate),
			"amount": flt(row.amount),
			"size": getattr(row, "custom_size", None) or getattr(row, "size", None),
		}
		for row in sales_order.items
	]


@frappe.whitelist(allow_guest=True, methods=["POST"])
def finalize_stripe_checkout(session_id=None):
	if not session_id:
		frappe.throw(_("Missing Stripe session id."))

	session = _stripe_get_request(
		f"/checkout/sessions/{session_id}"
	)

	if session.get("payment_status") != "paid":
		frappe.throw(_("Stripe payment is not complete yet."))

	sales_order_name = (
		session.get("metadata", {}).get("sales_order")
	)

	if not sales_order_name:
		frappe.throw(
			_("Sales Order is missing from Stripe session metadata.")
		)

	sales_order = _submit_sales_order(sales_order_name)
	restored_user = None
	checkout_user = session.get("metadata", {}).get("user")
	if frappe.session.user == "Guest" and checkout_user:
		restored_user = _restore_checkout_user(checkout_user, sales_order.name)

	return {
		"success": True,
		"sales_order": sales_order.name,
		"purchase_orders": _get_purchase_order_names_for_sales_order(sales_order.name),
		"sales_order_status": sales_order.status,
		"docstatus": sales_order.docstatus,
		"payment_status": session.get("payment_status"),
		"items": _get_sales_order_item_summary(sales_order),
		"user": restored_user,
	}


@frappe.whitelist(allow_guest=True, methods=["POST"])
def resume_checkout_session(checkout_resume_token=None):
	payload = _read_checkout_resume_token(checkout_resume_token)
	user = _restore_checkout_user(payload.get("user"), payload.get("sales_order"))

	return {
		"success": True,
		"user": user,
	}


@frappe.whitelist(methods=["POST"])
def sync_cart_sales_order(
	cart_items=None,
	sales_order_name=None,
	delivery_address=None,
	delivery_date=None,
	delivery_slot=None,
	customer_location=None,
	address_display=None,
	delivery_fee=None,
	coupon_code=None,
):
	_require_checkout_user()

	checkout_items = _get_checkout_items(cart_items, delivery_fee=delivery_fee)
	sales_order_checkout_items = _get_checkout_items(
		cart_items,
		delivery_fee=delivery_fee,
		include_delivery_fee_item=False,
	)
	sales_order = _upsert_sales_order(
		sales_order_checkout_items,
		sales_order_name=sales_order_name,
		delivery_address=delivery_address,
		delivery_date=delivery_date,
		delivery_slot=delivery_slot,
		customer_location=customer_location,
		address_display=address_display,
		coupon_code=coupon_code,
		delivery_fee=delivery_fee,
		use_delivery_charge_tax_template=True,
	)

	return {
		"success": True,
		"sales_order": sales_order.name,
		"totals": _build_cart_totals_summary(sales_order, checkout_items),
	}


@frappe.whitelist(methods=["POST"])
def create_checkout_session(
	cart_items=None,
	sales_order_name=None,
	delivery_address=None,
	return_origin=None,
	delivery_date=None,
	delivery_slot=None,
	customer_location=None,
	address_display=None,
	delivery_fee=None,
	coupon_code=None,
):
	_require_checkout_user()

	checkout_items = _get_checkout_items(cart_items, delivery_fee=delivery_fee)
	sales_order_checkout_items = _get_checkout_items(
		cart_items,
		delivery_fee=delivery_fee,
		include_delivery_fee_item=False,
	)
	sales_order = _upsert_sales_order(
		sales_order_checkout_items,
		sales_order_name=sales_order_name,
		delivery_address=delivery_address,
		delivery_date=delivery_date,
		delivery_slot=delivery_slot,
		customer_location=customer_location,
		address_display=address_display,
		coupon_code=coupon_code,
		delivery_fee=delivery_fee,
		use_delivery_charge_tax_template=True,
	)
	session = _stripe_request(
		"/checkout/sessions",
		_build_checkout_params(checkout_items, sales_order.name, return_origin=return_origin),
	)

	return {
		"success": True,
		"checkout_url": session.get("url"),
		"session_id": session.get("id"),
		"sales_order": sales_order.name,
		"checkout_resume_token": _create_checkout_resume_token(frappe.session.user, sales_order.name),
	}


@frappe.whitelist(methods=["POST"])
def create_cash_on_delivery_order(
	cart_items=None,
	sales_order_name=None,
	delivery_address=None,
	delivery_date=None,
	delivery_slot=None,
	customer_location=None,
	address_display=None,
	delivery_fee=None,
	coupon_code=None,
):
	_require_checkout_user()

	checkout_items = _get_checkout_items(
		cart_items,
		delivery_fee=delivery_fee,
		include_delivery_fee_item=False,
	)
	sales_order = _upsert_sales_order(
		checkout_items,
		sales_order_name=sales_order_name,
		submit=True,
		delivery_address=delivery_address,
		delivery_date=delivery_date,
		delivery_slot=delivery_slot,
		customer_location=customer_location,
		address_display=address_display,
		coupon_code=coupon_code,
		delivery_fee=delivery_fee,
		use_delivery_charge_tax_template=True,
	)
	purchase_orders = getattr(sales_order, "purchase_orders", None)

	if purchase_orders is None:
		purchase_orders = _get_purchase_orders_for_sales_order(sales_order.name)

	purchase_order_names = _get_purchase_order_names_for_sales_order(sales_order.name)
	if not purchase_order_names and purchase_orders:
		purchase_order_names = [purchase_order.name for purchase_order in purchase_orders]

	return {
		"success": True,
		"sales_order": sales_order.name,
		"purchase_orders": purchase_order_names,
		"payment_method": "cod",
	}




def _get_signature_timestamp_and_signatures(signature_header):
	timestamp = None
	signatures = []

	for part in (signature_header or "").split(","):
		key, _, value = part.partition("=")
		if key == "t":
			timestamp = value
		elif key == "v1":
			signatures.append(value)

	return timestamp, signatures


def _verify_webhook_signature(payload, signature_header):
	webhook_secret = _get_stripe_webhook_secret()
	if not webhook_secret:
		frappe.throw(_("Stripe webhook secret is not configured."))

	timestamp, signatures = _get_signature_timestamp_and_signatures(signature_header)
	if not timestamp or not signatures:
		frappe.throw(_("Invalid Stripe webhook signature."))

	signed_payload = f"{timestamp}.{payload.decode()}".encode()
	expected_signature = hmac.new(webhook_secret.encode(), signed_payload, hashlib.sha256).hexdigest()

	if not any(hmac.compare_digest(expected_signature, signature) for signature in signatures):
		frappe.throw(_("Invalid Stripe webhook signature."))


@frappe.whitelist(allow_guest=True, methods=["POST"])
def stripe_webhook():
	payload = frappe.request.get_data()
	signature_header = frappe.get_request_header("Stripe-Signature")
	_verify_webhook_signature(payload, signature_header)

	event = json.loads(payload.decode())
	if event.get("type") == "checkout.session.completed":
		session = event.get("data", {}).get("object", {})
		sales_order_name = session.get("metadata", {}).get("sales_order")
		if session.get("payment_status") == "paid" and sales_order_name:
			try:
				_submit_sales_order(sales_order_name)
			except Exception:
				frappe.log_error(
					title="Stripe Checkout Sales Order Submission Failed",
					message=frappe.get_traceback(),
				)
		frappe.log_error(
			title="Stripe Checkout Completed",
			message=json.dumps(
				{
					"session_id": session.get("id"),
					"payment_status": session.get("payment_status"),
					"user": session.get("metadata", {}).get("user"),
					"payment_method": session.get("metadata", {}).get("payment_method"),
					"sales_order": session.get("metadata", {}).get("sales_order"),
				},
				indent=2,
			),
		)

	return {"success": True}
