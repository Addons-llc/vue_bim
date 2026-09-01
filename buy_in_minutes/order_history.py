import frappe
from frappe.utils import flt


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

		_create_purchase_orders_for_sales_order(frappe.get_doc("Sales Order", sales_order.name))
	except Exception:
		frappe.log_error(
			title="Purchase Order Ensure Failed",
			message=f"Sales Order: {sales_order.name}\n\n{frappe.get_traceback()}",
		)


def _get_item_images(item_codes):
	item_codes = [item_code for item_code in item_codes if item_code]
	if not item_codes:
		return {}

	item_meta = frappe.get_meta("Item")
	image_fields = [
		fieldname
		for fieldname in ("image", "website_image", "thumbnail")
		if item_meta.has_field(fieldname)
	]
	if not image_fields:
		return {}

	item_records = frappe.get_all(
		"Item",
		fields=["name"] + image_fields,
		filters={"name": ["in", item_codes]},
		ignore_permissions=True,
		limit_page_length=len(item_codes),
	)

	return {
		item.name: next((item.get(fieldname) for fieldname in image_fields if item.get(fieldname)), "")
		for item in item_records
	}


def _get_submitted_reviews_by_order_item(rows):
	if not rows:
		return {}

	from buy_in_minutes import api as review_api

	profile_doctype = review_api._find_supplier_website_profile_doctype()
	reviewer_name = review_api._get_current_reviewer_name()
	if not profile_doctype or not reviewer_name:
		return {}

	reviews_by_key = {}
	supplier_profiles = {}
	product_ids = list({row.item_code for row in rows if row.item_code})

	for product_id in product_ids:
		supplier = review_api._get_product_supplier_name(product_id)
		if not supplier:
			continue

		profile_name = supplier_profiles.get(supplier)
		if profile_name is None:
			profile_name = review_api._get_matching_supplier_website_profile_name(profile_doctype, supplier)
			supplier_profiles[supplier] = profile_name or ""

		if not profile_name:
			continue

		reviews_field = review_api._get_reviews_table_field(profile_doctype)
		if not reviews_field:
			continue

		profile_doc = frappe.get_doc(profile_doctype, profile_name)
		for review_row in profile_doc.get(reviews_field.fieldname) or []:
			product_code = str(
				review_api._pick_first_value(
					review_row,
					("product_id", "item_code", "item", "product", "product_code"),
					"",
				)
			).strip()
			order_name = str(
				review_api._pick_first_value(
					review_row,
					("sales_order", "order_name", "sales_order_name", "reference_name"),
					"",
				)
			).strip()
			row_reviewer_name = str(
				review_api._pick_first_value(
					review_row,
					("customer_name", "reviewer_name", "customer", "user_name", "full_name", "review_by"),
					"",
				)
			).strip()

			if not product_code or not order_name or row_reviewer_name != reviewer_name:
				continue

			reviews_by_key[f"{order_name}::{product_code}"] = review_api._map_supplier_review_row(review_row)

	return reviews_by_key


def _get_order_items(sales_order_names):
	if not sales_order_names:
		return {}

	rows = frappe.get_all(
		"Sales Order Item",
		fields=["parent", "item_code", "item_name", "description", "qty", "rate", "amount"],
		filters={"parent": ["in", sales_order_names]},
		order_by="idx asc",
		ignore_permissions=True,
		limit_page_length=0,
	)
	item_images = _get_item_images(list({row.item_code for row in rows if row.item_code}))
	submitted_reviews = _get_submitted_reviews_by_order_item(rows)
	items_by_order = {}

	for row in rows:
		review_key = f"{row.parent}::{row.item_code}"
		items_by_order.setdefault(row.parent, []).append(
			{
				"id": row.item_code,
				"product_id": row.item_code,
				"item_code": row.item_code,
				"item_name": row.item_name or row.item_code,
				"description": row.description,
				"qty": flt(row.qty),
				"rate": flt(row.rate),
				"amount": flt(row.amount),
				"image": item_images.get(row.item_code),
				"submitted_review": submitted_reviews.get(review_key),
			}
		)

	return items_by_order


def _get_customer_names(customer_ids):
	customer_ids = [customer_id for customer_id in customer_ids if customer_id]
	if not customer_ids:
		return {}

	customer_rows = frappe.get_all(
		"Customer",
		fields=["name", "customer_name"],
		filters={"name": ["in", customer_ids]},
		ignore_permissions=True,
		limit_page_length=len(customer_ids),
	)

	return {
		customer.name: customer.customer_name or customer.name
		for customer in customer_rows
	}


@frappe.whitelist()
def get_order_history(limit_page_length=20):
	limit_page_length = frappe.utils.cint(limit_page_length) or 20
	if _is_guest_session_user():
		frappe.throw("Please sign in to view order history.", frappe.AuthenticationError)

	filters = {
		"docstatus": 1,
		"owner": frappe.session.user,
	}

	sales_orders = frappe.get_all(
		"Sales Order",
		fields=[
			"name",
			"status",
			"transaction_date",
			"grand_total",
			"currency",
			"owner",
			"customer",
		],
		filters=filters,
		order_by="transaction_date desc, creation desc",
		ignore_permissions=True,
		limit_page_length=limit_page_length,
	)
	if not sales_orders:
		return []

	items_by_order = _get_order_items([sales_order.name for sales_order in sales_orders])
	customer_names = _get_customer_names([sales_order.customer for sales_order in sales_orders])
	for sales_order in sales_orders:
		if _can_view_sales_order(sales_order):
			_ensure_purchase_orders_for_sales_order(sales_order)

	return [
		{
			"name": sales_order.name,
			"status": sales_order.status,
			"transaction_date": sales_order.transaction_date,
			"grand_total": flt(sales_order.grand_total),
			"currency": sales_order.currency or "AED",
			"customer": sales_order.customer or "",
			"customer_name": customer_names.get(sales_order.customer) or sales_order.customer or "",
			"purchase_orders": list(dict.fromkeys(_get_purchase_order_names_for_sales_order(sales_order.name))),
			"items": items_by_order.get(sales_order.name, []),
		}
		for sales_order in sales_orders
		if _can_view_sales_order(sales_order)
	]
