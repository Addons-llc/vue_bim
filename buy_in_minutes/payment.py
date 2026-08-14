import base64
import hashlib
import hmac
import json
from contextlib import contextmanager
from urllib.parse import urlencode
from urllib.error import HTTPError
from urllib.request import Request, urlopen

import frappe
from frappe import _
from frappe.utils import flt, get_url, getdate, nowdate
from erpnext.setup.doctype.brand.brand import get_brand_defaults
from erpnext.setup.doctype.item_group.item_group import get_item_group_defaults
from erpnext.stock.doctype.item.item import get_item_defaults


STRIPE_API_BASE_URL = "https://api.stripe.com/v1"
DEFAULT_CURRENCY = "aed"
HANDLING_FEE = 2
DELIVERY_FEE = 6
FREE_DELIVERY_MINIMUM = 60
SELLING_PRICE_LIST = "Selling Price"
STRIPE_SETTINGS_DOCTYPE = "Stripe Settings"
def _error(message, status_code=400):
	frappe.local.response["http_status_code"] = status_code
	return {"success": False, "message": message}


def _get_conf_value(key):
	value = frappe.conf.get(key)
	return value.strip() if isinstance(value, str) else value


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
	return _get_stripe_settings().get("secret_key")


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

		if not item_code or quantity <= 0:
			frappe.throw(_("Cart contains an invalid item."))

		normalized_items.append(
			{
				"item_code": item_code,
				"quantity": quantity,
				"supplier": supplier,
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
	user_name = user_name if user_name is not None else frappe.session.user
	return not user_name or user_name == "Guest"


def _require_checkout_user():
	if _is_guest_user():
		frappe.throw(_("Please sign in before checkout."), frappe.AuthenticationError)

	return frappe.session.user


def _get_or_create_customer_for_user(user_name):
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
		"building": _clean_text(delivery_address.get("building")),
		"landmark": _clean_text(delivery_address.get("landmark")),
		"latitude": _clean_text(delivery_address.get("latitude")),
		"longitude": _clean_text(delivery_address.get("longitude")),
	}


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
			"address_line1": address["building"],
			"address_line2": address["area"],
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


def _apply_delivery_address_to_sales_order(sales_order, customer, delivery_address):
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


def _get_checkout_items(cart_items):
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
			}
		)

	subtotal = sum(item["amount"] for item in checkout_items)
	if checkout_items:
		checkout_items.append(
			{
				"item_code": "handling-fee",
				"item_name": _("Handling charge"),
				"quantity": 1,
				"rate": HANDLING_FEE,
				"amount": HANDLING_FEE,
			}
		)

	if checkout_items and subtotal < FREE_DELIVERY_MINIMUM:
		checkout_items.append(
			{
				"item_code": "delivery-fee",
				"item_name": _("Delivery charge"),
				"quantity": 1,
				"rate": DELIVERY_FEE,
				"amount": DELIVERY_FEE,
			}
		)

	return checkout_items


def _build_sales_order_item_rows(checkout_items, company):
	order_items = []
	for item in checkout_items:
		if not frappe.db.exists("Item", item["item_code"]):
			continue

		supplier = _get_default_supplier_for_item(
			item["item_code"],
			company,
			item.get("supplier"),
		)

		row = {
			"item_code": item["item_code"],
			"item_name": item["item_name"],
			"qty": item["quantity"],
			"rate": item["rate"],
			"delivery_date": nowdate(),
		}
		if supplier:
			row["supplier"] = supplier
			row["delivered_by_supplier"] = 1

		order_items.append(row)

	return order_items


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
	)

	return [
		frappe.get_doc("Purchase Order", purchase_order_name)
		for purchase_order_name in dict.fromkeys(purchase_order_names)
		if purchase_order_name
	]


def _get_purchase_orderable_sales_order_items(sales_order):
	return [
		{"item_code": item.item_code, "supplier": item.supplier}
		for item in sales_order.items
		if item.item_code
		and item.supplier
		and flt(item.ordered_qty) < flt(item.stock_qty)
	]


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

	from erpnext.selling.doctype.sales_order.sales_order import make_purchase_order_for_default_supplier

	try:
		purchase_orders = make_purchase_order_for_default_supplier(sales_order.name, selected_items=selected_items) or []
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
			with _as_administrator():
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


@contextmanager
def _as_administrator():
	previous_user = frappe.session.user or "Guest"
	frappe.set_user("Administrator")
	try:
		yield
	finally:
		frappe.set_user(previous_user)


def _normalize_payment_schedule_dates(sales_order):
	transaction_date = sales_order.transaction_date or nowdate()
	transaction_date_value = getdate(transaction_date)

	for payment_row in sales_order.get("payment_schedule") or []:
		if not payment_row.due_date or getdate(payment_row.due_date) < transaction_date_value:
			payment_row.due_date = transaction_date


