// "View on Map" for a Supplier with a location (custom_latitude / custom_longitude, filled by the WhatsApp onboarding).
frappe.ui.form.on("Supplier", {
	refresh(frm) {
		const { custom_latitude: lat, custom_longitude: lng } = frm.doc;
		if (frm.is_new() || !lat || !lng) return;
		frm.add_custom_button(__("View on Map"), () => {
			window.open(`https://www.google.com/maps/search/?api=1&query=${encodeURIComponent(`${lat},${lng}`)}`, "_blank", "noopener");
		});
	},
});
