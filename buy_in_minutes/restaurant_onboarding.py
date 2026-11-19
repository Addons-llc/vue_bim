"""Invite restaurants (Leads) on WhatsApp to join Buy In Minutes, and onboard them in the chat.

1. Send Invitation (Lead list or form) sends the approved invitation template with Yes / No buttons.
   Or the restaurant writes first: the join link (wa.me with the Join Keyword typed in) starts the
   onboarding without any invitation, so no Marketing template is paid for.
2. Twilio posts every reply on the WhatsApp number to whatsapp_webhook. Replies from a restaurant being
   onboarded move it through the steps below; any other message is passed on to the number's previous
   webhook unchanged, so other apps using the same number keep working.
3. Once the name, logo and location are in, a Supplier is created with them.

The sender and Twilio account come from Twilio WhatsApp Settings; the wording from BIM Restaurant Onboarding Settings.
"""

import json
import re
from html import escape
from urllib.parse import urlparse

import frappe
from frappe import _
from frappe.utils import cint, now_datetime
from werkzeug.wrappers import Response

TWILIO_SETTINGS = "Twilio WhatsApp Settings"
SETTINGS = "BIM Restaurant Onboarding Settings"
ONBOARDING = "BIM Restaurant Onboarding"

INVITED = "Invited"
CONFIRMING_NAME = "Confirming Name"
AWAITING_LOGO = "Awaiting Logo"
AWAITING_LOCATION = "Awaiting Location"
SELECTING_ITEMS = "Selecting Items"
COMPLETED = "Completed"
DECLINED = "Declined"
FAILED = "Failed"
# Onboardings still waiting for the restaurant's reply
OPEN_STATUSES = (INVITED, CONFIRMING_NAME, AWAITING_LOGO, AWAITING_LOCATION, SELECTING_ITEMS)

# Ids of the invitation template's buttons, sent back by Twilio as ButtonPayload
CONFIRM_PAYLOAD = "bim_onboarding:yes"
DECLINE_PAYLOAD = "bim_onboarding:no"
YES_WORDS = {"yes", "y", "yeah", "yep", "ok", "okay", "sure", "confirm", "confirmed", "correct", "yes please", "نعم"}
NO_WORDS = {"no", "n", "nope", "no thanks", "no, thanks", "not interested", "لا"}

# The Lead's number is taken from the first of these that is filled in
LEAD_NUMBER_FIELDS = ("phone", "mobile_no", "whatsapp_no")
# Up to this many Leads are invited while the user waits; more are invited in the background
SEND_NOW_LIMIT = 5
# WhatsApp's limit on quick reply button titles
BUTTON_TITLE_LIMIT = 20
LOGO_SIZE_LIMIT = 5 * 1024 * 1024
LOGO_EXTENSIONS = {"image/jpeg": "jpg", "image/png": "png", "image/webp": "webp"}

WEBHOOK_METHOD = "buy_in_minutes.restaurant_onboarding.whatsapp_webhook"
SENDERS_API_URL = "https://messaging.twilio.com/v2/Channels/Senders"
CONTENT_API_URL = "https://content.twilio.com/v1/Content"
PLACEHOLDER_PATTERN = re.compile(r"{{\s*(.+?)\s*}}")

# Address of a location pin, looked up from its coordinates
GEOCODE_API_URL = "https://maps.googleapis.com/maps/api/geocode/json"
# Google plus codes such as "79W6+CWV", which are not a readable address
PLUS_CODE_PATTERN = re.compile(r"^[23456789CFGHJMPQRVWX]{4,8}\+[23456789CFGHJMPQRVWX]*\b")
ADDRESS_BUILDING_TYPES = {"premise", "subpremise"}
ADDRESS_STREET_TYPES = {"street_address", "route"}
ADDRESS_AREA_TYPES = {"neighborhood", "sublocality", "sublocality_level_1", "locality"}

# The item list is a WhatsApp form (a Flow) with a tick box per item and Submit. WhatsApp shows at
# most 20 options of up to 30 characters. When the form can't be sent, a numbered list in the chat is
# sent instead, answered with the numbers, names or "all".
MAX_ITEM_OPTIONS = 20
ITEM_TITLE_LIMIT = 30
FLOW_TEXT_LIMIT = 30
# The form's option ids are this prefix and the item's number in the list
ITEM_OPTION_PREFIX = "bim_item_"
ITEM_OPTION_PATTERN = re.compile(rf"\b{ITEM_OPTION_PREFIX}(\d+)\b")
ALL_WORDS = {"all", "all of them", "everything", "all items", "الكل"}
SAMPLE_CONTEXT = {"lead_name": "Spice Garden", "first_name": "Ahmed", "company_name": "Spice Garden"}

# Shown on the website from these Supplier fields (api.SUPPLIER_DETAIL_FIELDS)
SUPPLIER_LOCATION_FIELDS = [
	{"fieldname": "custom_location_section", "fieldtype": "Section Break", "label": "Location", "insert_after": "supplier_details", "collapsible": 1},
	{"fieldname": "custom_google_address", "fieldtype": "Small Text", "label": "Address", "insert_after": "custom_location_section"},
	{"fieldname": "custom_location_column", "fieldtype": "Column Break", "insert_after": "custom_google_address"},
	{"fieldname": "custom_latitude", "fieldtype": "Float", "label": "Latitude", "precision": "9", "insert_after": "custom_location_column"},
	{"fieldname": "custom_longitude", "fieldtype": "Float", "label": "Longitude", "precision": "9", "insert_after": "custom_latitude"},
]


def setup_supplier_location_fields():
	"""after_migrate: the Supplier fields the onboarding fills with the restaurant's location."""
	from frappe.custom.doctype.custom_field.custom_field import create_custom_fields

	create_custom_fields({"Supplier": SUPPLIER_LOCATION_FIELDS}, update=True)


