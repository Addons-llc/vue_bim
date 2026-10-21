import re
import time
import json

import frappe
import frappe.sessions
import requests
from frappe import _
from frappe.auth import LoginManager
from frappe.model.rename_doc import rename_doc
from frappe.sessions import get_expiry_in_seconds
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
DEFAULT_PHONE_LOGIN_SESSION_EXPIRY = "87600:00:00"
OTP_RATE_LIMIT_CACHE_VERSION = "v2"
PROFILE_TOKEN_TTL_SECONDS = 10 * 60
WEBSITE_LOGIN_TOKEN_TTL_SECONDS = 30 * 24 * 60 * 60
PHONE_AUTH_FLOW_TOKEN_TTL_SECONDS = 10 * 60
GOOGLE_TOKENINFO_URL = "https://oauth2.googleapis.com/tokeninfo"
GOOGLE_TOKEN_ISSUERS = {"accounts.google.com", "https://accounts.google.com"}
GOOGLE_USERINFO_URL = "https://openidconnect.googleapis.com/v1/userinfo"
# OAuth "web" client the mobile app requests ID tokens for. Override (or add
# more, e.g. an iOS/web app's client) with `google_oauth_client_ids` in
# site_config.json.
DEFAULT_GOOGLE_OAUTH_CLIENT_IDS = ["408596288649-1dv8u1abgrjlug0f5cm7buskl6ci2olu.apps.googleusercontent.com"]


def _error(message, status_code=400):
	frappe.local.response["http_status_code"] = status_code
	return {"success": False, "message": message}


def _log_phone_auth_response(action, phone_number, payload):
	frappe.logger("buy_in_minutes.auth").info(
		f"{action} response for {phone_number}: {frappe.as_json(payload, indent=None)}"
	)


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


def _get_phone_login_session_expiry():
	session_expiry = _get_conf_value("phone_login_session_expiry") or DEFAULT_PHONE_LOGIN_SESSION_EXPIRY
	session_expiry = str(session_expiry).strip()

	if len(session_expiry.split(":")) == 2:
		session_expiry = f"{session_expiry}:00"

	try:
		get_expiry_in_seconds(session_expiry)
	except Exception:
		return DEFAULT_PHONE_LOGIN_SESSION_EXPIRY

	return session_expiry


def _ensure_global_session_expiry(session_expiry):
	current_expiry = frappe.defaults.get_global_default("session_expiry")
	try:
		if current_expiry and get_expiry_in_seconds(current_expiry) >= get_expiry_in_seconds(session_expiry):
			return
	except Exception:
		pass

	frappe.defaults.set_global_default("session_expiry", session_expiry)


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


def _get_website_login_token_key(login_token):
	return frappe.cache.make_key(f"website-login-token:{OTP_RATE_LIMIT_CACHE_VERSION}:{login_token}")


def _get_phone_auth_flow_token_key(flow_token):
	return frappe.cache.make_key(f"phone-auth-flow:{OTP_RATE_LIMIT_CACHE_VERSION}:{flow_token}")


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
		frappe.cache.delete_value(_get_phone_profile_token_key(profile_token), make_keys=False)


def _create_phone_auth_flow_token(phone_number, mode, user_name=None):
	flow_token = frappe.generate_hash(length=32)
	frappe.cache.setex(
		_get_phone_auth_flow_token_key(flow_token),
		PHONE_AUTH_FLOW_TOKEN_TTL_SECONDS,
		json.dumps(
			{
				"phone_number": phone_number,
				"mode": mode,
				"user_name": user_name,
			}
		),
	)
	return flow_token


def _read_phone_auth_flow_token(flow_token, phone_number, allowed_modes=("sign_in", "sign_up")):
	flow_token = (flow_token or "").strip()
	if not flow_token:
		frappe.throw(_("Missing phone auth flow token."), frappe.AuthenticationError)

	payload = frappe.cache.get(_get_phone_auth_flow_token_key(flow_token))
	if isinstance(payload, bytes):
		payload = payload.decode()

	try:
		payload = json.loads(payload or "{}")
	except Exception:
		payload = {}

	if payload.get("phone_number") != phone_number:
		frappe.throw(_("Phone verification session does not match this number."), frappe.AuthenticationError)

	if payload.get("mode") not in allowed_modes:
		frappe.throw(_("Phone verification session expired. Please try again."), frappe.AuthenticationError)

	return payload


