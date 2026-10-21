import hashlib

import frappe

CATALOG_CACHE_TTL = 300
CATALOG_CACHE_VERSION_KEY = "buy_in_minutes:catalog_cache_version"
CATALOG_FILE_DOCTYPES = ("Item", "Item Group", "Brand", "Supplier", "Supplier Store")


def _get_catalog_cache_version():
	version = frappe.cache.get_value(CATALOG_CACHE_VERSION_KEY)
	if not version:
		version = frappe.generate_hash(length=10)
		frappe.cache.set_value(CATALOG_CACHE_VERSION_KEY, version)

	return version


def _make_catalog_cache_key(namespace, params):
	params_hash = hashlib.sha1(frappe.as_json(params, indent=None).encode()).hexdigest()

	return f"buy_in_minutes:catalog:{_get_catalog_cache_version()}:{namespace}:{params_hash}"


def get_cached_catalog_value(namespace, params, generator, ttl=CATALOG_CACHE_TTL):
	# Catalog reads are the same for every shopper, so they are cached site-wide and dropped
	# all at once (by rotating the version in the key) whenever catalog data changes.
	cache_key = _make_catalog_cache_key(namespace, params)
	value = frappe.cache.get_value(cache_key)
	if value is None:
		value = generator()
		frappe.cache.set_value(cache_key, value, expires_in_sec=ttl)

	return value


def clear_catalog_cache(doc=None, method=None):
	frappe.cache.set_value(CATALOG_CACHE_VERSION_KEY, frappe.generate_hash(length=10))


def clear_catalog_cache_for_file(doc, method=None):
	if doc.get("attached_to_doctype") in CATALOG_FILE_DOCTYPES:
		clear_catalog_cache()
