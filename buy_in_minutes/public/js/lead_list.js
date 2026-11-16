// "Invite on WhatsApp" in the Lead list's Actions menu, for the selected Leads (restaurant_onboarding.py).
// Frappe runs this file whenever the Lead doctype loads, so lead.js uses invite_leads_on_whatsapp on the form too.
frappe.provide("buy_in_minutes");

buy_in_minutes.invite_leads_on_whatsapp = function (leads, after_send) {
	if (!leads.length) {
		frappe.msgprint(__("Select the Leads to invite on WhatsApp."));
		return;
	}
	const question =
		leads.length === 1
			? __("Invite {0} on WhatsApp to add their restaurant to Buy In Minutes?", [frappe.utils.escape_html(leads[0])])
			: __("Invite {0} Leads on WhatsApp to add their restaurant to Buy In Minutes?", [leads.length]);
	frappe.confirm(question, () => {
		frappe.call({
			method: "buy_in_minutes.restaurant_onboarding.send_invitations",
			args: { leads },
			freeze: true,
			freeze_message: __("Sending WhatsApp..."),
			callback({ message: result }) {
				if (result.queued) {
					frappe.show_alert({
						message: __("Inviting {0} Leads in the background. See BIM Restaurant Onboarding.", [result.count]),
						indicator: "green",
					});
				} else {
					const parts = [__("Invited: {0}", [result.sent])];
					if (result.already_invited) parts.push(__("Already invited: {0}", [result.already_invited]));
					if (result.no_number) parts.push(__("No number: {0}", [result.no_number]));
					if (result.failed) parts.push(__("Failed: {0}", [result.failed]));
					frappe.show_alert({
						message: parts.join(", "),
						indicator: result.sent === leads.length ? "green" : "orange",
					});
				}
				after_send && after_send();
			},
		});
	});
};

(() => {
	const settings = (frappe.listview_settings["Lead"] = frappe.listview_settings["Lead"] || {});
	const onload = settings.onload;
	settings.onload = function (listview) {
		onload && onload.call(this, listview);
		listview.page.add_action_item(__("Invite on WhatsApp"), () => {
			buy_in_minutes.invite_leads_on_whatsapp(listview.get_checked_items(true), () => listview.clear_checked_items());
		});
	};
})();