# ---------------------------------------------------------------------------
# Settings and Twilio
# ---------------------------------------------------------------------------


def get_settings():
	"""BIM Restaurant Onboarding Settings, with the default wording for anything left blank or never saved."""
	settings = frappe.get_single(SETTINGS)
	saved = frappe.db.get_singles_dict(SETTINGS)
	for field in settings.meta.fields:
		if not field.default:
			continue
		# A checkbox that was never saved reads as 0, not its default
		blank = settings.get(field.fieldname) in (None, "") and field.fieldtype != "Check"
		if field.fieldname not in saved or blank:
			settings.set(field.fieldname, cint(field.default) if field.fieldtype == "Check" else field.default)
	return settings


def get_twilio() -> frappe._dict:
	twilio = frappe.get_single(TWILIO_SETTINGS)
	account_sid = (twilio.account_sid or "").strip()
	auth_token = twilio.get_password("auth_token", raise_exception=False) or ""
	from_number = to_whatsapp_address(twilio.from_whatsapp_number)
	if not twilio.enabled:
		frappe.throw(_("Turn on Twilio WhatsApp Settings to send WhatsApp messages."))
	if not account_sid.startswith("AC") or not auth_token or not from_number:
		frappe.throw(_("Please set the Account SID (starts with AC), Auth Token and From WhatsApp Number in Twilio WhatsApp Settings."))
	return frappe._dict(account_sid=account_sid, auth_token=auth_token, from_number=from_number)


def twilio_request(twilio, method: str, url: str, json: dict | None = None) -> dict:
	import requests

	response = requests.request(method, url, json=json, auth=(twilio.account_sid, twilio.auth_token), timeout=30)
	if not response.ok:
		frappe.throw(_("Twilio error {0}: {1}").format(response.status_code, escape(response.text[:500])))
	return response.json() if response.content else {}


def get_twilio_client(twilio):
	from twilio.rest import Client

	return Client(twilio.account_sid, twilio.auth_token)


# ---------------------------------------------------------------------------
# 1. Invitation
# ---------------------------------------------------------------------------


@frappe.whitelist(methods=["POST"])
def send_invitations(leads):
	leads = frappe.parse_json(leads) if isinstance(leads, str) else leads
	# The same Lead selected twice is invited once
	leads = list(dict.fromkeys(leads or []))
	if not leads:
		frappe.throw(_("Select the Leads to invite on WhatsApp."))
	for lead in leads:
		frappe.has_permission("Lead", "write", lead, throw=True)

	# Stop here, not in the background job, when something is not set up
	check_invitation_settings(get_settings())
	get_twilio()
	if len(leads) <= SEND_NOW_LIMIT:
		return {"queued": False, **invite_leads(leads)}

	frappe.enqueue(
		"buy_in_minutes.restaurant_onboarding.invite_leads",
		queue="long",
		timeout=3600,
		enqueue_after_commit=True,
		leads=leads,
		commit=True,
	)
	return {"queued": True, "count": len(leads)}


def invite_new_lead(doc, method=None):
	"""Lead after_insert: invite the new Lead on WhatsApp, once the invitation template is approved."""
	# Not for Leads added in bulk by Data Import, patches or installs
	if frappe.flags.in_import or frappe.flags.in_patch or frappe.flags.in_install or frappe.flags.in_migrate:
		return
	settings = get_settings()
	if not settings.enabled or not cint(settings.invite_new_leads) or not settings.invitation_content_sid:
		return
	if not get_lead_whatsapp_number(doc, settings.default_country_code):
		return
	# After commit, so the Lead is saved even if WhatsApp fails, and saving it never waits for Twilio
	frappe.enqueue(
		"buy_in_minutes.restaurant_onboarding.invite_leads_if_approved",
		queue="short",
		enqueue_after_commit=True,
		leads=[doc.name],
	)


@frappe.whitelist(methods=["POST"])
def invite_existing_leads():
	"""Invite every Lead with a number that has never been invited, e.g. Leads from before auto-invite or a Data Import."""
	frappe.only_for("System Manager")
	settings = get_settings()
	check_invitation_settings(settings)
	if not is_invitation_approved():
		frappe.throw(_("The invitation template is not approved by WhatsApp yet."))
	invited = set(frappe.get_all(ONBOARDING, pluck="lead", distinct=True))
	leads = [
		lead.name
		for lead in frappe.get_all("Lead", fields=["name", *LEAD_NUMBER_FIELDS], order_by="creation")
		if lead.name not in invited and get_lead_whatsapp_number(lead, settings.default_country_code)
	]
	if leads:
		frappe.enqueue(
			"buy_in_minutes.restaurant_onboarding.invite_leads",
			queue="long",
			timeout=3600,
			enqueue_after_commit=True,
			leads=leads,
			commit=True,
		)
	return {"count": len(leads), "leads": leads[:20]}


def invite_leads_if_approved(leads: list[str]):
	if not is_invitation_approved():
		frappe.log_error(
			title="Restaurant invitation not sent",
			message=f"The invitation template is not approved yet, so these new Leads were not invited: {', '.join(leads)}",
		)
		return
	invite_leads(leads, commit=True)


def is_invitation_approved() -> bool:
	"""WhatsApp's approval of the invitation template; an approval is remembered for a day."""
	content_sid = frappe.db.get_single_value(SETTINGS, "invitation_content_sid")
	cache_key = f"buy_in_minutes:invitation_approved:{content_sid}"
	if frappe.cache.get_value(cache_key):
		return True
	approval = twilio_request(get_twilio(), "GET", f"{CONTENT_API_URL}/{content_sid}/ApprovalRequests")
	approved = (approval.get("whatsapp") or {}).get("status") == "approved"
	if approved:
		frappe.cache.set_value(cache_key, True, expires_in_sec=24 * 60 * 60)
	return approved