def _create_website_login_token(user_name):
	user_name = _normalize_login_user_name(user_name)
	login_token = frappe.generate_hash(length=32)
	frappe.cache.setex(
		_get_website_login_token_key(login_token),
		WEBSITE_LOGIN_TOKEN_TTL_SECONDS,
		user_name,
	)
	return login_token


def _read_website_login_token(login_token):
	login_token = (login_token or "").strip()
	if not login_token:
		frappe.throw(_("Missing login token."), frappe.AuthenticationError)

	user_name = frappe.cache.get(_get_website_login_token_key(login_token))
	if isinstance(user_name, bytes):
		user_name = user_name.decode()

	return _normalize_login_user_name(user_name)


def _get_login_response_payload(user):
	return {
		"success": True,
		**_get_phone_user_payload(user, False),
		"session_token": _create_website_login_token(user.name),
		"message": _("Logged in successfully."),
	}


def _format_twilio_error(exc):
	error_code = f" Twilio error code: {exc.code}." if exc.code else ""

	if exc.code == 20003 or exc.status in {401, 403}:
		return _(
			"Twilio rejected the OTP request. Check the Account SID, Auth Token, Verify service, "
			"SMS geo permissions, and trial account recipient verification."
		) + error_code

	if exc.status == 429:
		return _("Too many OTP requests were sent to this phone number. Please wait a few minutes and try again.")

	return _("Unable to send OTP. Please try again.") + error_code


def _get_twilio_error_status(exc):
	if exc.status == 429:
		return 429

	if exc.code == 20003 or exc.status in {401, 403}:
		return 503

	return exc.status or 400


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
	user = _get_existing_user_by_phone(phone_number)
	if user and user.user_type == "Website User":
		if not user.enabled:
			frappe.throw(_("User disabled or missing"), frappe.AuthenticationError)
		return user

	return None


def _get_existing_user_by_phone(phone_number):
	user_name = frappe.db.get_value("User", {"mobile_no": phone_number}, "name")
	if not user_name:
		user_name = frappe.db.get_value("User", {"phone": phone_number}, "name")

	if not user_name:
		return None

	return frappe.get_doc("User", user_name)


def _build_phone_login_email(phone_number):
	phone_digits = re.sub(r"\D", "", phone_number or "")
	if not phone_digits:
		phone_digits = frappe.generate_hash(length=12).lower()

	return f"{phone_digits}@{PHONE_USER_EMAIL_DOMAIN}"


def _get_available_phone_login_email(phone_number):
	phone_digits = re.sub(r"\D", "", phone_number or "")
	base_local_part = phone_digits or frappe.generate_hash(length=12).lower()
	candidate = f"{base_local_part}@{PHONE_USER_EMAIL_DOMAIN}"
	if not frappe.db.exists("User", candidate):
		return candidate

	suffix = 2
	while True:
		candidate = f"{base_local_part}-{suffix}@{PHONE_USER_EMAIL_DOMAIN}"
		if not frappe.db.exists("User", candidate):
			return candidate
		suffix += 1


def _create_phone_website_user(phone_number):
	existing_user = _get_existing_user_by_phone(phone_number)
	if existing_user:
		if existing_user.user_type != "Website User":
			frappe.throw(_("This phone number is already linked to a non-website user account."))

		if not existing_user.enabled:
			frappe.throw(_("User disabled or missing"), frappe.AuthenticationError)

		return existing_user

	email = _get_available_phone_login_email(phone_number)

	user = frappe.get_doc(
		{
			"doctype": "User",
			"email": email,
			"first_name": _("Customer"),
			"last_name": "",
			"full_name": _("Customer"),
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


def _get_phone_login_lookup(phone_number):
	existing_user = _get_existing_user_by_phone(phone_number)
	if not existing_user:
		return {
			"user": None,
			"website_user": None,
			"user_exists": False,
			"website_user_exists": False,
		}

	if not existing_user.enabled:
		frappe.throw(_("User disabled or missing"), frappe.AuthenticationError)

	website_user = existing_user if existing_user.user_type == "Website User" else None
	return {
		"user": existing_user,
		"website_user": website_user,
		"user_exists": True,
		"website_user_exists": bool(website_user),
	}


def _create_profile_website_user(full_name, email, phone_number):
	if frappe.db.exists("User", email):
		# Linking needs proof the email is theirs, which only Google gives.
		frappe.throw(
			_("This email is already registered. Use Fill with Google to link it to this number, or enter a different email.")
		)

	existing_user = _get_existing_user_by_phone(phone_number)
	if existing_user:
		if existing_user.user_type == "Website User":
			frappe.throw(_("A user with this phone number already exists. Please sign in again."))

		frappe.throw(_("This phone number is already linked to a non-website user account."))

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
			"user_image": user.user_image,
		},
	}


