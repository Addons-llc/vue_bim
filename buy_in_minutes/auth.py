import re
import time

import frappe
import frappe.sessions
from frappe import _
from frappe.auth import LoginManager
from frappe.model.rename_doc import rename_doc
from frappe.utils import validate_email_address
from twilio.base.exceptions import TwilioRestException
from twilio.rest import Client


DEFAULT_COUNTRY_CODE = "+971"
PHONE_PATTERN = re.compile(r"^\+\d{8,15}$")
OTP_PATTERN = re.compile(r"^\d{4,10}$")
SETTINGS_DOCTYPE = "BIM Twilio Verify Settings"
PHONE_USER_EMAIL_DOMAIN = "phone.buy-in-minutes.local"
DEFAULT_OTP_REQUEST_LIMIT = 100
DEFAULT_OTP_VERIFY_LIMIT = 30
DEFAULT_OTP_RATE_LIMIT_SECONDS = 10 * 60
DEFAULT_OTP_REQUEST_COOLDOWN_SECONDS = 60
OTP_RATE_LIMIT_CACHE_VERSION = "v2"
PROFILE_TOKEN_TTL_SECONDS = 10 * 60


def _error(message, status_code=400):
	frappe.local.response["http_status_code"] = status_code
	return {"success": False, "message": message}


def _get_conf_value(key):
	value = frappe.conf.get(key)
	return value.strip() if isinstance(value, str) else value


def _get_conf_int(key, default):
	try:
		return int(frappe.conf.get(key, default))
	except (TypeError, ValueError):
		return default


def _get_conf_list(key):
	value = frappe.conf.get(key)
	if isinstance(value, str):
		return [item.strip() for item in value.split(",") if item.strip()]
	if isinstance(value, list | tuple | set):
		return [str(item).strip() for item in value if str(item).strip()]

	return []


def _get_otp_request_limit():
	return _get_conf_int("phone_login_otp_request_limit", DEFAULT_OTP_REQUEST_LIMIT)


def _get_otp_verify_limit():
	return _get_conf_int("phone_login_otp_verify_limit", DEFAULT_OTP_VERIFY_LIMIT)


def _get_otp_request_cooldown_seconds():
	return _get_conf_int("phone_login_otp_request_cooldown_seconds", DEFAULT_OTP_REQUEST_COOLDOWN_SECONDS)


def _get_test_otp():
	otp = _get_conf_value("phone_login_test_otp")
	return otp if otp and OTP_PATTERN.match(otp) else None


def _is_test_otp_enabled(phone_number):
	test_otp = _get_test_otp()
	if not test_otp:
		return False

	return phone_number in {_normalize_phone(phone) for phone in _get_conf_list("phone_login_test_phone_numbers")}


def _check_otp_rate_limit(action, phone_number, limit):
	if limit <= 0:
		return None

	cache_key = frappe.cache.make_key(
		f"rl:{OTP_RATE_LIMIT_CACHE_VERSION}:buy_in_minutes.auth.{action}:{phone_number}"
	)
	value = frappe.cache.get(cache_key) or 0
	if not value:
		frappe.cache.setex(cache_key, DEFAULT_OTP_RATE_LIMIT_SECONDS, 0)

	value = frappe.cache.incrby(cache_key, 1)
	if value > limit:
		return _error(
			_("Too many OTP requests. Please wait a few minutes before trying again."),
			429,
		)

	return None


def _get_otp_request_cooldown_key(phone_number):
	return frappe.cache.make_key(f"otp-request-cooldown:{OTP_RATE_LIMIT_CACHE_VERSION}:{phone_number}")


def _get_phone_profile_token_key(profile_token):
	return frappe.cache.make_key(f"phone-profile-token:{OTP_RATE_LIMIT_CACHE_VERSION}:{profile_token}")


