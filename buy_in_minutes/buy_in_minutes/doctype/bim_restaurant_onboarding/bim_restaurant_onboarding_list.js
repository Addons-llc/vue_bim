const ONBOARDING_COLORS = {
	Invited: "blue",
	"Confirming Name": "orange",
	"Awaiting Logo": "orange",
	"Awaiting Location": "orange",
	Completed: "green",
	Declined: "gray",
	Failed: "red",
};

frappe.listview_settings["BIM Restaurant Onboarding"] = {
	add_fields: ["status"],
	get_indicator(doc) {
		return [__(doc.status), ONBOARDING_COLORS[doc.status] || "gray", `status,=,${doc.status}`];
	},
};