def check_invitation_settings(settings):
	if not settings.enabled:
		frappe.throw(_("Turn on BIM Restaurant Onboarding Settings to invite restaurants."))
	if not (settings.invitation_content_sid or "").startswith("HX") or not settings.invitation_message:
		frappe.throw(_("Create the invitation template in BIM Restaurant Onboarding Settings first (WhatsApp > Create Invitation Template)."))
	# Twilio fills a variable that is not sent with the template's sample value, e.g. "Spice Garden"
	expected = get_template_variable_count(settings.invitation_content_sid)
	found = len(get_placeholders(settings.invitation_message))
	if found != expected:
		frappe.throw(
			_(
				"The Invitation Message has {0} placeholders but the approved template has {1} variables. "
				"Write the message as approved, with placeholders like {{{{ lead_name }}}} (two braces on each side)."
			).format(found, expected)
		)


def get_template_variable_count(content_sid: str) -> int:
	cache_key = f"buy_in_minutes:invitation_variables:{content_sid}"
	count = frappe.cache.get_value(cache_key)
	if count is None:
		template = twilio_request(get_twilio(), "GET", f"{CONTENT_API_URL}/{content_sid}")
		count = len(template.get("variables") or {})
		frappe.cache.set_value(cache_key, count, expires_in_sec=24 * 60 * 60)
	return count


def invite_leads(leads: list[str], commit: bool = False) -> dict:
	settings = get_settings()
	check_invitation_settings(settings)
	twilio = get_twilio()
	client = get_twilio_client(twilio)
	counts = {"sent": 0, "no_number": 0, "already_invited": 0, "failed": 0}
	for name in leads:
		counts[invite_lead(client, twilio, frappe.get_doc("Lead", name), settings)] += 1
		# In the background job, so each invitation is kept even if a later one stops the job
		if commit:
			frappe.db.commit()
	return counts


def invite_lead(client, twilio, lead, settings) -> str:
	to_number = get_lead_whatsapp_number(lead, settings.default_country_code)
	if not to_number:
		lead.add_comment("Info", _("WhatsApp invitation not sent: the Lead has no Phone, Mobile No or WhatsApp number."))
		return "no_number"
	# Replies are matched to the onboarding by number, so a number has one open onboarding at a time
	if frappe.db.exists(ONBOARDING, {"status": ("in", OPEN_STATUSES), "whatsapp_number": to_number}):
		return "already_invited"

	context = get_lead_context(lead)
	doc = frappe.get_doc(
		{
			"doctype": ONBOARDING,
			"lead": lead.name,
			"proposed_name": lead.company_name or lead.lead_name or "",
			"whatsapp_number": to_number,
			"status": INVITED,
		}
	)
	message = frappe.render_template(settings.invitation_message, context)
	try:
		response = client.messages.create(
			from_=twilio.from_number,
			to=to_number,
			content_sid=settings.invitation_content_sid,
			content_variables=frappe.as_json(get_template_variables(settings.invitation_message, context)),
		)
	except Exception as e:
		frappe.log_error(title=f"Restaurant invitation failed: {lead.name}")
		doc.status = FAILED
		doc.error = str(getattr(e, "msg", None) or e)[:1000]
		add_message(doc, "Outgoing", message)
		doc.insert(ignore_permissions=True)
		return "failed"

	doc.invitation_sid = response.sid
	add_message(doc, "Outgoing", message, response.sid)
	doc.insert(ignore_permissions=True)
	lead.add_comment(
		"Info",
		_("Invited on WhatsApp to join Buy In Minutes: {0}").format(frappe.utils.get_link_to_form(ONBOARDING, doc.name)),
	)
	return "sent"


def get_lead_context(lead) -> dict:
	lead_name = lead.company_name or lead.lead_name or lead.first_name or lead.name
	return {
		"lead": lead.name,
		"lead_name": lead_name,
		"first_name": lead.first_name or lead.lead_name or lead_name,
		"company_name": lead.company_name or lead_name,
	}


def get_template_variables(message_template: str, context: dict) -> dict[str, str]:
	"""Each {{ placeholder }} of the message, in order, as Twilio's numbered content variables."""
	return {
		str(index): frappe.render_template(f"{{{{ {expression} }}}}", context).strip()
		# WhatsApp rejects template messages with empty variables
		or "-"
		for index, expression in enumerate(get_placeholders(message_template), start=1)
	}


def get_placeholders(message_template: str) -> list[str]:
	return list(dict.fromkeys(PLACEHOLDER_PATTERN.findall(message_template or "")))


def get_lead_whatsapp_number(lead, country_code: str | None) -> str:
	for fieldname in LEAD_NUMBER_FIELDS:
		number = "".join(ch for ch in str(lead.get(fieldname) or "") if ch.isdigit() or ch == "+")
		if not number:
			continue
		if number.startswith("00"):
			number = "+" + number[2:]
		elif number.startswith("0") and country_code:
			number = "+" + country_code.strip().lstrip("+") + number[1:]
		return to_whatsapp_address(number)
	return ""


def to_whatsapp_address(number: str | None) -> str:
	number = "".join(ch for ch in str(number or "").removeprefix("whatsapp:") if ch.isdigit() or ch == "+")
	if not number:
		return ""
	return "whatsapp:" + (number if number.startswith("+") else "+" + number)


def add_message(doc, direction: str, message: str, twilio_sid: str | None = None):
	doc.append(
		"messages",
		{"direction": direction, "message": message, "twilio_sid": twilio_sid, "sent_at": now_datetime()},
	)


# ---------------------------------------------------------------------------
# 2. Replies
# ---------------------------------------------------------------------------


