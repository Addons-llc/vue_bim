"""Readable storefront URLs built from record names.

    /buy-in-minutes/products/amul-butter-500g     Item.custom_slug
    /buy-in-minutes/categories/fresh-fruits       Item Group.custom_slug
    /buy-in-minutes/brands/amul                   Brand.custom_slug

A slug is set once from the record's title and then left alone, so the URL stays stable
when the title is edited. Clear the field to regenerate it from the current title.

Lookups accept either the slug or the record name, so old name-based links keep working
(seo.py redirects them to the slug URL).
"""

import re
import unicodedata

import frappe

SLUG_FIELD = "custom_slug"
SLUG_MAX_LENGTH = 120

# doctype -> field holding the human title the slug is built from
SLUG_TITLE_FIELDS = {
	"Item": "item_name",
	"Item Group": "item_group_name",
	"Brand": "brand",
}


def slugify(text):
	text = unicodedata.normalize("NFKD", str(text or "")).encode("ascii", "ignore").decode()
	text = re.sub(r"[^a-z0-9]+", "-", text.lower()).strip("-")
	return text[:SLUG_MAX_LENGTH].rstrip("-")


def has_slug_field(doctype):
	return frappe.get_meta(doctype).has_field(SLUG_FIELD)


def _is_taken(doctype, slug, name):
	# Lookups match slug OR name, so a slug must not equal another record's name either.
	# (MariaDB compares these case-insensitively.)
	return bool(
		frappe.db.sql(
			f"""select name from `tab{doctype}`
			where (`{SLUG_FIELD}` = %(slug)s or name = %(slug)s) and name != %(name)s
			limit 1""",
			{"slug": slug, "name": name},
		)
	)


def make_unique_slug(doctype, base, name):
	base = base or "item"
	candidate = base
	suffix = 2
	while _is_taken(doctype, candidate, name):
		tail = f"-{suffix}"
		candidate = base[: SLUG_MAX_LENGTH - len(tail)].rstrip("-") + tail
		suffix += 1

	return candidate


def build_slug(doctype, doc):
	# Titles in non-Latin scripts slugify to nothing; fall back to the record name.
	title_field = SLUG_TITLE_FIELDS[doctype]
	base = (
		slugify(doc.get(SLUG_FIELD))
		or slugify(doc.get(title_field))
		or slugify(doc.get("item_code") or doc.get("name"))
	)
	return make_unique_slug(doctype, base, doc.get("name"))


def set_slug(doc, method=None):
	"""`validate` hook for Item, Item Group and Brand: fill in or normalise the slug."""
	if doc.doctype not in SLUG_TITLE_FIELDS or not has_slug_field(doc.doctype):
		return

	doc.set(SLUG_FIELD, build_slug(doc.doctype, doc))


def resolve_name(doctype, value):
	"""Record name for a slug or a name; None if neither matches. A slug match wins."""
	value = str(value or "").strip()
	if not value:
		return None

	if has_slug_field(doctype):
		name = frappe.db.get_value(doctype, {SLUG_FIELD: value}, "name")
		if name:
			return name

	return frappe.db.get_value(doctype, value, "name")


def get_slug(doctype, name):
	"""Public URL key for a record: its slug, or its name when it has none yet."""
	if name and has_slug_field(doctype):
		return frappe.db.get_value(doctype, name, SLUG_FIELD) or name
	return name


def get_item_code_for_slug(value):
	return resolve_name("Item", value)


def backfill_slugs(doctype):
	"""Give every record of `doctype` without a slug one. Safe to run repeatedly."""
	if not has_slug_field(doctype):
		return 0

	fields = list(dict.fromkeys(["name", SLUG_TITLE_FIELDS[doctype]] + (["item_code"] if doctype == "Item" else [])))
	# "is not set" matches both NULL and empty strings.
	records = frappe.get_all(
		doctype,
		filters={SLUG_FIELD: ["is", "not set"]},
		fields=fields,
		order_by="creation asc",
		limit_page_length=0,
	)

	# One at a time, so each new slug is visible to the uniqueness check for the next.
	for record in records:
		slug = build_slug(doctype, frappe._dict(record))
		frappe.db.set_value(doctype, record.name, SLUG_FIELD, slug, update_modified=False)

	return len(records)
