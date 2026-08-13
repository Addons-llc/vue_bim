import frappe
from frappe.utils import flt


SELLING_PRICE_LIST = "Selling Price"
ITEM_SUPPLIER_PORTAL_PUBLISH_FIELDS = (
	"published_in_supplier_portal",
	"custom_published_in_supplier_portal",
)
ITEM_SUPPLIER_FIELDS = (
	"supplier",
	"default_supplier",
	"supplier_name",
	"custom_supplier",
	"custom_supplier_name",
)
SUPPLIER_DETAIL_FIELDS = (
	"supplier_name",
	"supplier_group",
	"supplier_type",
	"supplier_details",
	"website",
	"mobile_no",
	"email_id",
	"image",
	"supplier_logo",
	"supplier_image",
	"supplier_banner",
	"supplier_banner_image",
	"custom_supplier_logo",
	"custom_supplier_image",
	"custom_supplier_banner",
	"custom_supplier_banner_image",
	"custom_seller_since",
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


def _get_item_supplier_portal_publish_fields():
	meta = frappe.get_meta("Item")
	publish_fields = _get_existing_fields("Item", ITEM_SUPPLIER_PORTAL_PUBLISH_FIELDS)

	if publish_fields:
		return publish_fields

	return [
		df.fieldname
		for df in meta.fields
		if df.fieldname and df.label == "Published in Supplier Portal"
	]


def _record_has_publish_flag(record, publish_fields):
	if not publish_fields:
		return True

	return any(_is_truthy_flag(record.get(fieldname)) for fieldname in publish_fields)


def _filter_published_records(records, publish_fields):
	if not publish_fields:
		return records

	return [
		record
		for record in records
		if _record_has_publish_flag(record, publish_fields)
	]


def _get_item_group_order_fields():
	return _get_existing_fields("Item Group", ("lft", "idx"))


def _get_item_group_order_by(order_fields):
	if "lft" in order_fields:
		return "lft asc"

	if "idx" in order_fields:
		return "idx asc"

	return "name asc"


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


def _get_item_supplier_links(item_names):
	item_names = [item_name for item_name in item_names if item_name]
	if not item_names or not frappe.db.exists("DocType", "Item Supplier"):
		return {}

	item_supplier_rows = frappe.get_all(
		"Item Supplier",
		fields=["parent", "supplier"],
		filters={"parent": ["in", item_names]},
		order_by="idx asc",
		ignore_permissions=True,
		limit_page_length=len(item_names) * 5,
	)
	item_suppliers = {}
	for row in item_supplier_rows:
		if row.parent and row.supplier and row.parent not in item_suppliers:
			item_suppliers[row.parent] = row.supplier

	return item_suppliers


def _get_supplier_from_item_fields(item):
	for fieldname in ITEM_SUPPLIER_FIELDS:
		if item.get(fieldname):
			return item.get(fieldname)

	return ""


def _apply_supplier_details(items):
	item_names = [item.name for item in items if item.name]
	item_supplier_links = _get_item_supplier_links(item_names)
	item_suppliers = {}

	for item in items:
		supplier = _get_supplier_from_item_fields(item) or item_supplier_links.get(item.name) or ""
		if supplier:
			item_suppliers[item.name] = supplier

	supplier_names = sorted({supplier for supplier in item_suppliers.values() if supplier})
	if not supplier_names:
		return

	supplier_fields = ["name"] + _get_existing_fields("Supplier", SUPPLIER_DETAIL_FIELDS)
	supplier_records = frappe.get_all(
		"Supplier",
		fields=supplier_fields,
		filters={"name": ["in", supplier_names]},
		ignore_permissions=True,
		limit_page_length=len(supplier_names),
	)
	suppliers_by_name = {
		supplier.name: supplier
		for supplier in supplier_records
	}

	for item in items:
		supplier_name = item_suppliers.get(item.name)
		supplier = suppliers_by_name.get(supplier_name)
		if not supplier_name:
			continue

		item.supplier = supplier_name
		item.default_supplier = supplier_name
		item.supplier_display_name = (
			supplier.get("supplier_name")
			if supplier
			else supplier_name
		) or supplier_name

		if not supplier:
			continue

		item.supplier_name = supplier.get("supplier_name") or supplier_name
		item.supplier_group = supplier.get("supplier_group")
		item.supplier_type = supplier.get("supplier_type")
		item.supplier_details = supplier.get("supplier_details")
		item.supplier_phone = supplier.get("mobile_no")
		item.supplier_email = supplier.get("email_id")
		item.supplier_website = supplier.get("website")
		item.supplier_image = (
			supplier.get("image")
			or supplier.get("supplier_logo")
			or supplier.get("supplier_image")
			or supplier.get("custom_supplier_logo")
			or supplier.get("custom_supplier_image")
		)
		item.supplier_banner = (
			supplier.get("supplier_banner")
			or supplier.get("supplier_banner_image")
			or supplier.get("custom_supplier_banner")
			or supplier.get("custom_supplier_banner_image")
		)
		item.seller_since = supplier.get("custom_seller_since")


def _get_supplier_store_record(supplier_store):
	if not supplier_store or not frappe.db.exists("DocType", "Supplier Store"):
		return None

	if frappe.db.exists("Supplier Store", supplier_store):
		return frappe.get_doc("Supplier Store", supplier_store)

	store_meta = frappe.get_meta("Supplier Store")
	or_filters = [
		[fieldname, "=", supplier_store]
		for fieldname in ("store_code", "store_name", "supplier")
		if store_meta.has_field(fieldname)
	]

	if not or_filters:
		return None

	store_records = frappe.get_all(
		"Supplier Store",
		fields=["name"],
		or_filters=or_filters,
		ignore_permissions=True,
		limit_page_length=1,
	)

	return frappe.get_doc("Supplier Store", store_records[0].name) if store_records else None


def _get_supplier_store_item_codes(supplier_store_record):
	if not supplier_store_record:
		return []

	item_codes = []
	store_meta = frappe.get_meta("Supplier Store")
	table_fields = [
		field
		for field in store_meta.fields
		if field.fieldtype == "Table"
	]

	for table_field in table_fields:
		for row in supplier_store_record.get(table_field.fieldname) or []:
			for fieldname in (
				"item",
				"item_code",
				"item_name",
				"product",
				"product_code",
			):
				if row.get(fieldname):
					item_codes.append(row.get(fieldname))
					break

	return list(dict.fromkeys(item_codes))


def _filter_items_by_supplier(items, supplier):
	if not supplier:
		return items

	return [
		item
		for item in items
		if supplier in (
			item.get("supplier"),
			item.get("default_supplier"),
			item.get("supplier_name"),
			item.get("supplier_display_name"),
		)
	]


def _filter_items_by_item_codes(items, item_codes):
	item_codes = set(item_codes or [])
	if not item_codes:
		return items

	return [
		item
		for item in items
		if item.get("name") in item_codes or item.get("item_code") in item_codes
	]


def _get_supplier_detail_record(supplier):
	if not supplier:
		return None

	supplier_fields = ["name"] + _get_existing_fields("Supplier", SUPPLIER_DETAIL_FIELDS)
	supplier_filters = {"name": supplier}

	if not frappe.db.exists("Supplier", supplier):
		supplier_filters = {"supplier_name": supplier}

	supplier_records = frappe.get_all(
		"Supplier",
		fields=supplier_fields,
		filters=supplier_filters,
		ignore_permissions=True,
		limit_page_length=1,
	)

	return supplier_records[0] if supplier_records else None


@frappe.whitelist(allow_guest=True)
def get_supplier_details(supplier):
	return _get_supplier_detail_record(supplier) or {}


@frappe.whitelist(allow_guest=True)
def get_supplier_stores(limit_page_length=24, published=1):
	limit_page_length = frappe.utils.cint(limit_page_length) or 24

	if not frappe.db.exists("DocType", "Supplier Store"):
		return []

	store_fields = _get_existing_fields(
		"Supplier Store",
		(
			"store_name",
			"store_code",
			"supplier",
			"store_status",
			"published",
			"store_logo",
			"logo",
			"supplier_logo",
			"custom_store_logo",
			"custom_supplier_logo",
			"banner_image",
			"store_banner",
			"store_banner_image",
			"supplier_banner",
			"supplier_banner_image",
			"custom_banner_image",
			"custom_store_banner",
			"custom_store_banner_image",
			"custom_supplier_banner",
			"custom_supplier_banner_image",
			"primary_colour",
			"secondary_colour",
			"contact_number",
			"whatsapp_number",
			"email",
			"contact_email",
			"website",
			"store_website",
			"description",
			"store_details",
			"about",
			"supplier_details",
			"seller_since",
		),
	)
	fields = ["name"] + store_fields
	filters = {}

	if "store_status" in store_fields:
		filters["store_status"] = "Active"

	if _is_truthy_flag(published) and "published" in store_fields:
		filters["published"] = 1

	return frappe.get_all(
		"Supplier Store",
		fields=fields,
		filters=filters,
		ignore_permissions=True,
		order_by="modified desc",
		limit_page_length=limit_page_length,
	)


@frappe.whitelist(allow_guest=True)
def get_items(
	limit_page_length=20,
	limit_start=0,
	search=None,
	item_group=None,
	item=None,
	supplier=None,
	supplier_store=None,
	published=1,
):
	limit_page_length = frappe.utils.cint(limit_page_length) or 20
	limit_start = frappe.utils.cint(limit_start) or 0
	supplier_store_record = _get_supplier_store_record(supplier_store)
	supplier_store_item_codes = _get_supplier_store_item_codes(supplier_store_record)

	if supplier_store and not supplier_store_record:
		return []

	if supplier_store_record and not supplier:
		supplier = supplier_store_record.get("supplier")

	filters = {"disabled": 0}
	or_filters = None

	if item:
		filters["name"] = item

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
	publish_fields = _get_item_supplier_portal_publish_fields()
	optional_fields = [
		fieldname
		for fieldname in (
			"image",
			"website_image",
			"thumbnail",
			"standard_rate",
			*ITEM_SUPPLIER_FIELDS,
		)
		if item_meta.has_field(fieldname)
	]
	fields = [
		"name",
		"item_code",
		"item_name",
		"item_group",
		"description",
		"disabled",
	] + optional_fields + publish_fields
	get_all_kwargs = {
		"fields": fields,
		"filters": filters,
		"or_filters": or_filters,
		"order_by": "modified desc",
	}
	should_filter_after_loading = bool(supplier or supplier_store_item_codes)

	if _is_truthy_flag(published) and (publish_fields or should_filter_after_loading):
		get_all_kwargs["limit_page_length"] = 0
	else:
		get_all_kwargs["limit_start"] = limit_start
		get_all_kwargs["limit_page_length"] = limit_page_length

	items = frappe.get_all(
		"Item",
		**get_all_kwargs,
	)

	if _is_truthy_flag(published):
		items = _filter_published_records(items, publish_fields)

	_apply_selling_prices(items)
	_apply_item_group_images(items)
	_apply_supplier_details(items)
	items = _filter_items_by_item_codes(items, supplier_store_item_codes)
	items = _filter_items_by_supplier(items, supplier)

	if _is_truthy_flag(published) and (publish_fields or should_filter_after_loading):
		items = items[limit_start:limit_start + limit_page_length]

	return items


@frappe.whitelist(allow_guest=True)
def get_item_groups(limit_page_length=5000, published=1):
	limit_page_length = frappe.utils.cint(limit_page_length) or 5000
	optional_fields = _get_existing_fields(
		"Item Group",
		(
			"item_group_name",
			"profile_image",
			"category_profile_image",
			"item_group_profile_image",
			"item_group_image",
			"item_group_website_image",
			"image",
			"website_image",
			"parent_item_group",
			"is_group",
		),
	)
	order_fields = _get_item_group_order_fields()

	item_groups = frappe.get_all(
		"Item Group",
		fields=["name"] + optional_fields + order_fields,
		ignore_permissions=True,
		order_by=_get_item_group_order_by(order_fields),
		limit_page_length=limit_page_length,
	)

	return [
		item_group
		for item_group in item_groups
		if item_group.name != "All Item Groups"
	]


def _get_customer_for_user(user_name):
	if not user_name or user_name == "Guest":
		return None

	user = frappe.get_cached_doc("User", user_name)
	if user.email:
		customer = frappe.db.get_value("Customer", {"email_id": user.email}, "name")
		if customer:
			return customer

	if user.mobile_no:
		return frappe.db.get_value("Customer", {"mobile_no": user.mobile_no}, "name")

	return None


def _can_view_sales_order(sales_order):
	if frappe.session.user == "Administrator" or sales_order.owner == frappe.session.user:
		return True

	return bool(sales_order.customer and sales_order.customer == _get_customer_for_user(frappe.session.user))


@frappe.whitelist(allow_guest=True)
def get_sales_order(sales_order_name):
	if frappe.session.user == "Guest":
		frappe.throw("Please sign in to view this Sales Order.", frappe.AuthenticationError)

	if not sales_order_name:
		frappe.throw("Sales Order is required.")

	if not frappe.db.exists("Sales Order", sales_order_name):
		frappe.throw("Sales Order was not found.")

	sales_order = frappe.get_doc("Sales Order", sales_order_name)
	if not _can_view_sales_order(sales_order):
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