@frappe.whitelist(allow_guest=True, methods=["POST"])
def whatsapp_webhook():
	params = frappe.request.form
	settings = get_settings()
	twilio = get_twilio()
	signature = frappe.get_request_header("X-Twilio-Signature") or ""
	from twilio.request_validator import RequestValidator

	# Checked against the public address given to Twilio; behind ngrok the request's own URL differs
	if not settings.webhook_url or not RequestValidator(twilio.auth_token).validate(settings.webhook_url, params, signature):
		frappe.throw(_("Invalid WhatsApp callback signature"), frappe.PermissionError)
	if params.get("AccountSid") != twilio.account_sid:
		frappe.throw(_("Unexpected WhatsApp callback account"), frappe.PermissionError)

	try:
		reply = handle_incoming(params, settings) if settings.enabled else None
	except Exception:
		# The message still reaches the previous webhook, so other apps on this number never miss it
		frappe.db.rollback()
		frappe.log_error(title="Restaurant onboarding reply failed")
		reply = None
	if reply is None:
		return pass_on(settings)
	return twiml(f"<Message>{escape(reply)}</Message>" if reply else "")


def pass_on(settings) -> Response:
	"""Hand a message that is not part of an onboarding to the number's previous webhook, unchanged."""
	previous = settings.previous_webhook_url
	if previous and previous != settings.webhook_url:
		return twiml(f'<Redirect method="POST">{escape(previous)}</Redirect>')
	return twiml("")


def twiml(body: str) -> Response:
	return Response(f'<?xml version="1.0" encoding="UTF-8"?><Response>{body}</Response>', mimetype="application/xml")


def handle_incoming(params, settings) -> str | None:
	"""The reply to send back, "" for none, or None when the message is not part of an onboarding."""
	from_number = to_whatsapp_address(params.get("From"))
	name = frappe.db.get_value(
		ONBOARDING,
		{"whatsapp_number": from_number, "status": ("in", OPEN_STATUSES)},
		"name",
		order_by="creation desc",
	)
	sid = params.get("MessageSid") or params.get("SmsMessageSid")
	if not name:
		return start_onboarding(params, settings, from_number, sid)

	doc = frappe.get_doc(ONBOARDING, name, for_update=True)
	# Twilio may send the same message again; it is answered once
	if sid and any(row.twilio_sid == sid for row in doc.messages):
		return ""

	add_message(doc, "Incoming", describe_incoming(params), sid)
	reply = next_step(doc, params, settings)
	if reply:
		add_message(doc, "Outgoing", reply)
	doc.save(ignore_permissions=True)
	if doc.status == COMPLETED and not doc.supplier:
		create_supplier(doc, settings)
	return reply


def start_onboarding(params, settings, from_number: str, sid: str | None) -> str | None:
	"""A restaurant that sent the join keyword itself (from the join link) is onboarded without an invitation.

	It wrote first, so every reply is a free-form message in WhatsApp's customer service window and no
	Marketing template is needed. Returns None when the message is not a join request.
	"""
	if not is_join_request(params.get("Body"), settings.join_keyword):
		return None

	completed = frappe.db.get_value(
		ONBOARDING, {"whatsapp_number": from_number, "status": COMPLETED}, "restaurant_name", order_by="creation desc"
	)
	if completed:
		# Joining twice would add the restaurant as a second Supplier
		return frappe.render_template(settings.already_joined_message or "", {"restaurant_name": completed}).strip()

	lead = find_lead(from_number, settings.default_country_code)
	proposed_name = (lead.company_name or lead.lead_name or "") if lead else ""
	doc = frappe.get_doc(
		{
			"doctype": ONBOARDING,
			"lead": lead.name if lead else None,
			"proposed_name": proposed_name,
			"whatsapp_number": from_number,
			# Writing the keyword is the restaurant's "yes", so the invitation step is skipped
			"status": CONFIRMING_NAME,
		}
	)
	add_message(doc, "Incoming", describe_incoming(params), sid)
	reply = render(settings.ask_name_message if proposed_name else settings.join_welcome_message, doc, settings)
	if reply:
		add_message(doc, "Outgoing", reply)
	doc.insert(ignore_permissions=True)
	if lead:
		lead.add_comment(
			"Info",
			_("Started joining Buy In Minutes on WhatsApp: {0}").format(frappe.utils.get_link_to_form(ONBOARDING, doc.name)),
		)
	return reply


def normalize_text(text: str | None) -> str:
	return " ".join(re.sub(r"[^\w\s]", " ", (text or "").lower()).split())


def is_join_request(body: str | None, keyword: str | None) -> bool:
	"""Whether the message contains the join keyword, ignoring case and punctuation."""
	keyword = normalize_text(keyword)
	return bool(keyword) and f" {keyword} " in f" {normalize_text(body)} "


def find_lead(whatsapp_number: str, country_code: str | None):
	"""The newest Lead whose phone number is this WhatsApp number, or None."""
	meta = frappe.get_meta("Lead")
	fields = [field for field in LEAD_NUMBER_FIELDS if meta.has_field(field)]
	# Compared on the last 9 digits, as Lead numbers are stored with or without the country code
	digits = whatsapp_number.removeprefix("whatsapp:").lstrip("+")[-9:]
	if not fields or not digits:
		return None
	stripped = "REPLACE(REPLACE(REPLACE(REPLACE(`{0}`, ' ', ''), '-', ''), '(', ''), ')', '')"
	conditions = " or ".join(f"{stripped.format(field)} like %(pattern)s" for field in fields)
	names = frappe.db.sql_list(
		f"select name from `tabLead` where {conditions} order by creation desc limit 20", {"pattern": f"%{digits}"}
	)
	for name in names:
		lead = frappe.get_doc("Lead", name)
		if get_lead_whatsapp_number(lead, country_code) == whatsapp_number:
			return lead
	return None


