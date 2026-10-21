import frappe

# Columns the storefront filters on that ERPNext does not index by default. Fields are skipped when
# the doctype or column does not exist on this site, so this is safe to run on every migrate.
CATALOG_INDEXES = (
	("Item", ("brand",)),
	("Item", ("published_in_supplier_portal",)),
	("Item", ("custom_published_in_supplier_portal",)),
	("Item Supplier", ("supplier",)),
	("Brand", ("custom_published",)),
	("Brand", ("published",)),
	("Supplier Store", ("store_code",)),
	("Supplier Store", ("supplier",)),
	("Supplier Store", ("published",)),
)


def ensure_catalog_indexes():
	for doctype, fields in CATALOG_INDEXES:
		if not frappe.db.exists("DocType", doctype):
			continue

		table_columns = frappe.db.get_table_columns(doctype)
		if all(fieldname in table_columns for fieldname in fields):
			frappe.db.add_index(doctype, list(fields))
