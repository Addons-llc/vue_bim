"""Web-sized WebP copies of catalog images.

Photos uploaded in ERPNext are often several MB. For each public JPEG/PNG attached to a
catalog record (Item, Item Group, Brand, Supplier, Supplier Store) this writes a sibling
file next to the original:

    /files/amul-butter.jpg  ->  /files/amul-butter.web.webp   (max 1000px, quality 80)

The original File is never modified. Catalog API rows pass through apply_web_images(),
which swaps in the .web.webp URL wherever one exists, so the storefront downloads the
small copy.

Existing images: bench --site <site> execute buy_in_minutes.image_optimizer.backfill
"""

import os

import frappe

from buy_in_minutes.catalog_cache import CATALOG_FILE_DOCTYPES, clear_catalog_cache

WEB_SUFFIX = ".web.webp"
MAX_DIMENSION = 1000
WEBP_QUALITY = 80
SOURCE_EXTENSIONS = (".jpg", ".jpeg", ".png")
PUBLIC_PREFIX = "/files/"


def _is_source_url(url):
	return (
		isinstance(url, str)
		and url.startswith(PUBLIC_PREFIX)
		and url.lower().endswith(SOURCE_EXTENSIONS)
		and ".." not in url
	)


def web_variant_url(url):
	return os.path.splitext(url)[0] + WEB_SUFFIX


def _disk_path(url):
	return frappe.get_site_path("public", "files", url[len(PUBLIC_PREFIX) :])


def web_image_url(url):
	"""The .web.webp copy of a /files/ image when it exists, else the URL unchanged."""
	if not _is_source_url(url):
		return url

	variant = web_variant_url(url)
	return variant if os.path.exists(_disk_path(variant)) else url


def apply_web_images(rows):
	"""Swap image URLs in API rows (dicts, nested lists of dicts) for their web copies."""
	for row in rows or []:
		if not isinstance(row, dict):
			continue
		for key, value in row.items():
			if isinstance(value, str):
				if _is_source_url(value):
					row[key] = web_image_url(value)
			elif isinstance(value, list):
				apply_web_images(value)

	return rows


def make_web_image(file_url):
	"""Write the .web.webp copy of a public image. Returns its URL, or None if skipped."""
	if not _is_source_url(file_url):
		return None

	from PIL import Image, ImageOps

	source = _disk_path(file_url)
	if not os.path.exists(source):
		return None

	target_url = web_variant_url(file_url)
	target = _disk_path(target_url)

	try:
		with Image.open(source) as image:
			image = ImageOps.exif_transpose(image)
			if image.mode not in ("RGB", "RGBA"):
				image = image.convert("RGBA" if "transparency" in image.info else "RGB")
			image.thumbnail((MAX_DIMENSION, MAX_DIMENSION))
			image.save(target, "WEBP", quality=WEBP_QUALITY, method=6)
	except Exception:
		frappe.log_error(title=f"Buy In Minutes: web image failed for {file_url}")
		return None

	# Small, already-compressed originals can come out larger; keep the original then.
	if os.path.getsize(target) >= os.path.getsize(source):
		os.remove(target)
		return None

	return target_url


def _is_catalog_image(doc):
	return (
		not doc.get("is_private")
		and doc.get("attached_to_doctype") in CATALOG_FILE_DOCTYPES
		and _is_source_url(doc.get("file_url"))
	)


def on_file_insert(doc, method=None):
	"""File after_insert: build the web copy in the background."""
	if _is_catalog_image(doc):
		frappe.enqueue(
			"buy_in_minutes.image_optimizer.make_web_image_and_refresh",
			file_url=doc.file_url,
			queue="short",
			enqueue_after_commit=True,
		)


def make_web_image_and_refresh(file_url):
	if make_web_image(file_url):
		clear_catalog_cache()


def on_file_trash(doc, method=None):
	"""File on_trash: remove the web copy with its original."""
	url = doc.get("file_url")
	if not _is_source_url(url):
		return

	# Another File row may share the same file on disk (Frappe dedupes uploads).
	if frappe.db.count("File", {"file_url": url, "name": ["!=", doc.name]}):
		return

	variant = _disk_path(web_variant_url(url))
	if os.path.exists(variant):
		os.remove(variant)


def backfill(force=False):
	"""Create web copies for existing catalog images. force=True rebuilds them all."""
	files = frappe.get_all(
		"File",
		filters={
			"is_private": 0,
			"is_folder": 0,
			"attached_to_doctype": ["in", list(CATALOG_FILE_DOCTYPES)],
		},
		fields=["file_url"],
		distinct=True,
		limit_page_length=0,
	)

	made = skipped = 0
	for row in files:
		url = row.file_url
		if not _is_source_url(url):
			continue
		if not force and os.path.exists(_disk_path(web_variant_url(url))):
			skipped += 1
			continue
		if make_web_image(url):
			made += 1

	clear_catalog_cache()
	print(f"Web images created: {made}, already present: {skipped}")
	return made