def next_step(doc, params, settings) -> str:
	text = (params.get("Body") or "").strip()
	answer = get_yes_no(params, text)

	if doc.status == INVITED:
		if answer == "yes" or is_join_request(text, settings.join_keyword):
			doc.status = CONFIRMING_NAME
			return render(settings.ask_name_message if doc.proposed_name else settings.ask_new_name_message, doc, settings)
		if answer == "no":
			doc.status = DECLINED
			return render(settings.declined_message, doc, settings)
		return render(settings.invalid_choice_message, doc, settings)

	if doc.status == CONFIRMING_NAME:
		if answer == "yes" and doc.proposed_name:
			doc.restaurant_name = doc.proposed_name
		elif text and answer != "yes":
			doc.restaurant_name = text[:140]
		else:
			return render(settings.ask_name_message if doc.proposed_name else settings.ask_new_name_message, doc, settings)
		doc.status = AWAITING_LOGO
		return render(settings.ask_logo_message, doc, settings)

	if doc.status == AWAITING_LOGO:
		if not save_logo(doc, params):
			return render(settings.invalid_logo_message, doc, settings)
		doc.status = AWAITING_LOCATION
		return render(settings.ask_location_message, doc, settings)

	if doc.status == AWAITING_LOCATION:
		if not params.get("Latitude") or not params.get("Longitude"):
			return render(settings.invalid_location_message, doc, settings)
		doc.latitude = float(params.get("Latitude"))
		doc.longitude = float(params.get("Longitude"))
		# A dropped pin comes without an address, so it is looked up from the coordinates
		address = params.get("Address") or reverse_geocode(doc.latitude, doc.longitude, settings)
		doc.address = ", ".join(part for part in (params.get("Label"), address) if part)
		if get_item_options(doc, settings):
			doc.status = SELECTING_ITEMS
			return ask_for_items(doc, settings)
		doc.status = COMPLETED
		return render(settings.completed_message, doc, settings)

	if doc.status == SELECTING_ITEMS:
		submission = params.get("InteractiveData") or params.get("FlowData")
		items = get_submitted_items(doc, submission) if submission else get_selected_items(doc, text)
		if not items:
			# Nothing ticked or recognised: the same list is sent again
			return ask_for_items(doc, settings, invalid=True)
		doc.set("items", [{"item_code": item} for item in items])
		doc.status = COMPLETED
		# WhatsApp shows the submitted form only as "Response sent", so the choice is repeated in the chat
		return "\n\n".join(
			part
			for part in (selected_items_message(items, settings), render(settings.completed_message, doc, settings))
			if part
		)

	return ""


def selected_items_message(items: list[str], settings) -> str:
	"""The Items Selected Message with {{ items }} as a bulleted list of the chosen items' names."""
	names = get_item_names(items)
	listing = "\n".join(f"• {names.get(item) or item}" for item in items)
	return frappe.render_template(settings.items_selected_message or "", {"items": listing}).strip()


def get_yes_no(params, text: str) -> str | None:
	payload = params.get("ButtonPayload") or ""
	if payload == CONFIRM_PAYLOAD:
		return "yes"
	if payload == DECLINE_PAYLOAD:
		return "no"
	word = text.lower().strip(" .!*")
	if word in YES_WORDS:
		return "yes"
	if word in NO_WORDS:
		return "no"
	return None


def render(message: str, doc, settings) -> str:
	context = {
		"restaurant_name": doc.restaurant_name or doc.proposed_name or "",
		"confirm_button_text": settings.confirm_button_text,
		"decline_button_text": settings.decline_button_text,
	}
	return frappe.render_template(message or "", context).strip()


def describe_incoming(params) -> str:
	"""The message as shown in the onboarding's conversation."""
	parts = [(params.get("ButtonText") or params.get("Body") or "").strip()]
	if cint(params.get("NumMedia")):
		parts.append(_("[{0} attached]").format(params.get("MediaContentType0") or _("file")))
	if params.get("Latitude"):
		parts.append(_("[Location {0}, {1}]").format(params.get("Latitude"), params.get("Longitude")))
	submission = params.get("InteractiveData") or params.get("FlowData")
	if submission:
		parts.append(_("[Form submitted: {0}]").format(submission[:500]))
	return " ".join(part for part in parts if part) or _("[empty message]")


def get_item_list(settings) -> list[dict]:
	"""The items the restaurant can choose from, kept short enough to read as one chat message."""
	if not settings.items_item_group:
		return []
	return frappe.get_all(
		"Item",
		filters={"item_group": settings.items_item_group, "disabled": 0, "is_sales_item": 1, "has_variants": 0},
		fields=["name", "item_name"],
		order_by="item_name asc",
		limit=MAX_ITEM_OPTIONS,
	)


def get_item_options(doc, settings) -> dict[str, str]:
	"""Which Item each list number stands for. Numbered once per onboarding, so a list sent again keeps its numbers."""
	options = frappe.parse_json(doc.item_options or "{}") or {}
	if not options:
		options = {str(number): item.name for number, item in enumerate(get_item_list(settings), start=1)}
	elif not all(key.isdigit() for key in options):
		# Saved by an earlier version as form option ids ("bim_item_1"); the number is the id's end
		options = {key.removeprefix(ITEM_OPTION_PREFIX): item for key, item in options.items()}
	doc.item_options = json.dumps(options) if options else None
	return options


def ask_for_items(doc, settings, invalid: bool = False) -> str:
	"""Send the tick box form and reply nothing, or reply with the numbered list when the form can't be sent."""
	if settings.items_content_sid and send_item_form(doc, settings):
		return ""
	parts = [render(settings.invalid_items_message, doc, settings) if invalid else "", item_list_message(doc, settings)]
	return "\n\n".join(part for part in parts if part)


