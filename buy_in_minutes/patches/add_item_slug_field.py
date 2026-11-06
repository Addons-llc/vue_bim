import frappe
from frappe.custom.doctype.custom_field.custom_field import create_custom_fields

from buy_in_minutes.catalog_cache import clear_catalog_cache
from buy_in_minutes.product_slug import backfill_item_slugs

ITEM_SLUG_FIELD = {
	"fieldname": "custom_slug",
	"label": "URL Slug",
	"fieldtype": "Data",
	"insert_after": "custom_published",
	"unique": 1,
	"no_copy": 1,
	"search_index": 1,
	"description": "Readable product URL on the Buy In Minutes website, e.g. amul-butter-500g. "
	"Filled in from the item name; clear it to regenerate.",
}


def execute():
	# Fixtures sync after patches, so create the field here before backfilling it.
	create_custom_fields({"Item": [ITEM_SLUG_FIELD]}, ignore_validate=frappe.flags.in_patch, update=True)
	frappe.clear_cache(doctype="Item")
	backfill_item_slugs()
	clear_catalog_cache()
