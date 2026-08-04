import base64
import hashlib
import hmac
import json
from urllib.parse import urlencode
from urllib.error import HTTPError
from urllib.request import Request, urlopen

import frappe
from frappe import _
from frappe.utils import flt, get_url


STRIPE_API_BASE_URL = "https://api.stripe.com/v1"
DEFAULT_CURRENCY = "aed"
HANDLING_FEE = 2
DELIVERY_FEE = 6
FREE_DELIVERY_MINIMUM = 60


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

		rate = flt(item.standard_rate)
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


def _build_checkout_params(checkout_items):
	success_url = get_url("/buy-in-minutes#/payment/success?session_id={CHECKOUT_SESSION_ID}")
	cancel_url = get_url("/buy-in-minutes#/payment/cancel")
	params = {
		"mode": "payment",
		"success_url": success_url,
		"cancel_url": cancel_url,
		"client_reference_id": frappe.session.user,
		"metadata[user]": frappe.session.user,
	}

	for index, item in enumerate(checkout_items):
		unit_amount = int(round(item["rate"] * 100))
		params[f"line_items[{index}][quantity]"] = item["quantity"]
		params[f"line_items[{index}][price_data][currency]"] = DEFAULT_CURRENCY
		params[f"line_items[{index}][price_data][unit_amount]"] = unit_amount
		params[f"line_items[{index}][price_data][product_data][name]"] = item["item_name"]
		params[f"line_items[{index}][price_data][product_data][metadata][item_code]"] = item["item_code"]

	return params


@frappe.whitelist(methods=["POST"])
def create_checkout_session(cart_items=None):
	if frappe.session.user == "Guest":
		frappe.throw(_("Please sign in before checkout."), frappe.AuthenticationError)

	checkout_items = _get_checkout_items(cart_items)
	session = _stripe_request("/checkout/sessions", _build_checkout_params(checkout_items))

	return {
		"success": True,
		"checkout_url": session.get("url"),
		"session_id": session.get("id"),
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
		frappe.log_error(
			title="Stripe Checkout Completed",
			message=json.dumps(
				{
					"session_id": session.get("id"),
					"payment_status": session.get("payment_status"),
					"user": session.get("metadata", {}).get("user"),
				},
				indent=2,
			),
		)

	return {"success": True}