def send_item_form(doc, settings) -> bool:
	"""Send the WhatsApp form with a tick box per item and Submit; False when it failed."""
	options = get_item_options(doc, settings)
	names = get_item_names(list(options.values()))
	choices = [
		{"id": f"{ITEM_OPTION_PREFIX}{number}", "title": (names.get(item) or item)[:ITEM_TITLE_LIMIT]}
		for number, item in options.items()
	]
	twilio = get_twilio()
	try:
		response = get_twilio_client(twilio).messages.create(
			from_=twilio.from_number,
			to=doc.whatsapp_number,
			content_sid=settings.items_content_sid,
			# The whole option list is the template's one variable
			content_variables=json.dumps({"1": json.dumps(choices)}),
		)
	except Exception as e:
		frappe.log_error(title=f"Restaurant item form failed: {doc.name}")
		doc.error = _("The item form could not be sent, so the numbered list was sent: {0}").format(
			str(getattr(e, "msg", None) or e)[:800]
		)
		return False

	titles = ", ".join(choice["title"] for choice in choices)
	add_message(doc, "Outgoing", f"{settings.items_message}\n[{settings.items_button_text}: {titles}]", response.sid)
	return True


def item_list_message(doc, settings) -> str:
	"""The Items Message with a numbered list to answer in the chat, used when the form can't be sent."""
	options = get_item_options(doc, settings)
	names = get_item_names(list(options.values()))
	listing = "\n".join(f"{number}. {names.get(item) or item}" for number, item in options.items())
	hint = _("Reply with the numbers of the items, for example *1, 3*, or *all*.")
	return "\n\n".join(part for part in ((settings.items_message or "").strip(), listing, hint) if part)


def get_submitted_items(doc, submission: str) -> list[str]:
	"""The Items ticked in the form, in the order they were listed."""
	options = frappe.parse_json(doc.item_options or "{}") or {}
	# The ids are unique, so they are found in the submission whatever its JSON shape
	numbers = set(ITEM_OPTION_PATTERN.findall(submission or ""))
	return [item for number, item in options.items() if number in numbers]


def get_item_names(items: list[str]) -> dict[str, str]:
	return dict(frappe.get_all("Item", filters={"name": ("in", items)}, fields=["name", "item_name"], as_list=True))


def get_selected_items(doc, reply: str) -> list[str]:
	"""The Items picked in the reply, by number ("1, 3"), by name or with "all", in the order they were listed."""
	options = frappe.parse_json(doc.item_options or "{}") or {}
	text = normalize_text(reply)
	if text in ALL_WORDS:
		return list(options.values())
	numbers = set(re.findall(r"\d+", text))
	names = get_item_names(list(options.values()))
	return [
		item
		for number, item in options.items()
		if number in numbers or f" {normalize_text(names.get(item) or item)} " in f" {text} "
	]


def reverse_geocode(latitude: float, longitude: float, settings) -> str:
	"""The street address at the coordinates from Google's Geocoding API, or "" when it cannot be found."""
	import requests

	api_key = settings.get_password("google_maps_api_key", raise_exception=False)
	if not api_key:
		return ""
	try:
		response = requests.get(
			GEOCODE_API_URL,
			params={"latlng": f"{latitude},{longitude}", "key": api_key, "language": "en"},
			timeout=10,
		)
		data = response.json()
	except Exception:
		frappe.log_error(title="Restaurant location lookup failed")
		return ""
	if data.get("status") != "OK":
		if data.get("status") != "ZERO_RESULTS":
			frappe.log_error(
				title="Restaurant location lookup failed",
				message=f"{data.get('status')}: {data.get('error_message') or ''} ({latitude}, {longitude})",
			)
		return ""
	result = pick_address_result(data.get("results") or [])
	return result.get("formatted_address", "") if result else ""


def pick_address_result(results: list[dict]) -> dict | None:
	"""The most precise readable result: a building, then a street, then an area (as the website's address picker does)."""
	readable = [
		result
		for result in results
		if not PLUS_CODE_PATTERN.match(result.get("formatted_address") or "")
		and not {"plus_code", "parking"} & set(result.get("types") or [])
	]
	for wanted in (ADDRESS_BUILDING_TYPES, ADDRESS_STREET_TYPES, ADDRESS_AREA_TYPES):
		for result in readable:
			if wanted & set(result.get("types") or []):
				return result
	return readable[0] if readable else None


def save_logo(doc, params) -> bool:
	"""Download the image the restaurant sent from Twilio and attach it as the onboarding's logo."""
	content_type = (params.get("MediaContentType0") or "").split(";")[0].strip().lower()
	if not cint(params.get("NumMedia")) or content_type not in LOGO_EXTENSIONS:
		return False

	content = download_twilio_media(params.get("MediaUrl0"))
	if not content:
		return False
	file = frappe.get_doc(
		{
			"doctype": "File",
			"file_name": f"{frappe.scrub(doc.restaurant_name or doc.name)}-logo.{LOGO_EXTENSIONS[content_type]}",
			"attached_to_doctype": ONBOARDING,
			"attached_to_name": doc.name,
			"attached_to_field": "logo",
			# Shown on the website
			"is_private": 0,
			"content": content,
		}
	)
	file.insert(ignore_permissions=True)
	doc.logo = file.file_url
	return True


def download_twilio_media(url: str | None) -> bytes | None:
	import requests

	# Only Twilio's own media links get the account credentials
	if not url or urlparse(url).hostname not in ("api.twilio.com", "media.twiliocdn.com"):
		return None
	twilio = get_twilio()
	response = requests.get(url, auth=(twilio.account_sid, twilio.auth_token), timeout=30)
	if not response.ok or len(response.content) > LOGO_SIZE_LIMIT:
		frappe.log_error(title="Restaurant logo download failed", message=f"{response.status_code} {url}")
		return None
	return response.content


# ---------------------------------------------------------------------------
# 3. Supplier
# ---------------------------------------------------------------------------