def _normalize_login_user_name(user_name):
	user_name = str(user_name or "").strip()
	if not user_name or user_name.lower() in {"guest", "none", "null"}:
		frappe.throw(_("Unable to restore your session. Please sign in again."), frappe.AuthenticationError)

	return user_name


def _is_guest_session_user():
	user_name = str(getattr(frappe.session, "user", "") or "").strip()
	return not user_name or user_name.lower() in {"guest", "none", "null"}


def _login_user(user_name):
	user_name = _normalize_login_user_name(user_name)
	session_expiry = _get_phone_login_session_expiry()
	_ensure_global_session_expiry(session_expiry)

	frappe.local.login_manager = LoginManager()
	frappe.local.login_manager.login_as(user_name)

	frappe.local.session_obj.data.data.session_expiry = session_expiry
	frappe.local.session_obj.update(force=True)
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


@frappe.whitelist(allow_guest=True, methods=["GET"])
def get_current_user():
	if _is_guest_session_user():
		return {
			"is_authenticated": False,
			"user": None,
		}

	user = frappe.get_doc("User", frappe.session.user)
	return {
		"is_authenticated": True,
		"user": {
			"name": user.name,
			"email": user.email,
			"mobile_no": user.mobile_no,
			"full_name": user.full_name,
			"user_type": user.user_type,
			"user_image": user.user_image,
		},
	}


@frappe.whitelist(allow_guest=True, methods=["GET", "POST"])
def request_phone_otp(phone_number=None, phoneNumber=None):
	phone_number = _normalize_phone(phone_number or phoneNumber)
	lookup = _get_phone_login_lookup(phone_number)
	if lookup["user"] and not lookup["website_user"]:
		return _error(_("This phone number is already linked to a non-website user account."))
	mode = "sign_in" if lookup["website_user"] else "sign_up"
	flow_token = _create_phone_auth_flow_token(
		phone_number,
		mode,
		lookup["website_user"].name if lookup["website_user"] else None,
	)

	cooldown_response = _check_otp_request_cooldown(phone_number)
	if cooldown_response:
		return cooldown_response

	rate_limit_response = _check_otp_rate_limit("request_phone_otp", phone_number, _get_otp_request_limit())
	if rate_limit_response:
		return rate_limit_response

	if _is_test_otp_enabled(phone_number):
		_set_otp_request_cooldown(phone_number)
		response = {
			"success": True,
			"status": "test",
			"auth_flow_token": flow_token,
			"auth_mode": mode,
			"user_exists": lookup["user_exists"],
			"website_user_exists": lookup["website_user_exists"],
			"message": _("Test OTP enabled. Use the configured OTP to continue."),
		}
		_log_phone_auth_response(
			"request_phone_otp",
			phone_number,
			{
				"success": response["success"],
				"status": response["status"],
				"auth_mode": response["auth_mode"],
				"user_exists": response["user_exists"],
				"website_user_exists": response["website_user_exists"],
			},
		)
		return response

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
		return _error(_format_twilio_error(exc), _get_twilio_error_status(exc))

	_set_otp_request_cooldown(phone_number)

	response = {
		"success": True,
		"status": verification.status,
		"auth_flow_token": flow_token,
		"auth_mode": mode,
		"user_exists": lookup["user_exists"],
		"website_user_exists": lookup["website_user_exists"],
		"message": _("OTP sent successfully."),
	}
	_log_phone_auth_response(
		"request_phone_otp",
		phone_number,
		{
			"success": response["success"],
			"status": response["status"],
			"auth_mode": response["auth_mode"],
			"user_exists": response["user_exists"],
			"website_user_exists": response["website_user_exists"],
		},
	)
	return response