def _check_otp_request_cooldown(phone_number):
	cooldown_seconds = _get_otp_request_cooldown_seconds()
	if cooldown_seconds <= 0:
		return None

	expires_at = frappe.cache.get(_get_otp_request_cooldown_key(phone_number))
	try:
		seconds_remaining = int(float(expires_at) - time.time()) if expires_at else 0
	except (TypeError, ValueError):
		seconds_remaining = 0

	if seconds_remaining > 0:
		return _error(
			_("Please wait {0} seconds before requesting another OTP.").format(seconds_remaining),
			429,
		)

	return None


def _set_otp_request_cooldown(phone_number):
	cooldown_seconds = _get_otp_request_cooldown_seconds()
	if cooldown_seconds <= 0:
		return

	frappe.cache.setex(
		_get_otp_request_cooldown_key(phone_number),
		cooldown_seconds,
		time.time() + cooldown_seconds,
	)


def _create_phone_profile_token(phone_number):
	profile_token = frappe.generate_hash(length=32)
	frappe.cache.setex(_get_phone_profile_token_key(profile_token), PROFILE_TOKEN_TTL_SECONDS, phone_number)
	return profile_token


def _validate_phone_profile_token(profile_token, phone_number):
	profile_token = (profile_token or "").strip()
	if not profile_token:
		frappe.throw(_("Please verify the OTP before completing your profile."), frappe.AuthenticationError)

	cached_phone_number = frappe.cache.get(_get_phone_profile_token_key(profile_token))
	if isinstance(cached_phone_number, bytes):
		cached_phone_number = cached_phone_number.decode()

	if cached_phone_number != phone_number:
		frappe.throw(_("Your verification has expired. Please verify the OTP again."), frappe.AuthenticationError)

	return profile_token


def _clear_phone_profile_token(profile_token):
	if profile_token:
		frappe.cache.delete_value(_get_phone_profile_token_key(profile_token))


def _format_twilio_error(exc):
	error_code = f" Twilio error code: {exc.code}." if exc.code else ""

	if exc.status == 403:
		return _(
			"Twilio rejected the OTP request. Check the Verify service, SMS geo permissions, "
			"trial account recipient verification, and account credentials."
		) + error_code

	if exc.status == 429:
		return _("Too many OTP requests were sent to this phone number. Please wait a few minutes and try again.")

	return _("Unable to send OTP. Please try again.") + error_code


def _get_settings():
	if frappe.db.exists("DocType", SETTINGS_DOCTYPE):
		settings = frappe.get_single(SETTINGS_DOCTYPE)
		auth_token = settings.get_password("auth_token") if settings.auth_token else None
		if settings.enabled and settings.account_sid and auth_token and settings.verify_service_sid:
			return {
				"account_sid": settings.account_sid,
				"auth_token": auth_token,
				"verify_service_sid": settings.verify_service_sid,
				"default_country_code": settings.default_country_code or DEFAULT_COUNTRY_CODE,
			}

	return {
		"account_sid": _get_conf_value("twilio_account_sid"),
		"auth_token": _get_conf_value("twilio_auth_token"),
		"verify_service_sid": _get_conf_value("twilio_verify_service_sid"),
		"default_country_code": _get_conf_value("phone_login_default_country_code") or DEFAULT_COUNTRY_CODE,
	}


def _get_twilio_client():
	settings = _get_settings()
	account_sid = settings.get("account_sid")
	auth_token = settings.get("auth_token")
	service_sid = settings.get("verify_service_sid")

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
		country_code = _get_settings().get("default_country_code") or DEFAULT_COUNTRY_CODE
		if not country_code.startswith("+"):
			country_code = f"+{country_code}"
		phone_number = f"{country_code}{phone_number.lstrip('0')}"

	if not PHONE_PATTERN.match(phone_number):
		frappe.throw(_("Enter a valid phone number."))

	return phone_number