def create_supplier(doc, settings):
	"""The restaurant as a Supplier with its name, logo and location; a failure leaves the onboarding Completed."""
	try:
		supplier = frappe.get_doc(
			{
				"doctype": "Supplier",
				"supplier_name": doc.restaurant_name,
				"supplier_type": "Company",
				"supplier_group": settings.supplier_group
				or frappe.db.get_single_value("Buying Settings", "supplier_group"),
				"image": doc.logo,
				"custom_google_address": doc.address,
				"custom_latitude": doc.latitude,
				"custom_longitude": doc.longitude,
				"supplier_details": (
					_("Joined on WhatsApp ({0}) from Lead {1}").format(doc.whatsapp_number.removeprefix("whatsapp:"), doc.lead)
					if doc.lead
					else _("Joined on WhatsApp ({0})").format(doc.whatsapp_number.removeprefix("whatsapp:"))
				),
			}
		)
		# Suppliers are named after the Supplier Name, which another supplier may already have
		name = supplier_unique_name(doc.restaurant_name)
		supplier.insert(ignore_permissions=True, set_name=name)
		add_supplier_contact(supplier, doc)
	except Exception:
		frappe.log_error(title=f"Supplier not created for {doc.name}")
		frappe.db.set_value(ONBOARDING, doc.name, "error", _("The Supplier could not be created; see Error Log."))
		return

	frappe.db.set_value(ONBOARDING, doc.name, {"supplier": supplier.name, "error": None})
	if not doc.lead:
		return
	frappe.get_doc("Lead", doc.lead).add_comment(
		"Info",
		_("Joined Buy In Minutes on WhatsApp as Supplier {0}").format(frappe.utils.get_link_to_form("Supplier", supplier.name)),
	)


def supplier_unique_name(supplier_name: str) -> str:
	name, count = supplier_name, 1
	while frappe.db.exists("Supplier", name):
		count += 1
		name = f"{supplier_name} - {count}"
	return name


def add_supplier_contact(supplier, doc):
	number = doc.whatsapp_number.removeprefix("whatsapp:")
	contact = frappe.get_doc(
		{
			"doctype": "Contact",
			"first_name": supplier.supplier_name,
			"phone_nos": [{"phone": number, "is_primary_mobile_no": 1}],
			"links": [{"link_doctype": "Supplier", "link_name": supplier.name}],
		}
	)
	contact.insert(ignore_permissions=True)
	frappe.db.set_value("Supplier", supplier.name, {"supplier_primary_contact": contact.name, "mobile_no": number})


# ---------------------------------------------------------------------------
# Setup buttons on BIM Restaurant Onboarding Settings
# ---------------------------------------------------------------------------


@frappe.whitelist(methods=["POST"])
def create_invitation_template():
	"""Create the invitation with its Yes / No buttons in Twilio, submit it for WhatsApp approval and save its SID."""
	frappe.only_for("System Manager")
	settings = get_settings()
	twilio = get_twilio()
	message = (settings.invitation_message or "").strip()
	buttons = [(settings.confirm_button_text or "").strip(), (settings.decline_button_text or "").strip()]
	if not message:
		frappe.throw(_("Please set the Invitation Message first."))
	if "{%" in message:
		frappe.throw(_("The Invitation Message can only use {{ placeholders }}."))
	if any(not title or len(title) > BUTTON_TITLE_LIMIT for title in buttons):
		frappe.throw(_("Button texts must be 1 to {0} characters.").format(BUTTON_TITLE_LIMIT))

	placeholders = get_placeholders(message)
	body = PLACEHOLDER_PATTERN.sub(lambda match: f"{{{{{placeholders.index(match.group(1)) + 1}}}}}", message)
	name = f"bim_restaurant_invite_{frappe.generate_hash(length=6)}"
	content = twilio_request(
		twilio,
		"POST",
		CONTENT_API_URL,
		{
			"friendly_name": name,
			"language": "en",
			"variables": get_template_variables(message, SAMPLE_CONTEXT),
			"types": {
				"twilio/quick-reply": {
					"body": body,
					"actions": [
						{"title": buttons[0], "id": CONFIRM_PAYLOAD},
						{"title": buttons[1], "id": DECLINE_PAYLOAD},
					],
				}
			},
		},
	)
	# A first message to a business that has not asked for it is Marketing for WhatsApp
	twilio_request(
		twilio,
		"POST",
		f"{CONTENT_API_URL}/{content['sid']}/ApprovalRequests/whatsapp",
		{"name": name, "category": "MARKETING"},
	)
	frappe.db.set_single_value(SETTINGS, "invitation_content_sid", content["sid"])
	return {"sid": content["sid"], "body": body}


@frappe.whitelist(methods=["POST"])
def create_items_template():
	"""Create the item form (a WhatsApp Flow with a tick box per item and Submit), submit it for approval and save its SID."""
	frappe.only_for("System Manager")
	settings = get_settings()
	twilio = get_twilio()
	message = (settings.items_message or "").strip()
	button = (settings.items_button_text or "").strip()
	title = (settings.items_page_title or "").strip()
	submit_text = (settings.items_continue_text or "").strip()
	if not message:
		frappe.throw(_("Please set the Items Message first."))
	if "{{" in message or "{%" in message:
		frappe.throw(_("The Items Message can't use placeholders."))
	if not button or len(button) > BUTTON_TITLE_LIMIT:
		frappe.throw(_("The Select Items Button must be 1 to {0} characters.").format(BUTTON_TITLE_LIMIT))
	if not title or len(title) > FLOW_TEXT_LIMIT or not submit_text or len(submit_text) > FLOW_TEXT_LIMIT:
		frappe.throw(_("The Form Title and Submit Button must be 1 to {0} characters.").format(FLOW_TEXT_LIMIT))
	# WhatsApp reviews the template with a sample list
	names = [item.item_name or item.name for item in get_item_list(settings)] or ["Samoosa"]
	sample = [
		{"id": f"{ITEM_OPTION_PREFIX}{number}", "title": name[:ITEM_TITLE_LIMIT]} for number, name in enumerate(names, start=1)
	]

	name = f"bim_restaurant_items_{frappe.generate_hash(length=6)}"
	content = twilio_request(
		twilio,
		"POST",
		CONTENT_API_URL,
		{
			"friendly_name": name,
			"language": "en",
			"variables": {"1": json.dumps(sample)},
			"types": {
				"twilio/flows": {
					"body": message,
					"button_text": button,
					"type": "OTHER",
					"pages": [
						{
							"id": "items",
							"next_page_id": None,
							"title": title,
							"layout": [
								# Twilio's reference says MULTI_SELECT, but its API only accepts MULTIPLE_SELECT.
								# Required, so WhatsApp keeps Submit disabled until at least one item is ticked.
								{
									"type": "MULTIPLE_SELECT",
									"label": "Items",
									"text": "Select all that apply",
									"options": "{{1}}",
									"required": True,
								},
								{"type": "FOOTER", "label": submit_text},
							],
						}
					],
				}
			},
		},
	)
	# Part of an onboarding the restaurant asked for, so Utility; Meta may still make it Marketing
	twilio_request(
		twilio,
		"POST",
		f"{CONTENT_API_URL}/{content['sid']}/ApprovalRequests/whatsapp",
		{"name": name, "category": "UTILITY"},
	)
	# Saved apart, so the approved form keeps being sent until this one is approved
	frappe.db.set_single_value(SETTINGS, "items_pending_content_sid", content["sid"])
	return {"sid": content["sid"], "body": message}


