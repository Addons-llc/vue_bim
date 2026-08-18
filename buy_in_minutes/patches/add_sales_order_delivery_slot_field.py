import frappe
from frappe.custom.doctype.custom_field.custom_field import create_custom_fields


def execute():
	create_custom_fields(
		{
			"Sales Order": [
				{
					"fieldname": "custom_delivery_slot",
					"label": "Delivery Slot",
					"fieldtype": "Data",
					"insert_after": "delivery_date",
					"allow_on_submit": 1,
				},
				{
					"fieldname": "custom_customer_location",
					"label": "Customer Location",
					"fieldtype": "Data",
					"insert_after": "custom_delivery_slot",
					"allow_on_submit": 1,
				}
			]
		},
		ignore_validate=frappe.flags.in_patch,
		update=True,
	)
