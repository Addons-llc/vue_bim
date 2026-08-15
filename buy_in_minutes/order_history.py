import frappe
from frappe.utils import flt


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


def _get_purchase_order_names_for_sales_order(sales_order_name):
	return frappe.get_all(
		"Purchase Order Item",
		filters={"sales_order": sales_order_name, "docstatus": ["<", 2]},
		pluck="parent",
		ignore_permissions=True,
		order_by="creation asc",
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
	if frappe.session.user == "Guest":
		frappe.throw("Please sign in to view order history.", frappe.AuthenticationError)

	customer = _get_customer_for_user(frappe.session.user)
	filters = {
		"docstatus": 1,
	}
	if customer:
		filters["customer"] = customer
	else:
		filters["owner"] = frappe.session.user

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