@frappe.whitelist()
def get_items_template_status():
	"""The pending item form's status when there is one, switching to it once WhatsApp approves it."""
	frappe.only_for("System Manager")
	pending = frappe.db.get_single_value(SETTINGS, "items_pending_content_sid")
	status = get_template_status(pending or frappe.db.get_single_value(SETTINGS, "items_content_sid"))
	if pending and status["status"] == "approved":
		frappe.db.set_single_value(SETTINGS, {"items_content_sid": pending, "items_pending_content_sid": None})
		status["switched"] = True
	return status


@frappe.whitelist()
def get_invitation_template_status():
	frappe.only_for("System Manager")
	return get_template_status(frappe.db.get_single_value(SETTINGS, "invitation_content_sid"))


def get_template_status(content_sid: str | None) -> dict:
	if not content_sid:
		return {"status": "not created"}
	approval = twilio_request(get_twilio(), "GET", f"{CONTENT_API_URL}/{content_sid}/ApprovalRequests")
	whatsapp = approval.get("whatsapp") or {}
	return {
		"sid": content_sid,
		"status": whatsapp.get("status") or "not submitted",
		# Meta sets the category from the wording, whatever was asked for
		"category": whatsapp.get("category"),
		"rejection_reason": whatsapp.get("rejection_reason"),
	}


@frappe.whitelist()
def get_join_link():
	"""The wa.me link that opens a chat with the join keyword typed in, for the website, a QR code or a flyer."""
	from urllib.parse import quote

	frappe.only_for("System Manager")
	keyword = (frappe.db.get_single_value(SETTINGS, "join_keyword") or "").strip()
	if not keyword:
		frappe.throw(_("Please set the Join Keyword first."))
	number = get_twilio().from_number.removeprefix("whatsapp:").lstrip("+")
	return f"https://wa.me/{number}?text={quote(keyword)}"


@frappe.whitelist(methods=["POST"])
def connect_restaurant_replies(site_url: str):
	"""Point the WhatsApp number's incoming messages at whatsapp_webhook; others still reach the previous webhook."""
	frappe.only_for("System Manager")
	parsed = urlparse((site_url or "").strip())
	if parsed.scheme != "https" or not parsed.netloc or parsed.username or parsed.password or parsed.query or parsed.fragment:
		frappe.throw(_("Please use the site's public https:// address, e.g. your ngrok address."))
	url = f"https://{parsed.netloc}{parsed.path.rstrip('/')}/api/method/{WEBHOOK_METHOD}"

	twilio = get_twilio()
	sender = get_sender(twilio)
	webhook = sender.get("webhook") or {}
	previous = webhook.get("callback_url") or ""
	values = {"webhook_url": url}
	# Reconnecting (e.g. a new ngrok address) keeps the original previous webhook
	if previous and not previous.endswith(WEBHOOK_METHOD):
		values["previous_webhook_url"] = previous
	frappe.db.set_single_value(SETTINGS, values)
	# The signature check needs the new address before Twilio starts calling it
	frappe.db.commit()

	updated = {key: value for key, value in webhook.items() if value is not None}
	updated.update(callback_url=url, callback_method="POST")
	twilio_request(twilio, "POST", f"{SENDERS_API_URL}/{sender['sid']}", {"webhook": updated})
	return {"webhook_url": url, "previous_webhook_url": frappe.db.get_single_value(SETTINGS, "previous_webhook_url")}


@frappe.whitelist(methods=["POST"])
def disconnect_restaurant_replies():
	"""Give the WhatsApp number's incoming messages back to the previous webhook."""
	frappe.only_for("System Manager")
	previous = frappe.db.get_single_value(SETTINGS, "previous_webhook_url")
	if not previous:
		frappe.throw(_("There is no previous webhook to give the replies back to."))
	twilio = get_twilio()
	sender = get_sender(twilio)
	updated = {key: value for key, value in (sender.get("webhook") or {}).items() if value is not None}
	updated.update(callback_url=previous, callback_method="POST")
	twilio_request(twilio, "POST", f"{SENDERS_API_URL}/{sender['sid']}", {"webhook": updated})
	frappe.db.set_single_value(SETTINGS, {"webhook_url": None, "previous_webhook_url": None})
	return {"webhook_url": previous}


def get_sender(twilio) -> dict:
	senders = twilio_request(twilio, "GET", f"{SENDERS_API_URL}?Channel=whatsapp&PageSize=50").get("senders") or []
	matches = [sender for sender in senders if sender.get("sender_id") == twilio.from_number]
	if len(matches) != 1:
		frappe.throw(_("{0} is not a WhatsApp sender on this Twilio account.").format(twilio.from_number.removeprefix("whatsapp:")))
	return matches[0]
