import frappe
from frappe.custom.doctype.custom_field.custom_field import create_custom_fields

from buy_in_minutes.catalog_cache import clear_catalog_cache
from buy_in_minutes.url_slug import backfill_slugs


def _slug_field(insert_after, example):
	return {
		"fieldname": "custom_slug",
		"label": "URL Slug",
		"fieldtype": "Data",
		"insert_after": insert_after,
		"unique": 1,
		"no_copy": 1,
		"search_index": 1,
		"description": f"Readable URL on the Buy In Minutes website, e.g. {example}. "
		"Filled in from the name; clear it to regenerate.",
	}


def execute():
	# Fixtures sync after patches, so create the fields here before backfilling them.
	create_custom_fields(
		{
			"Item Group": [_slug_field("item_group_name", "fresh-fruits")],
			"Brand": [_slug_field("brand", "amul")],
		},
		ignore_validate=frappe.flags.in_patch,
		update=True,
	)
	for doctype in ("Item Group", "Brand"):
		frappe.clear_cache(doctype=doctype)
		backfill_slugs(doctype)
	clear_catalog_cache()
