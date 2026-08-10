import frappe
from frappe.utils import flt


SELLING_PRICE_LIST = "Selling Price"
PUBLISH_FIELDS = (
	"published",
	"is_published",
	"published_in_website",
	"show_in_website",
	"website_published",
)


def _is_truthy_flag(value):
	return value in (True, 1, "1", "Yes")


def _get_existing_fields(doctype, fieldnames):
	meta = frappe.get_meta(doctype)

	return [
		fieldname
		for fieldname in fieldnames
		if meta.has_field(fieldname)
	]


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


def _apply_item_group_images(items):
	item_groups = list({item.item_group for item in items if item.item_group})
	if not item_groups:
		return

	item_group_meta = frappe.get_meta("Item Group")
	image_field = next(
		(
			fieldname
			for fieldname in (
				"profile_image",
				"category_profile_image",
				"item_group_profile_image",
				"image",
				"website_image",
			)
			if item_group_meta.has_field(fieldname)
		),
		None,
	)

	if not image_field:
		return

	item_group_records = frappe.get_all(
		"Item Group",
		fields=["name", image_field],
		filters={"name": ["in", item_groups]},
		ignore_permissions=True,
		limit_page_length=len(item_groups),
	)
	item_group_images = {
		record.name: record.get(image_field)
		for record in item_group_records
	}

	for item in items:
		item.item_group_image = item_group_images.get(item.item_group)


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
	_apply_item_group_images(items)

	return items


@frappe.whitelist(allow_guest=True)
def get_item_groups(limit_page_length=5000, published=1):
	limit_page_length = frappe.utils.cint(limit_page_length) or 5000

	item_groups_with_items = frappe.get_all(
		"Item",
		fields=["item_group"],
		filters={"disabled": 0},
		group_by="item_group",
		ignore_permissions=True,
		limit_page_length=limit_page_length,
	)
	item_group_names = [
		item_group.item_group
		for item_group in item_groups_with_items
		if item_group.item_group
	]

	if not item_group_names:
		return []

	optional_fields = _get_existing_fields(
		"Item Group",
		(
			"item_group_name",
			"profile_image",
			"category_profile_image",
			"item_group_profile_image",
			"image",
			"website_image",
		),
	)
	publish_fields = _get_existing_fields("Item Group", PUBLISH_FIELDS)

	item_groups = frappe.get_all(
		"Item Group",
		fields=["name"] + optional_fields + publish_fields,
		filters={"name": ["in", item_group_names]},
		ignore_permissions=True,
		order_by="name asc",
		limit_page_length=len(item_group_names),
	)

	if _is_truthy_flag(published) and publish_fields:
		item_groups = [
			item_group
			for item_group in item_groups
			if any(_is_truthy_flag(item_group.get(fieldname)) for fieldname in publish_fields)
		]

	return item_groups
