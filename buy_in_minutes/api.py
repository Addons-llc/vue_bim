import re

import frappe
from frappe import _
from twilio.base.exceptions import TwilioRestException
from twilio.rest import Client


@frappe.whitelist(allow_guest=True)
def get_items(limit_page_length=20, search=None, item_group=None):
	limit_page_length = frappe.utils.cint(limit_page_length) or 20

	filters = {"disabled": 0}

	if item_group:
		filters["item_group"] = item_group

	if search:
		filters["item_name"] = ["like", f"%{search}%"]

	items = frappe.get_all(
		"Item",
		fields=[
			"name",
			"item_code",
			"item_name",
			"item_group",
			"description",
			"image",
			"website_image",
			"thumbnail",
			"standard_rate",
			"disabled",
		],
		filters=filters,
		order_by="modified desc",
		limit_page_length=limit_page_length,
	)

	return items


def format_phone_number(phone_number, default_country_code="+971"):
	phone_number = str(phone_number or "").strip()
	phone_number = re.sub(r"[^\d+]", "", phone_number)

	if phone_number.startswith("00"):
		phone_number = f"+{phone_number[2:]}"

	if phone_number.startswith("+"):
		return phone_number

	if phone_number.startswith("0"):
		phone_number = phone_number[1:]

	return f"{default_country_code}{phone_number}"


@frappe.whitelist(allow_guest=True)
def send_otp(phone_number):
	if not phone_number:
		frappe.throw(_("Phone number is required."))

	settings = frappe.get_single("Twilio Settings")

	if not settings.enabled:
		frappe.throw(_("Twilio OTP login is disabled."))

	account_sid = settings.account_sid
	auth_token = settings.get_password("auth_token")
	verify_service_sid = settings.verify_service_sid
	default_country_code = settings.default_country_code or "+971"

	if not account_sid or not auth_token or not verify_service_sid:
		frappe.throw(_("Twilio Settings are incomplete."))

	formatted_phone = format_phone_number(
		phone_number,
		default_country_code,
	)

	try:
		client = Client(account_sid, auth_token)

		verification = (
			client.verify.v2.services(verify_service_sid)
			.verifications.create(
				to=formatted_phone,
				channel="sms",
			)
		)

		return {
			"success": True,
			"phone_number": formatted_phone,
			"status": verification.status,
			"message": _("OTP sent successfully."),
		}

	except TwilioRestException as error:
		frappe.log_error(
			title="Twilio Send OTP Error",
			message=frappe.get_traceback(),
		)

		frappe.throw(
			_("Unable to send OTP: {0}").format(error.msg)
		)