@frappe.whitelist(allow_guest=True, methods=["POST"])
def verify_phone_otp(phone_number=None, otp=None, phoneNumber=None, auth_flow_token=None):
	phone_number = _normalize_phone(phone_number or phoneNumber)
	rate_limit_response = _check_otp_rate_limit("verify_phone_otp", phone_number, _get_otp_verify_limit())
	if rate_limit_response:
		return rate_limit_response

	otp = (otp or "").strip()
	auth_flow = _read_phone_auth_flow_token(auth_flow_token, phone_number)

	if not OTP_PATTERN.match(otp):
		return _error(_("Enter a valid OTP."))

	test_otp = _get_test_otp()
	if _is_test_otp_enabled(phone_number):
		if otp != test_otp:
			return _error(_("Invalid OTP."), 400)

		if auth_flow["mode"] == "sign_in":
			user = frappe.get_doc("User", auth_flow["user_name"])
			_login_user(user.name)
			response = {
				**_get_login_response_payload(user),
				**_get_phone_user_payload(user, False),
			}
		else:
			response = {
				"success": True,
				"auth_mode": "sign_up",
				"profile_token": _create_phone_profile_token(phone_number),
				"phone_number": phone_number,
				"website_user_created": False,
				"website_user_exists": False,
				"needs_profile": True,
				"profile_completed": False,
				"message": _("OTP verified. Complete your profile to create your account."),
			}

		_log_phone_auth_response(
			"verify_phone_otp",
			phone_number,
			{
				"success": response["success"],
				"auth_mode": auth_flow["mode"],
				"is_new_user": response.get("is_new_user"),
				"website_user_exists": response["website_user_exists"],
				"profile_completed": response["profile_completed"],
				"user_name": response.get("user", {}).get("name"),
			},
		)
		return response

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
		return _error(_("Unable to verify OTP. Please try again."), _get_twilio_error_status(exc))

	if check.status != "approved":
		return _error(_("Invalid OTP."), 400)

	if auth_flow["mode"] == "sign_in":
		user = frappe.get_doc("User", auth_flow["user_name"])
		_login_user(user.name)
		response = {
			**_get_login_response_payload(user),
			**_get_phone_user_payload(user, False),
		}
	else:
		response = {
			"success": True,
			"auth_mode": "sign_up",
			"profile_token": _create_phone_profile_token(phone_number),
			"phone_number": phone_number,
			"website_user_created": False,
			"website_user_exists": False,
			"needs_profile": True,
			"profile_completed": False,
			"message": _("OTP verified. Complete your profile to create your account."),
		}

	_log_phone_auth_response(
		"verify_phone_otp",
		phone_number,
		{
			"success": response["success"],
			"auth_mode": auth_flow["mode"],
			"is_new_user": response.get("is_new_user"),
			"website_user_exists": response["website_user_exists"],
			"profile_completed": response["profile_completed"],
			"user_name": response.get("user", {}).get("name"),
		},
	)
	return response


@frappe.whitelist(allow_guest=True, methods=["POST"])
def complete_phone_profile(full_name=None, email=None, phone_number=None, phoneNumber=None, profile_token=None):
	phone_number = _normalize_phone(phone_number or phoneNumber)
	full_name = (full_name or "").strip()
	email = validate_email_address(email, throw=True)
	profile_token = (profile_token or "").strip()

	if not full_name:
		frappe.throw(_("Full name is required."))

	if profile_token:
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
				"user_image": user.user_image,
			},
			"session_token": _create_website_login_token(user.name),
			"message": _("Profile completed successfully."),
		}

	if _is_guest_session_user():
		frappe.throw(_("Please verify the OTP before completing your profile."), frappe.AuthenticationError)

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
			"user_image": user.user_image,
		},
		"session_token": _create_website_login_token(user.name),
		"message": _("Profile completed successfully."),
	}


