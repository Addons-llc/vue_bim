import frappe
from frappe import _
from frappe.utils import flt, getdate, today


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
ITEM_GROUP_PUBLISH_FIELDS = (
	"published",
	"is_published",
	"show_in_website",
	"custom_published",
	"custom_is_published",
	"custom_show_in_website",
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
	"custom_google_address",
	"custom_latitude",
	"custom_longitude",
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


def _get_item_group_publish_fields():
	return _get_existing_fields("Item Group", ITEM_GROUP_PUBLISH_FIELDS)


def _get_selling_price_list():
	configured_price_list = (
		frappe.defaults.get_user_default("selling_price_list")
		or frappe.defaults.get_global_default("selling_price_list")
	)
	if configured_price_list and frappe.db.get_value(
		"Price List",
		{"name": configured_price_list, "enabled": 1, "selling": 1},
		"name",
	):
		return configured_price_list

	enabled_price_list = frappe.db.get_value(
		"Price List",
		{"enabled": 1, "selling": 1},
		"name",
	)
	if enabled_price_list:
		return enabled_price_list

	return SELLING_PRICE_LIST


def _get_default_company():
	company = frappe.defaults.get_user_default("Company") or frappe.defaults.get_global_default("company")
	if company:
		return company

	company = frappe.db.get_value("Company", {}, "name")
	if not company:
		frappe.throw(_("Please configure a default Company before creating a quotation request."))

	return company


def _get_selling_prices(item_codes):
	item_codes = [item_code for item_code in item_codes if item_code]
	if not item_codes:
		return {}

	selling_price_list = _get_selling_price_list()

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
		if not current_price_record or price_record.price_list == selling_price_list:
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
	rfq_only_field = "custom_rfq_only" if item_group_meta.has_field("custom_rfq_only") else None
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
		if not rfq_only_field:
			return

	fields = ["name"]
	if image_field:
		fields.append(image_field)
	if rfq_only_field:
		fields.append(rfq_only_field)

	item_group_records = frappe.get_all(
		"Item Group",
		fields=fields,
		filters={"name": ["in", item_groups]},
		ignore_permissions=True,
		limit_page_length=len(item_groups),
	)
	item_group_images = {
		record.name: record.get(image_field)
		for record in item_group_records
		if image_field
	}
	item_group_rfq_flags = {
		record.name: record.get(rfq_only_field)
		for record in item_group_records
		if rfq_only_field
	}

	for item in items:
		if image_field:
			item.item_group_image = item_group_images.get(item.item_group)
		if rfq_only_field:
			item.custom_rfq_only = item_group_rfq_flags.get(item.item_group)


def _apply_item_attachments(items, max_attachments=2):
	item_names = [item.name for item in items if item.name]
	if not item_names or not frappe.db.exists("DocType", "File"):
		return

	file_rows = frappe.get_all(
		"File",
		fields=["attached_to_name", "file_url", "file_name"],
		filters={
			"attached_to_doctype": "Item",
			"attached_to_name": ["in", item_names],
			"is_folder": 0,
		},
		order_by="creation asc",
		ignore_permissions=True,
		limit_page_length=len(item_names) * max(max_attachments, 1) * 3,
	)

	attachments_by_item = {}
	for row in file_rows:
		item_name = row.attached_to_name
		file_url = row.file_url or row.file_name
		if not item_name or not file_url:
			continue

		item_attachments = attachments_by_item.setdefault(item_name, [])
		if any(attachment.get("file_url") == file_url for attachment in item_attachments):
			continue
		if len(item_attachments) >= max_attachments:
			continue

		item_attachments.append(
			{
				"file_url": file_url,
				"file_name": row.file_name or file_url.rsplit("/", 1)[-1],
			}
		)

	for item in items:
		item.attachments = attachments_by_item.get(item.name, [])


def _apply_item_variant_metadata(items):
	item_names = [item.name for item in items if item.name]
	if not item_names or not frappe.db.exists("DocType", "Item Variant Attribute"):
		return

	variant_attribute_rows = frappe.get_all(
		"Item Variant Attribute",
		fields=["parent", "attribute", "attribute_value", "idx"],
		filters={
			"parent": ["in", item_names],
			"parenttype": "Item",
		},
		order_by="parent asc, idx asc",
		ignore_permissions=True,
		limit_page_length=len(item_names) * 10,
	)

	attributes_by_item = {}
	for row in variant_attribute_rows:
		if not row.parent:
			continue

		attributes_by_item.setdefault(row.parent, []).append(
			{
				"attribute": row.attribute,
				"value": row.attribute_value,
			}
		)

	for item in items:
		item.variant_attributes = attributes_by_item.get(item.name, [])


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


def _row_matches_supplier(row, supplier=None):
	supplier = str(supplier or "").strip()
	if not supplier:
		return True

	row_supplier_candidates = [
		row.get("supplier"),
		row.get("supplier_name"),
		row.get("default_supplier"),
		row.get("custom_supplier"),
		row.get("custom_supplier_name"),
	]
	row_supplier_candidates = {str(value).strip() for value in row_supplier_candidates if value}
	if supplier in row_supplier_candidates:
		return True

	resolved_candidates = {
		_resolve_supplier_name(value)
		for value in row_supplier_candidates
		if value
	}
	return supplier in resolved_candidates


def _get_item_supplier_warehouse(item_doc, supplier=None):
	if not item_doc:
		return ""

	item_meta = item_doc.meta
	for df in item_meta.fields:
		if df.fieldtype != "Table" or not df.fieldname:
			continue
		if (
			df.fieldname not in ("supplier_list", "supplier_items")
			and df.options not in ("Supplier List", "Item Supplier")
			and df.label not in ("Supplier List", "Supplier Items")
		):
			continue

		for row in item_doc.get(df.fieldname) or []:
			if not _row_matches_supplier(row, supplier):
				continue
			if row.get("custom_supplier_warehouse"):
				return row.get("custom_supplier_warehouse")

	return ""


def _get_supplier_from_item_fields(item):
	for fieldname in ITEM_SUPPLIER_FIELDS:
		if item.get(fieldname):
			return item.get(fieldname)

	return ""


def _resolve_supplier_name(candidate_supplier):
	candidate_supplier = str(candidate_supplier or "").strip()
	if not candidate_supplier:
		return ""

	if frappe.db.exists("Supplier", candidate_supplier):
		return candidate_supplier

	return frappe.db.get_value("Supplier", {"supplier_name": candidate_supplier}, "name") or ""


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
		item.custom_google_address = supplier.get("custom_google_address")
		item.supplier_custom_google_address = supplier.get("custom_google_address")
		item.custom_latitude = supplier.get("custom_latitude")
		item.custom_longitude = supplier.get("custom_longitude")
		item.supplier_custom_latitude = supplier.get("custom_latitude")
		item.supplier_custom_longitude = supplier.get("custom_longitude")
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


def _find_supplier_website_profile_doctype():
	candidate_doctypes = (
		"Supplier Website Profile",
		"Website Supplier Profile",
	)

	for doctype_name in candidate_doctypes:
		if frappe.db.exists("DocType", doctype_name):
			return doctype_name

	return ""


def _get_product_supplier_name(product_id):
	product_id = (product_id or "").strip()
	if not product_id or not frappe.db.exists("DocType", "Item") or not frappe.db.exists("Item", product_id):
		return ""

	item_meta = frappe.get_meta("Item")
	item_fields = ["name"] + [
		fieldname
		for fieldname in ITEM_SUPPLIER_FIELDS
		if item_meta.has_field(fieldname)
	]
	item_records = frappe.get_all(
		"Item",
		fields=item_fields,
		filters={"name": product_id},
		ignore_permissions=True,
		limit_page_length=1,
	)
	item_record = item_records[0] if item_records else None
	if not item_record:
		return ""

	return _get_supplier_from_item_fields(item_record) or _get_item_supplier_links([product_id]).get(product_id) or ""


def _get_matching_supplier_website_profile_name(profile_doctype, supplier):
	supplier = (supplier or "").strip()
	if not profile_doctype or not supplier:
		return ""

	profile_meta = frappe.get_meta(profile_doctype)
	if frappe.db.exists(profile_doctype, supplier):
		return supplier

	supplier_record = _get_supplier_detail_record(supplier) or {}
	supplier_display_name = (
		supplier_record.get("supplier_name")
		or supplier
	)
	profile_filters = []

	for fieldname, fieldvalue in (
		("supplier", supplier_record.get("name") or supplier),
		("supplier_name", supplier_display_name),
		("title", supplier_display_name),
		("name", supplier_record.get("name") or supplier),
	):
		if fieldvalue and profile_meta.has_field(fieldname):
			profile_filters.append([fieldname, "=", fieldvalue])

	if not profile_filters:
		return ""

	profile_records = frappe.get_all(
		profile_doctype,
		fields=["name"],
		or_filters=profile_filters,
		ignore_permissions=True,
		limit_page_length=1,
	)

	return profile_records[0].name if profile_records else ""


def _pick_first_value(record, fieldnames, fallback=""):
	for fieldname in fieldnames:
		value = record.get(fieldname)
		if value not in (None, ""):
			return value

	return fallback


def _map_supplier_review_row(review_row):
	customer_name = _pick_first_value(
		review_row,
		("customer_name", "reviewer_name", "customer", "user_name", "full_name", "review_by"),
		"Anonymous",
	)
	rating = flt(
		_pick_first_value(
			review_row,
			("rating", "star_rating", "stars", "score", "value"),
			0,
		)
	)
	description = _pick_first_value(
		review_row,
		("description", "review", "comment", "message", "feedback", "remarks"),
		"",
	)

	return {
		"id": review_row.get("name") or frappe.generate_hash(length=10),
		"customerName": customer_name,
		"rating": max(0, min(5, int(round(rating)))),
		"description": description,
	}


def _get_reviews_table_field(profile_doctype):
	profile_meta = frappe.get_meta(profile_doctype)

	return next(
		(
			field
			for field in profile_meta.fields
			if field.fieldtype == "Table" and field.fieldname == "reviews"
		),
		None,
	)


def _review_row_matches_product(review_row, product_id):
	product_id = (product_id or "").strip()
	if not product_id:
		return True

	review_product_value = str(
		_pick_first_value(
			review_row,
			("product_id", "item_code", "item", "product", "product_code"),
			"",
		)
	).strip()

	if not review_product_value:
		return True

	return review_product_value == product_id


def _set_first_existing_value(target_doc, candidate_fields, value):
	if value in (None, ""):
		return False

	for fieldname in candidate_fields:
		if hasattr(target_doc, "meta") and target_doc.meta.has_field(fieldname):
			target_doc.set(fieldname, value)
			return True

	return False


def _get_current_reviewer_name():
	user_name = str(getattr(frappe.session, "user", "") or "").strip()
	if not user_name or user_name.lower() == "guest":
		return ""

	full_name = frappe.db.get_value("User", user_name, "full_name")
	if full_name:
		return full_name

	return user_name


def _find_existing_review_row(review_rows, order_name, product_id, reviewer_name):
	order_name = (order_name or "").strip()
	product_id = (product_id or "").strip()
	reviewer_name = (reviewer_name or "").strip()

	for review_row in review_rows or []:
		row_order_name = str(
			_pick_first_value(review_row, ("sales_order", "order_name", "sales_order_name", "reference_name"), "")
		).strip()
		row_product_id = str(
			_pick_first_value(review_row, ("product_id", "item_code", "item", "product", "product_code"), "")
		).strip()
		row_reviewer_name = str(
			_pick_first_value(review_row, ("customer_name", "reviewer_name", "customer", "user_name", "full_name", "review_by"), "")
		).strip()

		if row_order_name == order_name and row_product_id == product_id and row_reviewer_name == reviewer_name:
			return review_row

	return None


@frappe.whitelist(allow_guest=True)
def get_product_reviews(product_id=None, supplier=None):
	profile_doctype = _find_supplier_website_profile_doctype()
	if not profile_doctype:
		return []

	supplier = (supplier or "").strip() or _get_product_supplier_name((product_id or "").strip())
	if not supplier:
		return []

	profile_name = _get_matching_supplier_website_profile_name(profile_doctype, supplier)
	if not profile_name:
		return []

	profile_doc = frappe.get_doc(profile_doctype, profile_name)
	reviews_field = _get_reviews_table_field(profile_doctype)
	if not reviews_field:
		return []

	review_rows = [
		review_row
		for review_row in (profile_doc.get(reviews_field.fieldname) or [])
		if _review_row_matches_product(review_row, product_id)
	]

	return [
		mapped_review
		for mapped_review in (_map_supplier_review_row(review_row) for review_row in review_rows)
		if mapped_review.get("description") or mapped_review.get("rating") or mapped_review.get("customerName")
	]


@frappe.whitelist()
def add_product_review(order_name=None, product_id=None, rating=None, description=None):
	if _is_guest_session_user():
		frappe.throw("Please sign in to add a review.", frappe.AuthenticationError)

	order_name = (order_name or "").strip()
	product_id = (product_id or "").strip()
	description = (description or "").strip()
	rating = max(1, min(5, int(flt(rating))))

	if not order_name:
		frappe.throw("Order is required.")
	if not product_id:
		frappe.throw("Product is required.")
	if not description:
		frappe.throw("Review description is required.")
	if not frappe.db.exists("Sales Order", order_name):
		frappe.throw("Order was not found.")

	sales_order = frappe.get_doc("Sales Order", order_name)
	if not _can_view_sales_order(sales_order):
		frappe.throw("You are not allowed to review this order.")

	if not any((row.item_code or "").strip() == product_id for row in sales_order.items):
		frappe.throw("This product is not part of the selected order.")

	profile_doctype = _find_supplier_website_profile_doctype()
	if not profile_doctype:
		frappe.throw("Supplier Website Profile doctype was not found.")

	supplier = _get_product_supplier_name(product_id)
	if not supplier:
		frappe.throw("Supplier was not found for this product.")

	profile_name = _get_matching_supplier_website_profile_name(profile_doctype, supplier)
	if not profile_name:
		frappe.throw("Supplier Website Profile was not found for this supplier.")

	reviews_field = _get_reviews_table_field(profile_doctype)
	if not reviews_field:
		frappe.throw("Reviews section was not found in Supplier Website Profile.")

	profile_doc = frappe.get_doc(profile_doctype, profile_name)
	review_child_doctype = reviews_field.options
	reviewer_name = _get_current_reviewer_name() or sales_order.customer_name or sales_order.customer or frappe.session.user
	existing_review_row = _find_existing_review_row(
		profile_doc.get(reviews_field.fieldname) or [],
		order_name,
		product_id,
		reviewer_name,
	)

	review_row = existing_review_row or profile_doc.append(reviews_field.fieldname, {})
	if review_child_doctype and getattr(review_row, "doctype", "") != review_child_doctype:
		review_row.doctype = review_child_doctype

	_set_first_existing_value(review_row, ("customer_name", "reviewer_name", "customer", "full_name", "review_by"), reviewer_name)
	_set_first_existing_value(review_row, ("rating", "star_rating", "stars", "score", "value"), rating)
	_set_first_existing_value(review_row, ("description", "review", "comment", "message", "feedback", "remarks"), description)
	_set_first_existing_value(review_row, ("product_id", "item_code", "item", "product", "product_code"), product_id)
	_set_first_existing_value(review_row, ("sales_order", "order_name", "sales_order_name", "reference_name"), order_name)
	_set_first_existing_value(review_row, ("supplier",), supplier)
	_set_first_existing_value(review_row, ("review_date", "reviewed_on", "date"), today())

	profile_doc.save(ignore_permissions=True)

	return _map_supplier_review_row(review_row)


@frappe.whitelist()
def create_request_for_quotation(product_id=None, quantity=1, selected_size=None):
	if _is_guest_session_user():
		frappe.throw("Please sign in to request a quotation.", frappe.AuthenticationError)

	product_id = str(product_id or "").strip()
	selected_size = str(selected_size or "").strip()
	requested_qty = max(1, int(flt(quantity or 1)))

	if not product_id:
		frappe.throw("Product is required.")

	if not frappe.db.exists("Item", product_id):
		frappe.throw("Product was not found.")

	item_doc = frappe.get_doc("Item", product_id)
	item_group_meta = frappe.get_meta("Item Group")
	rfq_only_enabled = (
		item_group_meta.has_field("custom_rfq_only")
		and _is_truthy_flag(frappe.db.get_value("Item Group", item_doc.item_group, "custom_rfq_only"))
	)
	if not rfq_only_enabled:
		frappe.throw("This product is not configured for quotation requests.")

	supplier = (
		_resolve_supplier_name(_get_supplier_from_item_fields(item_doc))
		or _resolve_supplier_name(_get_item_supplier_links([item_doc.name]).get(item_doc.name))
	)
	if not supplier:
		frappe.throw("Supplier was not found for this product.")

	company = _get_default_company()
	request_warehouse = _get_item_supplier_warehouse(item_doc, supplier)
	if item_doc.is_stock_item and not request_warehouse:
		frappe.throw(
			_(
				"Please configure Custom Supplier Warehouse in the Supplier List for stock item {0} before creating a quotation request."
			).format(frappe.bold(item_doc.name))
		)
	item_description = item_doc.description or item_doc.item_name or item_doc.item_code or item_doc.name
	if selected_size:
		item_description = f"{item_description}\n\nSelected Size: {selected_size}"

	rfq_doc = frappe.get_doc(
		{
			"doctype": "Request for Quotation",
			"company": company,
			"transaction_date": today(),
			"message_for_supplier": _("Please share your best quotation for the requested item."),
			"suppliers": [
				{
					"doctype": "Request for Quotation Supplier",
					"supplier": supplier,
					"send_email": 0,
				}
			],
			"items": [
				{
					"doctype": "Request for Quotation Item",
					"item_code": item_doc.name,
					"item_name": item_doc.item_name or item_doc.name,
					"description": item_description,
					"item_group": item_doc.item_group,
					"brand": item_doc.brand,
					"qty": requested_qty,
					"uom": item_doc.stock_uom,
					"stock_uom": item_doc.stock_uom,
					"schedule_date": today(),
					"warehouse": request_warehouse or None,
				}
			],
		}
	)
	rfq_doc.insert(ignore_permissions=True)

	return {
		"name": rfq_doc.name,
		"supplier": supplier,
		"company": company,
	}


@frappe.whitelist(allow_guest=True)
def get_brands(limit_page_length=24, published=1):
	limit_page_length = frappe.utils.cint(limit_page_length) or 24

	if not frappe.db.exists("DocType", "Brand"):
		return []

	brand_fields = _get_existing_fields(
		"Brand",
		(
			"brand",
			"description",
			"image",
			"brand_image",
			"website_image",
			"logo",
			"brand_logo",
			"banner",
			"banner_image",
			"banner_2",
			"banner_3",
			"banner_image_2",
			"banner_image_3",
			"brand_banner",
			"brand_banner_image",
			"brand_banner_2",
			"brand_banner_3",
			"website_banner",
			"website_banner_image",
			"website_banner_2",
			"website_banner_3",
			"cover_image",
			"cover_photo",
			"custom_banner",
			"custom_banner_image",
			"custom_banner_2",
			"custom_banner_3",
			"custom_brand_banner",
			"custom_brand_banner_image",
			"custom_brand_banner_image_2",
			"custom_brand_banner_image_3",
			"custom_brand_banner_2",
			"custom_brand_banner_3",
			"custom_banner_image_2",
			"custom_banner_image_3",
			"brand_banner_image_2",
			"brand_banner_image_3",
			"website_banner_image_2",
			"website_banner_image_3",
			"custom_website_banner",
			"custom_website_banner_image",
			"custom_cover_image",
			"custom_cover_photo",
			"published",
			"disabled",
		),
	)
	fields = ["name"] + brand_fields
	filters = {}

	if "disabled" in brand_fields:
		filters["disabled"] = 0

	if _is_truthy_flag(published) and "published" in brand_fields:
		filters["published"] = 1

	return frappe.get_all(
		"Brand",
		fields=fields,
		filters=filters,
		ignore_permissions=True,
		order_by="modified desc",
		limit_page_length=limit_page_length,
	)


@frappe.whitelist()
def get_coupon_codes(limit_page_length=100):
	if frappe.session.user == "Guest":
		frappe.throw("Please sign in before using coupons.", frappe.AuthenticationError)

	if not frappe.db.exists("DocType", "Coupon Code"):
		return []

	limit_page_length = frappe.utils.cint(limit_page_length) or 100
	coupon_fields = _get_existing_fields(
		"Coupon Code",
		(
			"coupon_name",
			"coupon_code",
			"description",
			"valid_from",
			"valid_upto",
			"maximum_use",
			"used",
			"pricing_rule",
		),
	)
	coupon_records = frappe.get_all(
		"Coupon Code",
		fields=["name"] + coupon_fields,
		ignore_permissions=True,
		order_by="modified desc",
		limit_page_length=limit_page_length,
	)
	today_value = getdate(today())

	return [
		{
			"name": coupon.name,
			"coupon_name": coupon.get("coupon_name") or coupon.name,
			"coupon_code": coupon.get("coupon_code") or coupon.name,
			"description": coupon.get("description") or "",
			"pricing_rule": coupon.get("pricing_rule") or "",
		}
		for coupon in coupon_records
		if coupon.get("pricing_rule")
		and (not coupon.get("valid_from") or getdate(coupon.get("valid_from")) <= today_value)
		and (not coupon.get("valid_upto") or getdate(coupon.get("valid_upto")) >= today_value)
		and (
			not coupon.get("maximum_use")
			or flt(coupon.get("used")) < flt(coupon.get("maximum_use"))
		)
	]


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
			"store_image",
			"logo",
			"image",
			"website_image",
			"supplier_image",
			"supplier_logo",
			"custom_store_logo",
			"custom_supplier_logo",
			"banner_image",
			"banner",
			"store_banner",
			"store_banner_image",
			"store_cover",
			"store_cover_image",
			"cover_image",
			"cover_photo",
			"website_banner",
			"website_banner_image",
			"supplier_banner",
			"supplier_banner_image",
			"custom_banner_image",
			"custom_store_banner",
			"custom_store_banner_image",
			"custom_store_cover",
			"custom_store_cover_image",
			"custom_cover_image",
			"custom_cover_photo",
			"custom_website_banner",
			"custom_website_banner_image",
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
			"short_description",
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
	variant_of=None,
	brand=None,
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

	item_meta = frappe.get_meta("Item")
	filters = {"disabled": 0}
	or_filters = None

	if item:
		filters["name"] = item

	if variant_of and item_meta.has_field("variant_of"):
		filters["variant_of"] = variant_of

	if item_group:
		filters["item_group"] = item_group

	if brand:
		if not item_meta.has_field("brand"):
			return []
		filters["brand"] = brand

	if search:
		search_text = f"%{search}%"
		or_filters = [
			["item_name", "like", search_text],
			["item_code", "like", search_text],
			["description", "like", search_text],
		]

	publish_fields = _get_item_supplier_portal_publish_fields()
	optional_fields = [
		fieldname
	for fieldname in (
			"image",
			"website_image",
			"thumbnail",
			"brand",
			"has_variants",
			"variant_based_on",
			"variant_of",
			"custom_size",
			"custom_size_options",
			"custom_sizes",
			"custom_popular_items",
			"custom_delivery_slots",
			"custom_delivery_fee",
			"custom_available_qty",
			"custom_out_of_stock",
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
	_apply_item_attachments(items)
	_apply_item_variant_metadata(items)
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
	publish_fields = _get_item_group_publish_fields()

	item_groups = frappe.get_all(
		"Item Group",
		fields=["name"] + optional_fields + order_fields + publish_fields,
		ignore_permissions=True,
		order_by=_get_item_group_order_by(order_fields),
		limit_page_length=limit_page_length,
	)

	if _is_truthy_flag(published):
		item_groups = _filter_published_records(item_groups, publish_fields)

	return [
		item_group
		for item_group in item_groups
		if item_group.name != "All Item Groups"
	]


def _can_view_sales_order(sales_order):
	return frappe.session.user == "Administrator" or sales_order.owner == frappe.session.user


def _is_guest_session_user():
	user_name = str(getattr(frappe.session, "user", "") or "").strip()
	return not user_name or user_name.lower() in {"guest", "none", "null"}


def _get_purchase_order_names_for_sales_order(sales_order_name):
	return frappe.get_all(
		"Purchase Order Item",
		filters={"sales_order": sales_order_name, "docstatus": ["<", 2]},
		pluck="parent",
		ignore_permissions=True,
		order_by="creation asc",
	)


def _ensure_purchase_orders_for_sales_order(sales_order):
	if not sales_order or sales_order.docstatus != 1:
		return

	if _get_purchase_order_names_for_sales_order(sales_order.name):
		return

	try:
		from buy_in_minutes.payment import _create_purchase_orders_for_sales_order

		_create_purchase_orders_for_sales_order(sales_order)
	except Exception:
		frappe.log_error(
			title="Purchase Order Ensure Failed",
			message=f"Sales Order: {sales_order.name}\n\n{frappe.get_traceback()}",
		)


@frappe.whitelist(allow_guest=True, methods=["GET"])
def get_sales_order(sales_order_name):
	if _is_guest_session_user():
		frappe.throw("Please sign in to view this Sales Order.", frappe.AuthenticationError)

	if not sales_order_name:
		frappe.throw("Sales Order is required.")

	if not frappe.db.exists("Sales Order", sales_order_name):
		frappe.throw("Sales Order was not found.")

	sales_order = frappe.get_doc("Sales Order", sales_order_name)
	if not _can_view_sales_order(sales_order):
		frappe.throw("You are not allowed to view this Sales Order.")

	_ensure_purchase_orders_for_sales_order(sales_order)

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
		"delivery_date": sales_order.delivery_date,
		"delivery_slot": getattr(sales_order, "custom_delivery_slot", "") or "",
		"net_total": flt(sales_order.net_total),
		"total_taxes_and_charges": flt(sales_order.total_taxes_and_charges),
		"grand_total": flt(sales_order.grand_total),
		"currency": sales_order.currency or "AED",
		"customer_name": sales_order.customer_name or sales_order.customer,
		"shipping_address": sales_order.shipping_address or sales_order.address_display or "",
		"contact_display": sales_order.contact_display or "",
		"contact_mobile": sales_order.contact_mobile or "",
		"purchase_orders": list(dict.fromkeys(_get_purchase_order_names_for_sales_order(sales_order.name))),
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
def get_order_history(limit_page_length=20):
	from buy_in_minutes.order_history import get_order_history as get_history

	return get_history(limit_page_length=limit_page_length)


@frappe.whitelist()
def get_ordered_products(limit_page_length=40):
	limit_page_length = frappe.utils.cint(limit_page_length) or 40
	if _is_guest_session_user():
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
