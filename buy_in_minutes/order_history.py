import frappe
from frappe.utils import flt


def _can_view_sales_order(sales_order):
	return frappe.session.user == "Administrator" or sales_order.owner == frappe.session.user


def _can_view_request_for_quotation(request_for_quotation):
	return (
		frappe.session.user == "Administrator"
		or request_for_quotation.owner == frappe.session.user
	)


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
				"id": row.item_code,
				"product_id": row.item_code,
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


def _get_supplier_quotation_items(quotation_names):
	if not quotation_names:
		return {}

	rows = frappe.get_all(
		"Supplier Quotation Item",
		fields=["parent", "item_code", "item_name", "description", "qty", "rate", "amount"],
		filters={"parent": ["in", quotation_names]},
		order_by="idx asc",
		ignore_permissions=True,
		limit_page_length=0,
	)
	item_images = _get_item_images(list({row.item_code for row in rows if row.item_code}))
	items_by_quotation = {}

	for row in rows:
		items_by_quotation.setdefault(row.parent, []).append(
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
			}
		)

	return items_by_quotation


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


def _get_existing_fields(doctype, fieldnames):
	meta = frappe.get_meta(doctype)
	return [fieldname for fieldname in fieldnames if fieldname == "name" or meta.has_field(fieldname)]


def _build_address_display_from_doc(address_name):
	address_name = str(address_name or "").strip()
	if not address_name or not frappe.db.exists("Address", address_name):
		return ""

	address_doc = frappe.get_doc("Address", address_name)
	lines = [
		str(address_doc.get("address_title") or "").strip(),
		str(address_doc.get("address_line1") or "").strip(),
		str(address_doc.get("address_line2") or "").strip(),
		str(address_doc.get("address_line3") or "").strip(),
		", ".join(
			part
			for part in [
				str(address_doc.get("city") or "").strip(),
				str(address_doc.get("state") or "").strip(),
				str(address_doc.get("country") or "").strip(),
			]
			if part
		),
	]
	phone = str(address_doc.get("phone") or "").strip()
	if phone:
		lines.append(phone)

	return "\n".join(line for line in lines if line)


def _get_contact_summary(contact_name):
	contact_name = str(contact_name or "").strip()
	if not contact_name or not frappe.db.exists("Contact", contact_name):
		return {
			"display": "",
			"mobile": "",
			"email": "",
		}

	contact_doc = frappe.get_doc("Contact", contact_name)
	contact_mobile = str(contact_doc.get("mobile_no") or contact_doc.get("phone") or "").strip()
	if not contact_mobile:
		contact_mobile = str(
			frappe.db.get_value(
				"Contact Phone",
				{"parent": contact_name, "is_primary_mobile_no": 1},
				"phone",
			)
			or frappe.db.get_value(
				"Contact Phone",
				{"parent": contact_name, "is_primary_phone": 1},
				"phone",
			)
			or ""
		).strip()

	contact_email = str(contact_doc.get("email_id") or "").strip()
	if not contact_email:
		contact_email = str(
			frappe.db.get_value(
				"Contact Email",
				{"parent": contact_name, "is_primary": 1},
				"email_id",
			)
			or ""
		).strip()

	return {
		"display": str(contact_doc.get("full_name") or contact_doc.get("first_name") or "").strip(),
		"mobile": contact_mobile,
		"email": contact_email,
	}


def _get_supplier_quotations_for_user(limit_page_length):
	request_for_quotation_names = frappe.get_all(
		"Request for Quotation",
		filters={"docstatus": 1, "owner": frappe.session.user},
		pluck="name",
		ignore_permissions=True,
		limit_page_length=0,
	)
	if not request_for_quotation_names:
		return []

	supplier_quotation_names = frappe.get_all(
		"Supplier Quotation Item",
		filters={"request_for_quotation": ["in", request_for_quotation_names], "docstatus": ["<", 2]},
		pluck="parent",
		ignore_permissions=True,
		limit_page_length=0,
	)
	supplier_quotation_names = list(dict.fromkeys(filter(None, supplier_quotation_names)))
	if not supplier_quotation_names:
		return []

	supplier_quotation_fields = _get_existing_fields(
		"Supplier Quotation",
		[
			"name",
			"supplier",
			"supplier_name",
			"status",
			"transaction_date",
			"valid_till",
			"grand_total",
			"currency",
			"company",
		],
	)
	return frappe.get_all(
		"Supplier Quotation",
		fields=supplier_quotation_fields,
		filters={
			"name": ["in", supplier_quotation_names],
			"docstatus": 1,
		},
		order_by="transaction_date desc, creation desc",
		ignore_permissions=True,
		limit_page_length=limit_page_length,
	)


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
	supplier_quotations = _get_supplier_quotations_for_user(limit_page_length)

	if not sales_orders and not supplier_quotations:
		return []

	items_by_order = _get_order_items([sales_order.name for sales_order in sales_orders])
	items_by_supplier_quotation = _get_supplier_quotation_items(
		[supplier_quotation.name for supplier_quotation in supplier_quotations]
	)
	customer_names = _get_customer_names([sales_order.customer for sales_order in sales_orders])
	for sales_order in sales_orders:
		if _can_view_sales_order(sales_order):
			_ensure_purchase_orders_for_sales_order(sales_order)

	history_entries = [
		{
			"name": sales_order.name,
			"history_type": "sales_order",
			"title": sales_order.name,
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

	for supplier_quotation in supplier_quotations:
		history_entries.append(
			{
				"name": supplier_quotation.name,
				"history_type": "supplier_quotation",
				"title": supplier_quotation.name,
				"status": supplier_quotation.status,
				"transaction_date": supplier_quotation.transaction_date,
				"valid_till": supplier_quotation.get("valid_till"),
				"grand_total": flt(supplier_quotation.get("grand_total")),
				"currency": supplier_quotation.get("currency") or "AED",
				"customer": "",
				"customer_name": "",
				"purchase_orders": [],
				"items": items_by_supplier_quotation.get(supplier_quotation.name, []),
				"company": supplier_quotation.get("company") or "",
				"supplier": supplier_quotation.get("supplier") or "",
				"supplier_name": supplier_quotation.get("supplier_name") or supplier_quotation.get("supplier") or "",
			}
		)

	return sorted(
		history_entries,
		key=lambda entry: (
			str(entry.get("transaction_date") or ""),
			str(entry.get("name") or ""),
		),
		reverse=True,
	)[:limit_page_length]
