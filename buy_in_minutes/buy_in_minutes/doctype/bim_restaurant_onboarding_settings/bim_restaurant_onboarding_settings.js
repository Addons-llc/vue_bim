const ONBOARDING = "buy_in_minutes.restaurant_onboarding";

frappe.ui.form.on("BIM Restaurant Onboarding Settings", {
	refresh(frm) {
		const group = __("WhatsApp");
		frm.add_custom_button(__("Create Invitation Template"), () => create_invitation_template(frm), group);
		frm.add_custom_button(__("Check Template Status"), () => check_template_status("get_invitation_template_status", __("Invitation Template")), group);
		frm.add_custom_button(__("Create Items Template"), () => create_items_template(frm), group);
		frm.add_custom_button(__("Check Items Template Status"), () => check_items_template_status(frm), group);
		frm.add_custom_button(__("Get Join Link"), () => show_join_link(frm), group);
		frm.add_custom_button(__("Invite Existing Leads"), () => invite_existing_leads(), group);
		frm.add_custom_button(__("Connect Restaurant Replies"), () => connect_replies(frm), group);
		if (frm.doc.previous_webhook_url) {
			frm.add_custom_button(__("Disconnect Restaurant Replies"), () => disconnect_replies(frm), group);
		}
	},
});

function saved_first(frm) {
	if (frm.is_dirty()) {
		frappe.msgprint(__("Please save the settings first."));
		return false;
	}
	return true;
}

function create_invitation_template(frm) {
	if (!saved_first(frm)) return;
	frappe.confirm(
		__("Submit the Invitation Message with its two buttons to WhatsApp for approval? Approval usually takes from a few minutes to a day."),
		() =>
			frappe.call({
				method: `${ONBOARDING}.create_invitation_template`,
				freeze: true,
				freeze_message: __("Creating template..."),
				callback: ({ message }) => {
					frappe.msgprint({
						title: __("Submitted for WhatsApp Approval"),
						indicator: "green",
						message: __("Template {0}: {1}<br><br>Use Check Template Status to see when it is approved.", [
							message.sid,
							frappe.utils.escape_html(message.body),
						]),
					});
					frm.reload_doc();
				},
			})
	);
}

function invite_existing_leads() {
	frappe.confirm(__("Send the WhatsApp invitation to every Lead with a phone number that has not been invited yet?"), () =>
		frappe.call({
			method: `${ONBOARDING}.invite_existing_leads`,
			freeze: true,
			callback: ({ message }) => {
				frappe.msgprint(
					message.count
						? __("Inviting {0} Leads in the background. See BIM Restaurant Onboarding.", [message.count])
						: __("Every Lead with a phone number has already been invited.")
				);
			},
		})
	);
}

function check_template_status(method, title) {
	frappe.call({
		method: `${ONBOARDING}.${method}`,
		freeze: true,
		callback: ({ message }) => show_template_status(title, message),
	});
}

function show_template_status(title, message) {
	const reason = message.rejection_reason ? `<br>${frappe.utils.escape_html(message.rejection_reason)}` : "";
	// Meta decides the category from the wording; Marketing is charged even inside an open chat
	const category = message.category ? `<br>${__("Category")}: <b>${frappe.utils.escape_html(message.category)}</b>` : "";
	const switched = message.switched ? `<br><br>${__("Approved, so this form is now sent to restaurants.")}` : "";
	frappe.msgprint({
		title,
		indicator: message.status === "approved" ? "green" : message.status === "rejected" ? "red" : "orange",
		message: `${frappe.utils.escape_html(message.sid || "")} ${frappe.utils.escape_html(message.status)}${category}${reason}${switched}`,
	});
}

function create_items_template(frm) {
	if (!saved_first(frm)) return;
	frappe.confirm(
		__("Submit the item form (Items Message, Select Items button, a tick box per item and Submit) to WhatsApp for approval? The current form keeps being sent until the new one is approved."),
		() =>
			frappe.call({
				method: `${ONBOARDING}.create_items_template`,
				freeze: true,
				freeze_message: __("Creating template..."),
				callback: ({ message }) => {
					frappe.msgprint({
						title: __("Submitted for WhatsApp Approval"),
						indicator: "green",
						message: __("Template {0}<br><br>Use Check Items Template Status to see when it is approved; it is used from then on.", [
							message.sid,
						]),
					});
					frm.reload_doc();
				},
			})
	);
}

function check_items_template_status(frm) {
	frappe.call({
		method: `${ONBOARDING}.get_items_template_status`,
		freeze: true,
		callback: ({ message }) => {
			show_template_status(__("Items Template"), message);
			if (message.switched) frm.reload_doc();
		},
	});
}

function show_join_link(frm) {
	if (!saved_first(frm)) return;
	frappe.call({
		method: `${ONBOARDING}.get_join_link`,
		callback: ({ message: link }) => {
			const safe = frappe.utils.escape_html(link);
			const dialog = frappe.msgprint({
				title: __("Join Link"),
				message: __(
					"Restaurants that open this link get the Join Keyword typed in for them and only have to tap send. Put it on your website, in a QR code or on a flyer.<br><br><a href='{0}' target='_blank' rel='noopener'>{0}</a>",
					[safe]
				),
				primary_action: {
					label: __("Copy Link"),
					action: () => {
						frappe.utils.copy_to_clipboard(link);
						dialog.hide();
					},
				},
			});
		},
	});
}

function connect_replies(frm) {
	if (!saved_first(frm)) return;
	frappe.prompt(
		{
			fieldname: "site_url",
			fieldtype: "Data",
			label: __("Public Site URL"),
			default: window.location.protocol === "https:" ? window.location.origin : "",
			reqd: 1,
			description: __(
				"The https:// address Twilio can reach this site on, e.g. your ngrok address. Messages that are not from a restaurant being onboarded keep going to the number's current webhook."
			),
		},
		({ site_url }) =>
			frappe.call({
				method: `${ONBOARDING}.connect_restaurant_replies`,
				args: { site_url },
				freeze: true,
				freeze_message: __("Connecting..."),
				callback: ({ message }) => {
					frappe.msgprint({
						title: __("Restaurant Replies Connected"),
						indicator: "green",
						message: __("Replies now go to {0}", [frappe.utils.escape_html(message.webhook_url)]),
					});
					frm.reload_doc();
				},
			}),
		__("Connect Restaurant Replies"),
		__("Connect")
	);
}

function disconnect_replies(frm) {
	frappe.confirm(__("Give the WhatsApp number's replies back to {0}?", [frappe.utils.escape_html(frm.doc.previous_webhook_url)]), () =>
		frappe.call({
			method: `${ONBOARDING}.disconnect_restaurant_replies`,
			freeze: true,
			callback: () => frm.reload_doc(),
		})
	);
}
