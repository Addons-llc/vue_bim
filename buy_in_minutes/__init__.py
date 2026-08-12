__version__ = "0.0.1"

import frappe


@frappe.whitelist(methods=["POST"])
def create_cash_on_delivery_order(cart_items=None, sales_order_name=None):
	from buy_in_minutes.payment import create_cash_on_delivery_order as create_order

	return create_order(cart_items=cart_items, sales_order_name=sales_order_name)