def _get_existing_website_user_by_phone(phone_number):
	user_name = frappe.db.get_value(
		"User",
		{"mobile_no": phone_number, "user_type": "Website User"},
		"name",
	)
	if user_name:
		user = frappe.get_doc("User", user_name)
		if not user.enabled:
			frappe.throw(_("User disabled or missing"), frappe.AuthenticationError)
		return user

	digits = re.sub(r"\D", "", phone_number)
	email = f"{digits}@{PHONE_USER_EMAIL_DOMAIN}"
	if frappe.db.exists("User", email):
		user = frappe.get_doc("User", email)
		if not user.enabled:
			frappe.throw(_("User disabled or missing"), frappe.AuthenticationError)
		if user.user_type != "Website User":
			frappe.throw(_("Only website users can sign in with phone OTP."))
		user.mobile_no = phone_number
		user.phone = phone_number
		user.enabled = 1
		user.save(ignore_permissions=True)
		frappe.db.commit()
		return user

	return None


def _create_profile_website_user(full_name, email, phone_number):
	if frappe.db.exists("User", email):
		frappe.throw(_("A user with this email address already exists."))

	if _get_existing_website_user_by_phone(phone_number):
		frappe.throw(_("A user with this phone number already exists. Please sign in again."))

	first_name, last_name = _split_full_name(full_name)
	user = frappe.get_doc(
		{
			"doctype": "User",
			"email": email,
			"first_name": first_name,
			"last_name": last_name,
			"full_name": full_name,
			"enabled": 1,
			"user_type": "Website User",
			"send_welcome_email": 0,
			"mobile_no": phone_number,
			"phone": phone_number,
		}
	)

	if frappe.db.exists("Role", "Customer"):
		user.append("roles", {"role": "Customer"})

	user.insert(ignore_permissions=True)
	frappe.db.commit()
	return user


def _get_phone_user_payload(user, is_new_user):
	needs_profile = _needs_phone_profile(user)

	return {
		"is_new_user": is_new_user,
		"website_user_created": is_new_user,
		"website_user_exists": not is_new_user,
		"needs_profile": needs_profile,
		"profile_completed": not needs_profile,
		"user": {
			"name": user.name,
			"email": user.email,
			"mobile_no": user.mobile_no,
			"full_name": user.full_name,
		},
	}


def _login_user(user_name):
	frappe.local.login_manager = LoginManager()
	frappe.local.login_manager.login_as(user_name)
	frappe.db.commit()


def _split_full_name(full_name):
	names = full_name.strip().split()
	first_name = names[0] if names else _("Customer")
	last_name = " ".join(names[1:])

	return first_name, last_name


def _is_phone_login_user(user):
	return bool(user.name.endswith(f"@{PHONE_USER_EMAIL_DOMAIN}"))


def _needs_phone_profile(user):
	return _is_phone_login_user(user)


def _rename_phone_user_if_needed(user, email):
	if not email or user.name == email:
		return user

	if not _is_phone_login_user(user):
		frappe.throw(_("This account already has an email address."))

	if frappe.db.exists("User", email):
		frappe.throw(_("A user with this email address already exists."))

	new_name = rename_doc(
		"User",
		user.name,
		email,
		force=True,
		ignore_permissions=True,
		show_alert=False,
	)
	frappe.local.login_manager = LoginManager()
	frappe.local.login_manager.login_as(new_name)

	return frappe.get_doc("User", new_name)


@frappe.whitelist(allow_guest=True, methods=["GET"])
def get_csrf_token():
	return {"csrf_token": frappe.sessions.get_csrf_token()}


@frappe.whitelist(allow_guest=True, methods=["GET", "POST"])
def request_phone_otp(phone_number=None, phoneNumber=None):
	phone_number = _normalize_phone(phone_number or phoneNumber)
	cooldown_response = _check_otp_request_cooldown(phone_number)
	if cooldown_response:
		return cooldown_response

	rate_limit_response = _check_otp_rate_limit("request_phone_otp", phone_number, _get_otp_request_limit())
	if rate_limit_response:
		return rate_limit_response

	if _is_test_otp_enabled(phone_number):
		_set_otp_request_cooldown(phone_number)
		return {
			"success": True,
			"status": "test",
			"message": _("Test OTP enabled. Use the configured OTP to continue."),
		}

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
		return _error(_format_twilio_error(exc), exc.status or 400)

	_set_otp_request_cooldown(phone_number)

	return {
		"success": True,
		"status": verification.status,
		"message": _("OTP sent successfully."),
	}


