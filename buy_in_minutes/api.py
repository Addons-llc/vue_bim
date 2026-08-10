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


@frappe.whitelist()
def get_sales_order(sales_order_name):
	if not sales_order_name:
		frappe.throw("Sales Order is required.")

	if not frappe.db.exists("Sales Order", sales_order_name):
		frappe.throw("Sales Order was not found.")

	sales_order = frappe.get_doc("Sales Order", sales_order_name)
	if sales_order.owner != frappe.session.user and frappe.session.user != "Administrator":
		frappe.throw("You are not allowed to view this Sales Order.")

	item_codes = [row.item_code for row in sales_order.items if row.item_code]
	item_images = {}
	if item_codes:
		item_meta = frappe.get_meta("Item")
		image_fields = [
			fieldname
			for fieldname in ("image", "website_image", "thumbnail")
			if item_meta.has_field(fieldname)
		]
		if image_fields:
			item_records = frappe.get_all(
				"Item",
				fields=["name"] + image_fields,
				filters={"name": ["in", item_codes]},
				ignore_permissions=True,
				limit_page_length=len(item_codes),
			)
			for item in item_records:
				item_images[item.name] = next(
					(item.get(fieldname) for fieldname in image_fields if item.get(fieldname)),
					"",
				)

	return {
		"name": sales_order.name,
		"status": sales_order.status,
		"transaction_date": sales_order.transaction_date,
		"grand_total": flt(sales_order.grand_total),
		"currency": sales_order.currency or "AED",
		"items": [
			{
				"item_code": row.item_code,
				"item_name": row.item_name or row.item_code,
				"description": row.description,
				"qty": flt(row.qty),
				"rate": flt(row.rate),
				"amount": flt(row.amount),
				"image": item_images.get(row.item_code),
			}
			for row in sales_order.items
		],
	}


@frappe.whitelist()
def get_ordered_products(limit_page_length=40):
	limit_page_length = frappe.utils.cint(limit_page_length) or 40
	if frappe.session.user == "Guest":
		frappe.throw("Please sign in to view ordered products.")

	sales_orders = frappe.get_all(
		"Sales Order",
		fields=["name", "transaction_date"],
		filters={
			"owner": frappe.session.user,
			"docstatus": ["<", 2],
		},
		order_by="modified desc",
		ignore_permissions=True,
		limit_page_length=20,
	)
	sales_order_names = [sales_order.name for sales_order in sales_orders]
	if not sales_order_names:
		return []

	order_dates = {
		sales_order.name: sales_order.transaction_date
		for sales_order in sales_orders
	}
	rows = frappe.get_all(
		"Sales Order Item",
		fields=["parent", "item_code", "item_name", "description", "qty", "rate", "amount"],
		filters={"parent": ["in", sales_order_names]},
		order_by="creation desc",
		ignore_permissions=True,
		limit_page_length=limit_page_length,
	)
	item_codes = list({row.item_code for row in rows if row.item_code})
	item_images = {}
	item_groups = {}

	if item_codes:
		item_meta = frappe.get_meta("Item")
		image_fields = [
			fieldname
			for fieldname in ("image", "website_image", "thumbnail")
			if item_meta.has_field(fieldname)
		]
		item_records = frappe.get_all(
			"Item",
			fields=["name", "item_group"] + image_fields,
			filters={"name": ["in", item_codes]},
			ignore_permissions=True,
			limit_page_length=len(item_codes),
		)
		for item in item_records:
			item_groups[item.name] = item.item_group
			item_images[item.name] = next(
				(item.get(fieldname) for fieldname in image_fields if item.get(fieldname)),
				"",
			)

	ordered_products = []
	seen_item_codes = set()
	for row in rows:
		if not row.item_code or row.item_code in seen_item_codes:
			continue

		seen_item_codes.add(row.item_code)
		ordered_products.append(
			{
				"id": row.item_code,
				"itemCode": row.item_code,
				"name": row.item_name or row.item_code,
				"category": item_groups.get(row.item_code) or "",
				"description": row.description,
				"price": flt(row.rate),
				"currency": "AED",
				"quantity": flt(row.qty),
				"orderedAmount": flt(row.amount),
				"orderedDate": order_dates.get(row.parent),
				"salesOrder": row.parent,
				"rating": 4.8,
				"reviewCount": 0,
				"stockQuantity": 1,
				"inStock": True,
				"deliveryTime": "Ordered",
				"image": item_images.get(row.item_code),
			}
		)

	return ordered_products
