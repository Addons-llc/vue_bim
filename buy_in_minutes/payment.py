import base64
import hashlib
import hmac
import json
from urllib.parse import urlencode
from urllib.error import HTTPError
from urllib.request import Request, urlopen

import frappe
from frappe import _
from frappe.utils import flt, get_url, nowdate
from erpnext.setup.doctype.brand.brand import get_brand_defaults
from erpnext.setup.doctype.item_group.item_group import get_item_group_defaults
from erpnext.stock.doctype.item.item import get_item_defaults


STRIPE_API_BASE_URL = "https://api.stripe.com/v1"
DEFAULT_CURRENCY = "aed"
HANDLING_FEE = 2
DELIVERY_FEE = 6
FREE_DELIVERY_MINIMUM = 60
SELLING_PRICE_LIST = "Selling Price"
def _error(message, status_code=400):
	frappe.local.response["http_status_code"] = status_code
	return {"success": False, "message": message}


def _get_conf_value(key):
	value = frappe.conf.get(key)
	return value.strip() if isinstance(value, str) else value


def _get_stripe_secret_key():
	return _get_conf_value("stripe_secret_key")


def _get_stripe_webhook_secret():
	return _get_conf_value("stripe_webhook_secret")


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

		if not item_code or quantity <= 0:
			frappe.throw(_("Cart contains an invalid item."))

		normalized_items.append({"item_code": item_code, "quantity": quantity})

	return normalized_items


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


def _get_default_supplier_for_item(item_code, company):
	for resolver in (get_item_defaults, get_item_group_defaults, get_brand_defaults):
		defaults = resolver(item_code, company) or {}
		supplier = defaults.get("default_supplier")
		if supplier:
			return supplier

	return None


def _get_or_create_customer_for_user(user_name):
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

		supplier = _get_default_supplier_for_item(item["item_code"], company)
		if not supplier:
			frappe.throw(
				_("This item is not available for purchase right now. Please contact support for {0}.").format(
					item["item_name"]
				)
			)

		order_items.append(
			{
				"item_code": item["item_code"],
				"item_name": item["item_name"],
				"qty": item["quantity"],
				"rate": item["rate"],
				"delivery_date": nowdate(),
				"supplier": supplier,
			}
		)

	return order_items


def _create_purchase_orders_for_sales_order(sales_order):
	if not sales_order or sales_order.docstatus != 1:
		return []

	if frappe.db.exists("Purchase Order Item", {"sales_order": sales_order.name}):
		return []

	selected_items = [
		{"item_code": item.item_code, "supplier": item.supplier}
		for item in sales_order.items
		if item.item_code and item.supplier
	]

	if not selected_items:
		return []

	from erpnext.selling.doctype.sales_order.sales_order import make_purchase_order_for_default_supplier

	return make_purchase_order_for_default_supplier(sales_order.name, selected_items=selected_items) or []


def _upsert_sales_order(checkout_items, sales_order_name=None, submit=False):
	customer = _get_or_create_customer_for_user(frappe.session.user)
	company = _get_default_company()
	delivery_date = nowdate()
	order_items = _build_sales_order_item_rows(checkout_items, company)

	if not order_items:
		frappe.throw(_("Cart does not contain orderable items."))

	if sales_order_name and frappe.db.exists("Sales Order", sales_order_name):
		sales_order = frappe.get_doc("Sales Order", sales_order_name)
		if sales_order.docstatus != 0:
			frappe.throw(_("The linked Sales Order is no longer editable."))
		sales_order.set("items", [])
	else:
		sales_order = frappe.get_doc({"doctype": "Sales Order"})

	sales_order.update(
		{
			"customer": customer,
			"company": company,
			"transaction_date": nowdate(),
			"delivery_date": delivery_date,
			"order_type": "Sales",
		}
	)
	for item in order_items:
		sales_order.append("items", item)

	if sales_order.is_new():
		sales_order.insert(ignore_permissions=True)
	else:
		sales_order.save(ignore_permissions=True)

	if submit:
		sales_order.submit()
		_create_purchase_orders_for_sales_order(sales_order)

	return sales_order


def _build_checkout_params(checkout_items, sales_order_name=None):
	success_url = get_url("/buy-in-minutes#/payment/success?method=stripe&session_id={CHECKOUT_SESSION_ID}")
	cancel_url = get_url("/buy-in-minutes#/payment/cancel")
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
		params[f"line_items[{index}][price_data][currency]"] = DEFAULT_CURRENCY
		params[f"line_items[{index}][price_data][unit_amount]"] = unit_amount
		params[f"line_items[{index}][price_data][product_data][name]"] = item["item_name"]
		params[f"line_items[{index}][price_data][product_data][metadata][item_code]"] = item["item_code"]

	return params


def _submit_sales_order(sales_order_name):
	if not sales_order_name or not frappe.db.exists("Sales Order", sales_order_name):
		return None

	sales_order = frappe.get_doc("Sales Order", sales_order_name)
	if sales_order.docstatus != 0:
		return sales_order

	sales_order.submit()
	_create_purchase_orders_for_sales_order(sales_order)
	return sales_order


@frappe.whitelist(methods=["POST"])
def finalize_stripe_checkout(session_id=None):
	if frappe.session.user == "Guest":
		frappe.throw(_("Please sign in before checkout."), frappe.AuthenticationError)

	if not session_id:
		frappe.throw(_("Missing Stripe session id."))

	session = _stripe_get_request(f"/checkout/sessions/{session_id}")
	if session.get("payment_status") != "paid":
		frappe.throw(_("Stripe payment is not complete yet."))

	sales_order_name = session.get("metadata", {}).get("sales_order")
	sales_order = _submit_sales_order(sales_order_name)

	return {
		"success": True,
		"sales_order": sales_order.name if sales_order else sales_order_name,
		"payment_status": session.get("payment_status"),
	}


@frappe.whitelist(methods=["POST"])
def sync_cart_sales_order(cart_items=None, sales_order_name=None):
	if frappe.session.user == "Guest":
		frappe.throw(_("Please sign in before checkout."), frappe.AuthenticationError)

	checkout_items = _get_checkout_items(cart_items)
	sales_order = _upsert_sales_order(checkout_items, sales_order_name=sales_order_name)

	return {
		"success": True,
		"sales_order": sales_order.name,
	}


@frappe.whitelist(methods=["POST"])
def create_checkout_session(cart_items=None, sales_order_name=None):
	if frappe.session.user == "Guest":
		frappe.throw(_("Please sign in before checkout."), frappe.AuthenticationError)

	checkout_items = _get_checkout_items(cart_items)
	sales_order = _upsert_sales_order(checkout_items, sales_order_name=sales_order_name)
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
def create_cash_on_delivery_order(cart_items=None, sales_order_name=None):
	if frappe.session.user == "Guest":
		frappe.throw(_("Please sign in before checkout."), frappe.AuthenticationError)

	checkout_items = _get_checkout_items(cart_items)
	sales_order = _upsert_sales_order(checkout_items, sales_order_name=sales_order_name, submit=True)

	return {
		"success": True,
		"sales_order": sales_order.name,
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