def _get_google_oauth_client_ids():
	return _get_conf_list("google_oauth_client_ids") or DEFAULT_GOOGLE_OAUTH_CLIENT_IDS


def _verify_google_id_token(id_token):
	"""Validates a Google ID token with Google and returns its claims.

	Google's tokeninfo endpoint checks the signature and expiry; the audience,
	issuer and verified-email checks are ours."""
	id_token = (id_token or "").strip()
	if not id_token:
		frappe.throw(_("Missing Google ID token."), frappe.AuthenticationError)

	try:
		response = requests.get(GOOGLE_TOKENINFO_URL, params={"id_token": id_token}, timeout=10)
	except requests.RequestException:
		frappe.log_error(title="Google Token Verification Failed", message=frappe.get_traceback())
		frappe.throw(_("Unable to verify Google sign-in. Please try again."))

	if response.status_code != 200:
		frappe.throw(_("Invalid Google sign-in. Please try again."), frappe.AuthenticationError)

	claims = response.json()
	if claims.get("aud") not in _get_google_oauth_client_ids():
		frappe.throw(_("Invalid Google sign-in. Please try again."), frappe.AuthenticationError)

	if claims.get("iss") not in GOOGLE_TOKEN_ISSUERS:
		frappe.throw(_("Invalid Google sign-in. Please try again."), frappe.AuthenticationError)

	if str(claims.get("email_verified")).lower() != "true" or not claims.get("email"):
		frappe.throw(_("Your Google account email is not verified."), frappe.AuthenticationError)

	return claims


def _verify_google_access_token(access_token):
	"""Validates an OAuth access token from the web's token popup and returns
	the account's email and name.

	The audience check matters: it proves the token was issued to our client,
	not to some other app the user signed in to."""
	access_token = (access_token or "").strip()
	try:
		token_info = requests.get(GOOGLE_TOKENINFO_URL, params={"access_token": access_token}, timeout=10)
		user_info = (
			requests.get(GOOGLE_USERINFO_URL, headers={"Authorization": f"Bearer {access_token}"}, timeout=10)
			if token_info.status_code == 200
			else None
		)
	except requests.RequestException:
		frappe.log_error(title="Google Token Verification Failed", message=frappe.get_traceback())
		frappe.throw(_("Unable to verify Google sign-in. Please try again."))

	if token_info.status_code != 200 or user_info is None or user_info.status_code != 200:
		frappe.throw(_("Invalid Google sign-in. Please try again."), frappe.AuthenticationError)

	token_info = token_info.json()
	if token_info.get("aud") not in _get_google_oauth_client_ids():
		frappe.throw(_("Invalid Google sign-in. Please try again."), frappe.AuthenticationError)

	claims = user_info.json()
	if (
		not claims.get("email")
		or claims.get("email") != token_info.get("email")
		or str(claims.get("email_verified")).lower() != "true"
	):
		frappe.throw(_("Your Google account email is not verified."), frappe.AuthenticationError)

	return claims


def _verify_google_credential(id_token=None, access_token=None):
	# The mobile app sends ID tokens; the web's custom button sends access tokens.
	if (access_token or "").strip():
		return _verify_google_access_token(access_token)

	return _verify_google_id_token(id_token)


def _create_google_website_user(email, full_name):
	first_name, last_name = _split_full_name(full_name or email.split("@")[0])
	user = frappe.get_doc(
		{
			"doctype": "User",
			"email": email,
			"first_name": first_name,
			"last_name": last_name,
			"enabled": 1,
			"user_type": "Website User",
			"send_welcome_email": 0,
		}
	)

	if frappe.db.exists("Role", "Customer"):
		user.append("roles", {"role": "Customer"})

	user.insert(ignore_permissions=True)
	frappe.db.commit()
	return user


