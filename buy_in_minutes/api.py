import frappe


@frappe.whitelist(allow_guest=True)
def get_items(limit_page_length=20, search=None, item_group=None):
	limit_page_length = frappe.utils.cint(limit_page_length) or 20

	filters = {"disabled": 0}
	or_filters = None

	if item_group:
		filters["item_group"] = item_group

	if search:
		search_text = f"%{search}%"
		or_filters = [
			["item_name", "like", search_text],
			["item_code", "like", search_text],
			["description", "like", search_text],
		]

	item_meta = frappe.get_meta("Item")
	optional_fields = [
		fieldname
		for fieldname in ("image", "website_image", "thumbnail", "standard_rate")
		if item_meta.has_field(fieldname)
	]

	items = frappe.get_all(
		"Item",
		fields=[
			"name",
			"item_code",
			"item_name",
			"item_group",
			"description",
			"disabled",
		] + optional_fields,
		filters=filters,
		or_filters=or_filters,
		order_by="modified desc",
		limit_page_length=limit_page_length,
	)

	return items