def _upsert_sales_order(checkout_items, sales_order_name=None, submit=False, delivery_address=None):
	customer = _get_or_create_customer_for_user(frappe.session.user)
	company = _get_default_company()
	order_date = nowdate()
	delivery_date = order_date
	order_items = _build_sales_order_item_rows(checkout_items, company)

	if not order_items:
		frappe.throw(_("Cart does not contain orderable items."))

	if sales_order_name and frappe.db.exists("Sales Order", sales_order_name):
		sales_order_owner = frappe.db.sql(
			"select owner from `tabSales Order` where name = %s",
			(sales_order_name,),
			as_dict=True,
		)
		if not sales_order_owner or sales_order_owner[0].owner != frappe.session.user:
			frappe.throw(_("The linked Sales Order is no longer editable."))

		with _as_administrator():
			sales_order = frappe.get_doc("Sales Order", sales_order_name)
			if sales_order.docstatus != 0:
				frappe.throw(_("The linked Sales Order is no longer editable."))
			sales_order.set("items", [])
			sales_order.set("payment_schedule", [])
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
	for item in order_items:
		sales_order.append("items", item)

	_apply_delivery_address_to_sales_order(sales_order, customer, delivery_address)
	_normalize_payment_schedule_dates(sales_order)

	if sales_order.is_new():
		sales_order.insert(ignore_permissions=True)
	else:
		sales_order.save(ignore_permissions=True)

	if submit:
		with _as_administrator():
			sales_order.flags.ignore_permissions = True
			sales_order.submit()
			sales_order.purchase_orders = _create_purchase_orders_for_sales_order(sales_order)

	return sales_order


def _build_checkout_params(checkout_items, sales_order_name=None):
	success_url = get_url("/buy-in-minutes#/payment/success?method=stripe&session_id={CHECKOUT_SESSION_ID}")
	cancel_url = get_url("/buy-in-minutes#/payment/cancel")
	stripe_currency = _get_stripe_settings().get("currency") or DEFAULT_CURRENCY
	params = {
		"mode": "payment",
		"success_url": success_url,
		"cancel_url": cancel_url,
		"client_reference_id": frappe.session.user,
		"metadata[user]": frappe.session.user,
		"metadata[payment_method]": "stripe",
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

	with _as_administrator():
		sales_order = frappe.get_doc("Sales Order", sales_order_name)

		if sales_order.docstatus == 2:
			frappe.throw(
				_("Sales Order {0} is cancelled.").format(sales_order_name)
			)

		# Submit the Sales Order after successful Stripe payment
		if sales_order.docstatus == 0:
			sales_order.flags.ignore_permissions = True
			sales_order.submit()

		# Create Purchase Orders first
		_create_purchase_orders_for_sales_order(sales_order)

		# Force the status after ERPNext completes its submit processing
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

	return {
		"success": True,
		"sales_order": sales_order.name,
		"sales_order_status": sales_order.status,
		"docstatus": sales_order.docstatus,
		"payment_status": session.get("payment_status"),
		"items": _get_sales_order_item_summary(sales_order),
	}


@frappe.whitelist(methods=["POST"])
def sync_cart_sales_order(cart_items=None, sales_order_name=None, delivery_address=None):
	_require_checkout_user()

	checkout_items = _get_checkout_items(cart_items)
	sales_order = _upsert_sales_order(
		checkout_items,
		sales_order_name=sales_order_name,
		delivery_address=delivery_address,
	)

	return {
		"success": True,
		"sales_order": sales_order.name,
	}


@frappe.whitelist(methods=["POST"])
def create_checkout_session(cart_items=None, sales_order_name=None, delivery_address=None):
	_require_checkout_user()

	checkout_items = _get_checkout_items(cart_items)
	sales_order = _upsert_sales_order(
		checkout_items,
		sales_order_name=sales_order_name,
		delivery_address=delivery_address,
	)
	session = _stripe_request(
		"/checkout/sessions",
		_build_checkout_params(checkout_items, sales_order.name),
	)

	return {
		"success": True,
		"checkout_url": session.get("url"),
		"session_id": session.get("id"),
		"sales_order": sales_order.name,
	}


@frappe.whitelist(methods=["POST"])
def create_cash_on_delivery_order(cart_items=None, sales_order_name=None, delivery_address=None):
	_require_checkout_user()

	checkout_items = _get_checkout_items(cart_items)
	sales_order = _upsert_sales_order(
		checkout_items,
		sales_order_name=sales_order_name,
		submit=True,
		delivery_address=delivery_address,
	)
	purchase_orders = getattr(sales_order, "purchase_orders", None)

	if purchase_orders is None:
		purchase_orders = _get_purchase_orders_for_sales_order(sales_order.name)

	return {
		"success": True,
		"sales_order": sales_order.name,
		"purchase_orders": [purchase_order.name for purchase_order in purchase_orders],
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