@frappe.whitelist(allow_guest=True, methods=["POST"])
def google_login(id_token=None, access_token=None):
	claims = _verify_google_credential(id_token, access_token)
	email = validate_email_address(claims["email"].strip().lower(), throw=True)

	user_name = frappe.db.get_value("User", {"email": email}, "name")
	is_new_user = not user_name
	if is_new_user:
		user = _create_google_website_user(email, claims.get("name"))
	else:
		user = frappe.get_doc("User", user_name)
		# Google sign-in is for customers only; staff accounts keep their
		# own login so a Google account can't open the desk.
		if user.user_type != "Website User":
			return _error(_("This email belongs to a staff account. Please sign in with your password."), 403)

		if not user.enabled:
			return _error(_("This account is disabled."), 403)

	_login_user(user.name)
	response = {
		**_get_login_response_payload(user),
		"is_new_user": is_new_user,
		"website_user_created": is_new_user,
		"website_user_exists": not is_new_user,
		"needs_phone": not user.mobile_no,
	}

	frappe.logger("buy_in_minutes.auth").info(
		f"google_login response for {email}: "
		f"{frappe.as_json({'is_new_user': is_new_user, 'user_name': user.name}, indent=None)}"
	)
	return response


@frappe.whitelist(allow_guest=True, methods=["POST"])
def restore_login_session(session_token=None):
	user_name = _read_website_login_token(session_token)

	if not frappe.db.exists("User", user_name):
		frappe.throw(_("Login user was not found."), frappe.AuthenticationError)

	if frappe.db.get_value("User", user_name, "enabled") != 1:
		frappe.throw(_("Login user is disabled."), frappe.AuthenticationError)

	_login_user(user_name)
	# A fresh token is issued below; retire this one so only one stays valid.
	revoke_login_session(session_token)
	user = frappe.get_doc("User", user_name)
	return {
		"success": True,
		"user": {
			"name": user.name,
			"email": user.email,
			"mobile_no": user.mobile_no,
			"full_name": user.full_name,
			"user_type": user.user_type,
			"user_image": user.user_image,
		},
		"session_token": _create_website_login_token(user.name),
		"message": _("Logged in successfully."),
	}


def _get_session_website_user():
	if _is_guest_session_user():
		frappe.throw(_("Please sign in first."), frappe.AuthenticationError)

	user = frappe.get_doc("User", frappe.session.user)
	if user.user_type != "Website User":
		frappe.throw(_("Only website users can add a phone number."), frappe.PermissionError)

	return user


@frappe.whitelist(methods=["POST"])
def request_link_phone_otp(phone_number=None, phoneNumber=None):
	"""Sends an OTP to attach a phone number to the signed-in account, e.g.
	after a Google sign-in, instead of signing in or up by phone."""
	user = _get_session_website_user()
	phone_number = _normalize_phone(phone_number or phoneNumber)

	existing_user = _get_existing_user_by_phone(phone_number)
	if existing_user and existing_user.name != user.name:
		return _error(_("This phone number is already linked to another account."), 409)

	cooldown_response = _check_otp_request_cooldown(phone_number)
	if cooldown_response:
		return cooldown_response

	rate_limit_response = _check_otp_rate_limit("request_phone_otp", phone_number, _get_otp_request_limit())
	if rate_limit_response:
		return rate_limit_response

	if _is_test_otp_enabled(phone_number):
		status = "test"
	else:
		client, service_sid = _get_twilio_client()
		try:
			status = client.verify.v2.services(service_sid).verifications.create(
				to=phone_number,
				channel="sms",
			).status
		except TwilioRestException as exc:
			frappe.log_error(
				title="Twilio OTP Request Failed",
				message=f"Twilio error {exc.code}: {exc.msg}",
			)
			return _error(_format_twilio_error(exc), _get_twilio_error_status(exc))

	_set_otp_request_cooldown(phone_number)
	response = {
		"success": True,
		"status": status,
		"auth_flow_token": _create_phone_auth_flow_token(phone_number, "link_phone", user.name),
		"auth_mode": "link_phone",
		"message": _("OTP sent successfully."),
	}
	_log_phone_auth_response(
		"request_link_phone_otp",
		phone_number,
		{"success": True, "status": status, "user_name": user.name},
	)
	return response


