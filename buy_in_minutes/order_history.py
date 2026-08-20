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
	items_by_order = {}

	for row in rows:
		items_by_order.setdefault(row.parent, []).append(
			{
				"item_code": row.item_code,
				"item_name": row.item_name or row.item_code,
				"description": row.description,
				"qty": flt(row.qty),
				"rate": flt(row.rate),
				"amount": flt(row.amount),
				"image": item_images.get(row.item_code),
			}
		)

	return items_by_order


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
			"purchase_orders": list(dict.fromkeys(_get_purchase_order_names_for_sales_order(sales_order.name))),
			"items": items_by_order.get(sales_order.name, []),
		}
		for sales_order in sales_orders
		if _can_view_sales_order(sales_order)
	]
