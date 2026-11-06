"""Readable product URLs: /buy-in-minutes/products/<slug>.

Each Item gets a unique `custom_slug` built from its item name (e.g. "amul-butter-500g").
The slug is set once and then left alone, so a product's URL stays stable when its name
is edited. Clear the field to have it regenerated from the current name.

Lookups accept either the slug or the item code, so old /products/<item_code> links keep
working (seo.py redirects them to the slug URL).
"""

import re
import unicodedata

import frappe

SLUG_FIELD = "custom_slug"
SLUG_MAX_LENGTH = 120


def slugify(text):
	text = unicodedata.normalize("NFKD", str(text or "")).encode("ascii", "ignore").decode()
	text = re.sub(r"[^a-z0-9]+", "-", text.lower()).strip("-")
	return text[:SLUG_MAX_LENGTH].rstrip("-")


def has_slug_field():
	return frappe.get_meta("Item").has_field(SLUG_FIELD)


def _is_taken(slug, item_name):
	# The storefront looks products up by slug OR item code, so a slug must not match
	# another item's code either. (MariaDB compares these case-insensitively.)
	return bool(
		frappe.db.sql(
			"""select name from `tabItem`
			where (`custom_slug` = %(slug)s or name = %(slug)s) and name != %(item)s
			limit 1""",
			{"slug": slug, "item": item_name},
		)
	)


def make_unique_slug(base, item_name):
	base = base or "product"
	candidate = base
	suffix = 2
	while _is_taken(candidate, item_name):
		tail = f"-{suffix}"
		candidate = base[: SLUG_MAX_LENGTH - len(tail)].rstrip("-") + tail
		suffix += 1

	return candidate


def build_slug(doc):
	# Names in non-Latin scripts slugify to nothing; fall back to the item code.
	base = slugify(doc.get(SLUG_FIELD)) or slugify(doc.get("item_name")) or slugify(
		doc.get("item_code") or doc.name
	)
	return make_unique_slug(base, doc.name)


def set_item_slug(doc, method=None):
	"""Item `validate` hook: fill in (or normalise a hand-edited) slug."""
	if not has_slug_field():
		return

	doc.set(SLUG_FIELD, build_slug(doc))


def get_item_code_for_slug(value):
	"""Resolve a slug or item code to the item code, or None."""
	value = str(value or "").strip()
	if not value:
		return None

	if has_slug_field():
		item_code = frappe.db.get_value("Item", {SLUG_FIELD: value}, "name")
		if item_code:
			return item_code

	return frappe.db.get_value("Item", value, "name")


def backfill_item_slugs():
	"""Give every Item without a slug one. Safe to run repeatedly."""
	if not has_slug_field():
		return 0

	# "is not set" matches both NULL and empty strings.
	items = frappe.get_all(
		"Item",
		filters={SLUG_FIELD: ["is", "not set"]},
		fields=["name", "item_code", "item_name"],
		order_by="creation asc",
		limit_page_length=0,
	)

	# One at a time, so each new slug is visible to the uniqueness check for the next.
	for item in items:
		slug = build_slug(frappe._dict(item))
		frappe.db.set_value("Item", item.name, SLUG_FIELD, slug, update_modified=False)

	return len(items)