@frappe.whitelist(methods=["POST"])
def verify_link_phone_otp(phone_number=None, otp=None, phoneNumber=None, auth_flow_token=None):
	user = _get_session_website_user()
	phone_number = _normalize_phone(phone_number or phoneNumber)
	rate_limit_response = _check_otp_rate_limit("verify_phone_otp", phone_number, _get_otp_verify_limit())
	if rate_limit_response:
		return rate_limit_response

	otp = (otp or "").strip()
	auth_flow = _read_phone_auth_flow_token(auth_flow_token, phone_number, allowed_modes=("link_phone",))
	if auth_flow.get("user_name") != user.name:
		frappe.throw(_("Phone verification session does not match this account."), frappe.AuthenticationError)

	if not OTP_PATTERN.match(otp):
		return _error(_("Enter a valid OTP."))

	if _is_test_otp_enabled(phone_number):
		if otp != _get_test_otp():
			return _error(_("Invalid OTP."), 400)
	else:
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
			return _error(_("Unable to verify OTP. Please try again."), _get_twilio_error_status(exc))

		if check.status != "approved":
			return _error(_("Invalid OTP."), 400)

	# Re-check: the number may have been claimed while the OTP was pending.
	existing_user = _get_existing_user_by_phone(phone_number)
	if existing_user and existing_user.name != user.name:
		return _error(_("This phone number is already linked to another account."), 409)

	user.mobile_no = phone_number
	user.phone = phone_number
	user.save(ignore_permissions=True)
	frappe.db.commit()
	frappe.cache.delete_value(_get_phone_auth_flow_token_key(auth_flow_token.strip()), make_keys=False)

	_log_phone_auth_response("verify_link_phone_otp", phone_number, {"success": True, "user_name": user.name})
	return {
		**_get_login_response_payload(user),
		"message": _("Phone number verified."),
	}


@frappe.whitelist(allow_guest=True, methods=["POST"])
def complete_phone_profile_with_google(
	id_token=None, phone_number=None, phoneNumber=None, profile_token=None, access_token=None, full_name=None
):
	"""Completes a phone sign-up with the name and email from a Google account.

	If that Google account already has a customer account (signed up with
	Google earlier), the verified phone is attached to it instead."""
	phone_number = _normalize_phone(phone_number or phoneNumber)
	claims = _verify_google_credential(id_token, access_token)
	email = validate_email_address(claims["email"].strip().lower(), throw=True)
	# The email must come from Google; the name may have been edited on the form.
	full_name = (full_name or "").strip() or (claims.get("name") or "").strip() or email.split("@")[0]

	google_user_name = frappe.db.get_value("User", {"email": email}, "name")
	profile_token = (profile_token or "").strip()
	if not google_user_name or not profile_token:
		# New email, or an already signed-in phone user: same as the manual form.
		return complete_phone_profile(
			full_name=full_name,
			email=email,
			phone_number=phone_number,
			profile_token=profile_token,
		)

	profile_token = _validate_phone_profile_token(profile_token, phone_number)
	user = frappe.get_doc("User", google_user_name)
	if user.user_type != "Website User":
		return _error(_("This email belongs to a staff account. Please use a different Google account."), 403)

	if not user.enabled:
		return _error(_("This account is disabled."), 403)

	if user.mobile_no and _normalize_phone(user.mobile_no) != phone_number:
		return _error(_("This Google account is already linked to a different phone number."), 409)

	existing_phone_user = _get_existing_user_by_phone(phone_number)
	if existing_phone_user and existing_phone_user.name != user.name:
		return _error(_("This phone number is already linked to another account."), 409)

	user.mobile_no = phone_number
	user.phone = phone_number
	user.save(ignore_permissions=True)
	frappe.db.commit()
	_login_user(user.name)
	_clear_phone_profile_token(profile_token)

	return {
		**_get_login_response_payload(user),
		"message": _("Google account linked successfully."),
	}


@frappe.whitelist(allow_guest=True, methods=["POST"])
def revoke_login_session(session_token=None):
	"""Invalidates a restore-session token on logout so it can't sign anyone in
	again. Holding the token is what proves the right to revoke it."""
	session_token = (session_token or "").strip()
	if session_token:
		# Keys from the _get_*_key helpers are already prefixed.
		frappe.cache.delete_value(_get_website_login_token_key(session_token), make_keys=False)

	return {"success": True}
