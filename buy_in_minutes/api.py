import frappe
from frappe.utils import flt


SELLING_PRICE_LIST = "Selling Price"


def _get_selling_prices(item_codes):
	item_codes = [item_code for item_code in item_codes if item_code]
	if not item_codes:
		return {}

	price_records = frappe.get_all(
		"Item Price",
		fields=["item_code", "price_list", "price_list_rate", "currency", "selling"],
		filters={
			"item_code": ["in", item_codes],
			"selling": 1,
		},
		limit_page_length=len(item_codes) * 5,
	)

	prices = {}
	for price_record in price_records:
		item_code = price_record.item_code
		current_price_record = prices.get(item_code)
		if not current_price_record or price_record.price_list == SELLING_PRICE_LIST:
			prices[item_code] = price_record

	return prices


def _apply_selling_prices(items):
	selling_prices = _get_selling_prices([item.item_code or item.name for item in items])

	for item in items:
		item_code = item.item_code or item.name
		price_record = selling_prices.get(item_code)
		if not price_record:
			item.selling_price = flt(item.get("standard_rate"))
			item.price_list_rate = flt(item.get("standard_rate"))
			item.currency = "AED"
			continue

		item.selling_price = flt(price_record.price_list_rate)
		item.price_list_rate = flt(price_record.price_list_rate)
		item.price_list = price_record.price_list
		item.currency = price_record.currency or "AED"


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

	_apply_selling_prices(items)

	return items
