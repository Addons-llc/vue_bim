import re

import frappe
import frappe.sessions
from frappe import _
from frappe.auth import LoginManager
from frappe.rate_limiter import rate_limit
from twilio.base.exceptions import TwilioRestException
from twilio.rest import Client


DEFAULT_COUNTRY_CODE = "+971"
PHONE_PATTERN = re.compile(r"^\+\d{8,15}$")
OTP_PATTERN = re.compile(r"^\d{4,10}$")


def _error(message, status_code=400):
	frappe.local.response["http_status_code"] = status_code
	return {"success": False, "message": message}


def _get_conf_value(key):
	value = frappe.conf.get(key)
	return value.strip() if isinstance(value, str) else value


def _get_twilio_client():
	account_sid = _get_conf_value("twilio_account_sid")
	auth_token = _get_conf_value("twilio_auth_token")
	service_sid = _get_conf_value("twilio_verify_service_sid")

	if not account_sid or not auth_token or not service_sid:
		frappe.throw(_("Twilio phone login is not configured."))

	return Client(account_sid, auth_token), service_sid


def _normalize_phone(phone_number):
	phone_number = re.sub(r"[^\d+]", "", (phone_number or "").strip())

	if not phone_number:
		frappe.throw(_("Phone number is required."))

	if phone_number.startswith("00"):
		phone_number = f"+{phone_number[2:]}"
	elif not phone_number.startswith("+"):
		country_code = _get_conf_value("phone_login_default_country_code") or DEFAULT_COUNTRY_CODE
		if not country_code.startswith("+"):
			country_code = f"+{country_code}"
		phone_number = f"{country_code}{phone_number.lstrip('0')}"

	if not PHONE_PATTERN.match(phone_number):
		frappe.throw(_("Enter a valid phone number."))

	return phone_number


def _get_or_create_phone_user(phone_number):
	user_name = frappe.db.get_value("User", {"mobile_no": phone_number}, "name")
	if user_name:
		user = frappe.get_doc("User", user_name)
		if not user.enabled:
			frappe.throw(_("User disabled or missing"), frappe.AuthenticationError)
		return user, False

	digits = re.sub(r"\D", "", phone_number)
	email = f"{digits}@phone.buy-in-minutes.local"
	if frappe.db.exists("User", email):
		user = frappe.get_doc("User", email)
		user.mobile_no = phone_number
		user.enabled = 1
		user.save(ignore_permissions=True)
		return user, False

	user = frappe.get_doc(
		{
			"doctype": "User",
			"email": email,
			"first_name": _("Customer"),
			"enabled": 1,
			"user_type": "Website User",
			"send_welcome_email": 0,
			"mobile_no": phone_number,
		}
	)

	if frappe.db.exists("Role", "Customer"):
		user.append("roles", {"role": "Customer"})

	user.insert(ignore_permissions=True)
	return user, True


def _login_user(user_name):
	frappe.local.login_manager = LoginManager()
	frappe.local.login_manager.login_as(user_name)
	frappe.db.commit()


@frappe.whitelist(allow_guest=True, methods=["GET"])
def get_csrf_token():
	return {"csrf_token": frappe.sessions.get_csrf_token()}


@frappe.whitelist(allow_guest=True)
@rate_limit(key="phone_number", limit=5, seconds=10 * 60, methods="POST", ip_based=True)
def request_phone_otp(phone_number=None):
	phone_number = _normalize_phone(phone_number)
	client, service_sid = _get_twilio_client()

	try:
		verification = client.verify.v2.services(service_sid).verifications.create(
			to=phone_number,
			channel="sms",
		)
	except TwilioRestException as exc:
		frappe.log_error(
			title="Twilio OTP Request Failed",
			message=f"Twilio error {exc.code}: {exc.msg}",
		)
		return _error(_("Unable to send OTP. Please try again."), exc.status or 400)

	return {
		"success": True,
		"status": verification.status,
		"message": _("OTP sent successfully."),
	}


@frappe.whitelist(allow_guest=True)
@rate_limit(key="phone_number", limit=10, seconds=10 * 60, methods="POST", ip_based=True)
def verify_phone_otp(phone_number=None, otp=None):
	phone_number = _normalize_phone(phone_number)
	otp = (otp or "").strip()

	if not OTP_PATTERN.match(otp):
		return _error(_("Enter a valid OTP."))

	client, service_sid = _get_twilio_client()

	try:
		check = client.verify.v2.services(service_sid).verification_checks.create(
			to=phone_number,
			code=otp,
		)
	except TwilioRestException as exc:
		frappe.log_error(
			title="Twilio OTP Verification Failed",
			message=f"Twilio error {exc.code}: {exc.msg}",
		)
		return _error(_("Unable to verify OTP. Please try again."), exc.status or 400)

	if check.status != "approved":
		return _error(_("Invalid OTP."), 400)

	user, is_new_user = _get_or_create_phone_user(phone_number)
	_login_user(user.name)

	return {
		"success": True,
		"is_new_user": is_new_user,
		"user": {
			"name": user.name,
			"email": user.email,
			"mobile_no": user.mobile_no,
			"full_name": user.full_name,
		},
		"message": _("Logged in successfully."),
	}
