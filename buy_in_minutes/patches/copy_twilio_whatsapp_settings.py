import frappe
from frappe.utils.password import get_decrypted_password, set_encrypted_password

SOURCE = "Twilio WhatsApp Settings"  # pos_app's DocType, when installed
TARGET = "BIM Twilio WhatsApp Settings"


def execute():
	"""Start BIM Twilio WhatsApp Settings from pos_app's Twilio WhatsApp Settings, if that app is on this site."""
	if not frappe.db.exists("DocType", SOURCE) or frappe.db.get_single_value(TARGET, "account_sid"):
		return
	source = frappe.db.get_singles_dict(SOURCE)
	if not source.get("account_sid"):
		return
	frappe.db.set_single_value(
		TARGET,
		{
			"enabled": source.get("enabled") or 0,
			"account_sid": (source.get("account_sid") or "").strip(),
			"from_whatsapp_number": (source.get("from_whatsapp_number") or "").strip(),
		},
	)
	auth_token = get_decrypted_password(SOURCE, SOURCE, "auth_token", raise_exception=False)
	if auth_token:
		set_encrypted_password(TARGET, TARGET, auth_token, "auth_token")
