frappe.ui.form.on("Lead", {
	refresh(frm) {
		if (frm.is_new()) return;
		frm.add_custom_button(__("Invite on WhatsApp"), () => {
			// Defined in lead_list.js
			buy_in_minutes.invite_leads_on_whatsapp([frm.doc.name], () => frm.reload_doc());
		});
	},
});
