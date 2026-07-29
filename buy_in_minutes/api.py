import frappe


@frappe.whitelist(allow_guest=True)
def get_items(limit_page_length=20, search=None, item_group=None):
	limit_page_length = frappe.utils.cint(limit_page_length) or 20

	filters = {"disabled": 0}

	if item_group:
		filters["item_group"] = item_group

	if search:
		filters["item_name"] = ["like", f"%{search}%"]

	items = frappe.get_all(
		"Item",
		fields=[
			"name",
			"item_code",
			"item_name",
			"item_group",
			"description",
			"image",
			"website_image",
			"thumbnail",
			"standard_rate",
			"disabled",
		],
		filters=filters,
		order_by="modified desc",
		limit_page_length=limit_page_length,
	)

	return items