@frappe.whitelist(allow_guest=True, methods=["POST"])
def verify_phone_otp(phone_number=None, otp=None, phoneNumber=None):
	phone_number = _normalize_phone(phone_number or phoneNumber)
	rate_limit_response = _check_otp_rate_limit("verify_phone_otp", phone_number, _get_otp_verify_limit())
	if rate_limit_response:
		return rate_limit_response

	otp = (otp or "").strip()

	if not OTP_PATTERN.match(otp):
		return _error(_("Enter a valid OTP."))

	test_otp = _get_test_otp()
	if _is_test_otp_enabled(phone_number):
		if otp != test_otp:
			return _error(_("Invalid OTP."), 400)

		user = _get_existing_website_user_by_phone(phone_number)
		if not user:
			return {
				"success": True,
				"is_new_user": True,
				"website_user_created": False,
				"website_user_exists": False,
				"needs_profile": True,
				"profile_completed": False,
				"profile_token": _create_phone_profile_token(phone_number),
				"message": _("OTP verified. Complete your profile to continue."),
			}

		_login_user(user.name)

		return {
			"success": True,
			**_get_phone_user_payload(user, False),
			"message": _("Logged in successfully."),
		}

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

	user = _get_existing_website_user_by_phone(phone_number)
	if not user:
		return {
			"success": True,
			"is_new_user": True,
			"website_user_created": False,
			"website_user_exists": False,
			"needs_profile": True,
			"profile_completed": False,
			"profile_token": _create_phone_profile_token(phone_number),
			"message": _("OTP verified. Complete your profile to continue."),
		}

	_login_user(user.name)

	return {
		"success": True,
		**_get_phone_user_payload(user, False),
		"message": _("Logged in successfully."),
	}


@frappe.whitelist(allow_guest=True, methods=["POST"])
def complete_phone_profile(full_name=None, email=None, phone_number=None, phoneNumber=None, profile_token=None):
	phone_number = _normalize_phone(phone_number or phoneNumber)
	full_name = (full_name or "").strip()
	email = validate_email_address(email, throw=True)

	if not full_name:
		frappe.throw(_("Full name is required."))

	if frappe.session.user == "Guest":
		profile_token = _validate_phone_profile_token(profile_token, phone_number)
		user = _create_profile_website_user(full_name, email, phone_number)
		_login_user(user.name)
		_clear_phone_profile_token(profile_token)

		return {
			"success": True,
			"user": {
				"name": user.name,
				"email": user.email,
				"mobile_no": user.mobile_no,
				"full_name": user.full_name,
			},
			"message": _("Profile completed successfully."),
		}

	user = frappe.get_doc("User", frappe.session.user)
	if user.user_type != "Website User":
		frappe.throw(_("Only website users can complete this profile."))

	if user.mobile_no and _normalize_phone(user.mobile_no) != phone_number:
		frappe.throw(_("This phone number does not match the signed-in account."))

	user = _rename_phone_user_if_needed(user, email)
	first_name, last_name = _split_full_name(full_name)
	user.first_name = first_name
	user.last_name = last_name
	user.full_name = full_name
	user.mobile_no = phone_number
	user.phone = phone_number
	user.enabled = 1
	user.user_type = "Website User"
	user.save(ignore_permissions=True)
	frappe.db.commit()

	return {
		"success": True,
		"user": {
			"name": user.name,
			"email": user.email,
			"mobile_no": user.mobile_no,
			"full_name": user.full_name,
		},
		"message": _("Profile completed successfully."),
	}
