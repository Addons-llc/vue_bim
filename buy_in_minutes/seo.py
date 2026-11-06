"""Server-rendered SEO tags for the Vue storefront.

The storefront is a client-side app, so without this every URL would ship the same
empty shell. `build_seo_head()` looks at the request path, loads the matching catalog
record (product, category, brand, store, supplier) and returns the <head> markup:
title, description, canonical, robots, Open Graph/Twitter tags and JSON-LD.
"""

import json
import re
from html import escape
from urllib.parse import quote, unquote

import frappe
from frappe.utils import cint, flt, strip_html

from buy_in_minutes import api
from buy_in_minutes.url_slug import SLUG_FIELD, get_slug, has_slug_field, resolve_name

APP_PREFIX = "/buy-in-minutes"
SITE_NAME = "Buy In Minutes"
DEFAULT_TITLE = "BUY IN MINUTES"
DEFAULT_DESCRIPTION = (
	"Order groceries, fresh produce and everyday essentials from local stores "
	"and get them delivered in minutes."
)
DEFAULT_IMAGE = "/assets/buy_in_minutes/buy-in-minutes/bim.jpeg"
DESCRIPTION_LIMIT = 160

# Pages behind login or with endless/thin content: crawlable links, but kept out of results.
NOINDEX_SECTIONS = {
	"cart",
	"wishlist",
	"profile",
	"addresses",
	"orders",
	"payment",
	"login",
	"search",
}

STATIC_PAGES = {
	"": (DEFAULT_TITLE, DEFAULT_DESCRIPTION),
	"categories": ("Shop by Category", "Browse every grocery and essentials category on Buy In Minutes."),
	"brands": ("Shop by Brand", "Find products from your favourite brands, delivered in minutes."),
	"stores": ("Local Stores", "Shop from trusted local stores and suppliers near you."),
	"essentials": ("Daily Essentials", "Everyday essentials delivered to your door in minutes."),
	"explore": ("Explore", "Discover new stores, trending picks and offers near you."),
	"services": ("Services", "Book trusted home and local services with Buy In Minutes."),
	"privacy-policy": ("Privacy Policy", "How Buy In Minutes collects and uses your data."),
	"terms-and-conditions": ("Terms & Conditions", "Terms of use for the Buy In Minutes store."),
}


def build_seo_page(request_path):
	"""SEO output for a storefront request path, as a dict:

	head      <head> tags (title, meta, canonical, Open Graph, JSON-LD)
	body      plain HTML for inside #app; Vue replaces it on mount, crawlers that do not
	          run JavaScript read it
	status    HTTP status code
	redirect  absolute URL when the page has moved (item-code product URL -> slug URL)
	"""
	seo = _resolve(_get_app_segments(request_path))
	redirect = seo.get("redirect")
	return {
		"head": _render_head(seo),
		"body": _render_body(seo),
		"status": seo.get("status", 200),
		"redirect": _canonical(redirect) if redirect else None,
	}


def _get_app_segments(request_path):
	path = (request_path or "/").split("?", 1)[0]
	if path.startswith(APP_PREFIX):
		path = path[len(APP_PREFIX) :]

	return [unquote(segment) for segment in path.strip("/").split("/") if segment]


def _resolve(segments):
	section = segments[0] if segments else ""
	key = segments[1] if len(segments) > 1 else ""
	path = "/" + "/".join(segments)

	if section in NOINDEX_SECTIONS:
		return {"title": DEFAULT_TITLE, "path": path, "noindex": True}

	if not key:
		if section not in STATIC_PAGES:
			return _not_found(path)
		heading, description = STATIC_PAGES[section]
		title = f"{heading} | {SITE_NAME}" if section else heading
		seo = {"title": title, "description": description, "path": path, "heading": heading}
		if not section:
			seo["heading"] = f"{SITE_NAME}: groceries and essentials delivered in minutes"
			seo["json_ld"] = _home_json_ld()
		if section in ("", "categories"):
			seo["links"] = _category_links()
		return seo

	if len(segments) > 2:
		return _not_found(path)

	resolver = {
		"products": _product_seo,
		"categories": _category_seo,
		"brands": _brand_seo,
		"stores": _store_seo,
		"suppliers": _supplier_seo,
	}.get(section)

	try:
		seo = resolver(key) if resolver else None
	except Exception:
		# SEO tags must never take the storefront down; fall back to the default shell.
		frappe.log_error(title="Buy In Minutes SEO tags failed")
		return {"title": DEFAULT_TITLE, "path": path}

	if not seo:
		return _not_found(path)

	seo.setdefault("path", path)
	return seo


def _not_found(path):
	return {"title": f"Page not found | {SITE_NAME}", "path": path, "noindex": True, "status": 404}


# ---------------------------------------------------------------------------
# Record resolvers
# ---------------------------------------------------------------------------


def _product_seo(product_key):
	# product_key is the readable slug, or the item code from links made before slugs.
	items = api.get_items(item=product_key, limit_page_length=1)
	if not items:
		return None

	item = items[0]
	product_path = _product_path(item)
	if product_path != f"/products/{product_key}":
		return {"redirect": product_path}
	name = item.get("item_name") or item.get("item_code") or item.get("name")
	description = _clean_description(item.get("description")) or (
		f"Buy {name} online at {SITE_NAME}. Fast delivery from local stores."
	)
	image = item.get("website_image") or item.get("image") or item.get("thumbnail")
	price = flt(item.get("selling_price") or item.get("price_list_rate"))
	currency = item.get("currency") or "AED"
	in_stock = not api._is_truthy_flag(item.get("custom_out_of_stock"))
	if item.get("custom_available_qty") not in (None, ""):
		in_stock = in_stock and flt(item.get("custom_available_qty")) > 0

	url = _canonical(product_path)
	product = {
		"@context": "https://schema.org",
		"@type": "Product",
		"name": name,
		"description": description,
		"sku": item.get("item_code") or item.get("name"),
		"url": url,
	}
	if image:
		product["image"] = [_absolute(image)]
	if item.get("brand"):
		product["brand"] = {"@type": "Brand", "name": item.get("brand")}
	if item.get("item_group"):
		product["category"] = item.get("item_group")
	if price > 0:
		product["offers"] = {
			"@type": "Offer",
			"url": url,
			"price": f"{price:.2f}",
			"priceCurrency": currency,
			"availability": "https://schema.org/InStock" if in_stock else "https://schema.org/OutOfStock",
			"itemCondition": "https://schema.org/NewCondition",
		}

	rating = _product_rating_json_ld(item)
	if rating:
		product.update(rating)

	crumbs = [("Home", "/")]
	if item.get("item_group"):
		crumbs.append((item.get("item_group"), f"/categories/{get_slug('Item Group', item.get('item_group'))}"))
	crumbs.append((name, product_path))

	return {
		"path": product_path,
		"heading": name,
		"body_text": _plain_text(item.get("description")),
		"facts": [
			value
			for value in (
				f"{currency} {price:.2f}" if price > 0 else "",
				"In stock" if in_stock else "Out of stock",
				f"Brand: {item.get('brand')}" if item.get("brand") else "",
				f"Sold by: {item.get('supplier')}" if item.get("supplier") else "",
			)
			if value
		],
		"crumbs": crumbs,
		"title": f"{name} | {SITE_NAME}",
		"description": description,
		"image": image,
		"og_type": "product",
		"price": (price, currency) if price > 0 else None,
		"json_ld": [product, _breadcrumbs(crumbs)],
	}


def _product_rating_json_ld(item):
	"""aggregateRating + review entries for the Product, from the reviews the page shows.

	Google requires the markup to match visible content, so this uses the same
	get_product_reviews() call the product page makes. Reviews live on the supplier's
	website profile, so they are cached briefly rather than read on every request."""
	from buy_in_minutes.catalog_cache import get_cached_catalog_value

	item_code = item.get("name")
	supplier = item.get("supplier") or ""
	try:
		reviews = get_cached_catalog_value(
			"seo_reviews",
			{"item": item_code, "supplier": supplier},
			lambda: api.get_product_reviews(product_id=item_code, supplier=supplier),
		)
	except Exception:
		frappe.log_error(title="Buy In Minutes SEO: product reviews failed")
		return None

	rated = [review for review in reviews or [] if cint(review.get("rating")) > 0]
	if not rated:
		return None

	average = sum(cint(review["rating"]) for review in rated) / len(rated)
	return {
		"aggregateRating": {
			"@type": "AggregateRating",
			"ratingValue": f"{average:.1f}",
			"reviewCount": len(rated),
			"bestRating": "5",
			"worstRating": "1",
		},
		"review": [
			{
				"@type": "Review",
				"author": {"@type": "Person", "name": review.get("customerName") or "Customer"},
				"reviewRating": {"@type": "Rating", "ratingValue": str(cint(review["rating"])), "bestRating": "5"},
				**({"reviewBody": _plain_text(review["description"])} if review.get("description") else {}),
			}
			# Google reads a handful; keep the page light.
			for review in rated[:5]
		],
	}


def _category_seo(category_key, section="categories"):
	# category_key is the readable slug, or the group name from links made before slugs.
	item_group = resolve_name("Item Group", category_key)
	if not item_group or item_group == "All Item Groups":
		return None

	publish_fields = api._get_item_group_publish_fields()
	fields = ["name"] + api._get_existing_fields(
		"Item Group",
		("item_group_name", "description", "image", "website_image", SLUG_FIELD) + tuple(publish_fields),
	)
	group = frappe.db.get_value("Item Group", item_group, fields, as_dict=True)
	if publish_fields and not any(api._is_truthy_flag(group.get(f)) for f in publish_fields):
		return None

	path = f"/{section}/{group.get(SLUG_FIELD) or group.name}"
	if path != f"/{section}/{category_key}":
		return {"redirect": path}

	name = group.get("item_group_name") or group.name
	crumbs = [("Home", "/"), ("Categories", "/categories"), (name, path)]
	return {
		"path": path,
		"heading": name,
		"body_text": _plain_text(group.get("description")),
		"crumbs": crumbs,
		"links": _product_links(item_group=group.name),
		"title": f"{name} - Shop Online | {SITE_NAME}",
		"description": _clean_description(group.get("description"))
		or f"Shop {name} online at {SITE_NAME}. Fresh stock from local stores, delivered in minutes.",
		"image": group.get("website_image") or group.get("image"),
		"json_ld": [_breadcrumbs(crumbs)],
	}


def _brand_seo(brand_key):
	# brand_key is the readable slug, or the brand name from links made before slugs.
	brand = api.get_brand(brand=brand_key)
	if not brand:
		return None

	path = f"/brands/{brand.get(SLUG_FIELD) or brand.get('name')}"
	if path != f"/brands/{brand_key}":
		return {"redirect": path}

	name = brand.get("brand") or brand.get("name")
	crumbs = [("Home", "/"), ("Brands", "/brands"), (name, path)]
	return {
		"path": path,
		"heading": f"{name} products",
		"body_text": _plain_text(brand.get("description")),
		"crumbs": crumbs,
		"links": _product_links(brand=brand.get("name")),
		"title": f"{name} Products | {SITE_NAME}",
		"description": _clean_description(brand.get("description"))
		or f"Shop {name} products online at {SITE_NAME}, delivered in minutes.",
		"image": brand.get("logo") or brand.get("image"),
		"json_ld": [_breadcrumbs(crumbs)],
	}


def _store_seo(store_identifier):
	store = api.get_supplier_store(supplier_store=store_identifier)
	if not store:
		# /stores/<x> is also used for category-style store listings.
		return _category_seo(store_identifier, section="stores")

	name = store.get("store_name") or store.get("name")
	description = _clean_description(
		store.get("short_description") or store.get("description") or store.get("about")
	) or f"Order from {name} on {SITE_NAME} and get it delivered in minutes."
	image = next(
		(store.get(f) for f in ("store_logo", "logo", "store_image", "image") if store.get(f)),
		None,
	)
	local_business = {
		"@context": "https://schema.org",
		"@type": "Store",
		"name": name,
		"description": description,
		"url": _canonical(f"/stores/{store_identifier}"),
	}
	if image:
		local_business["image"] = _absolute(image)
	if store.get("contact_number"):
		local_business["telephone"] = store.get("contact_number")

	crumbs = [("Home", "/"), ("Stores", "/stores"), (name, f"/stores/{store_identifier}")]
	return {
		"heading": name,
		"body_text": description,
		"crumbs": crumbs,
		"links": _product_links(supplier_store=store.get("name")),
		"title": f"{name} | {SITE_NAME}",
		"description": description,
		"image": image,
		"json_ld": [local_business, _breadcrumbs(crumbs)],
	}


def _supplier_seo(supplier_name):
	supplier = api.get_supplier_details(supplier_name)
	if not supplier:
		return None

	name = supplier.get("supplier_name") or supplier.get("name")
	return {
		"heading": name,
		"body_text": _plain_text(supplier.get("supplier_details")),
		"links": _product_links(supplier=supplier.get("name")),
		"title": f"{name} | {SITE_NAME}",
		"description": _clean_description(supplier.get("supplier_details"))
		or f"Shop products from {name} on {SITE_NAME}, delivered in minutes.",
		"image": supplier.get("supplier_logo") or supplier.get("image"),
	}


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


BODY_LINK_LIMIT = 48


def _product_links(**filters):
	"""(label, path) links to a listing's products, so crawlers reach every product page."""
	try:
		items = api.get_items(limit_page_length=BODY_LINK_LIMIT, **filters)
	except Exception:
		frappe.log_error(title="Buy In Minutes SEO: listing products failed")
		return []

	return [(item.get("item_name") or item.get("name"), _product_path(item)) for item in items]


def _category_links():
	"""Categories that hold published products: the same list the sitemap uses."""
	from buy_in_minutes.catalog_cache import get_cached_catalog_value

	try:
		paths = get_cached_catalog_value("sitemap", {}, _get_sitemap_paths)
	except Exception:
		frappe.log_error(title="Buy In Minutes SEO: categories failed")
		return []

	prefix = "/categories/"
	keys = [path[len(prefix) :] for path, _lastmod in paths if path.startswith(prefix)][:BODY_LINK_LIMIT]
	if not keys:
		return []

	# Paths hold slugs (or names for groups without one); show the group's display name.
	key_field = SLUG_FIELD if has_slug_field("Item Group") else "name"
	labels = {
		row.get(key_field): row.item_group_name or row.name
		for row in frappe.get_all(
			"Item Group",
			filters={key_field: ["in", keys]},
			fields=["name", "item_group_name", key_field],
		)
	}
	return [(labels.get(key) or key, f"{prefix}{key}") for key in keys]


def _product_path(item):
	"""Public URL path of a product: its readable slug, or the item code before slugs exist."""
	return f"/products/{item.get('custom_slug') or item.get('name')}"


def _home_json_ld():
	home = _absolute(f"{APP_PREFIX}/")
	return [
		{
			"@context": "https://schema.org",
			"@type": "Organization",
			"name": SITE_NAME,
			"url": home,
			"logo": _absolute(DEFAULT_IMAGE),
		},
		{
			"@context": "https://schema.org",
			"@type": "WebSite",
			"name": SITE_NAME,
			"url": home,
			"potentialAction": {
				"@type": "SearchAction",
				"target": {"@type": "EntryPoint", "urlTemplate": f"{home}search?q={{search_term_string}}"},
				"query-input": "required name=search_term_string",
			},
		},
	]


def _breadcrumbs(crumbs):
	return {
		"@context": "https://schema.org",
		"@type": "BreadcrumbList",
		"itemListElement": [
			{
				"@type": "ListItem",
				"position": index,
				"name": label,
				"item": _canonical(path),
			}
			for index, (label, path) in enumerate(crumbs, start=1)
		],
	}


BLOCK_TAG = re.compile(r"<\s*/?\s*(br|p|div|li|h[1-6]|tr|td|ul|ol)\b[^>]*>", re.IGNORECASE)


def _plain_text(text):
	# Break at block tags first so "<p>Storage</p><p>Keep cool</p>" doesn't run together.
	text = BLOCK_TAG.sub(" ", str(text or ""))
	return " ".join(strip_html(text).split())


def _clean_description(text):
	text = _plain_text(text)
	if len(text) <= DESCRIPTION_LIMIT:
		return text
	return text[: DESCRIPTION_LIMIT - 1].rsplit(" ", 1)[0] + "…"


def _origin():
	request = getattr(frappe.local, "request", None)
	if request is not None and request.host_url:
		return request.host_url.rstrip("/")
	return frappe.utils.get_url().rstrip("/")


def _absolute(url):
	url = str(url or "")
	if url.startswith(("http://", "https://")):
		return url
	return _origin() + "/" + url.lstrip("/")


def _canonical(path):
	return _absolute(APP_PREFIX + quote(path or "/", safe="/"))


def _render_head(seo):
	title = seo.get("title") or DEFAULT_TITLE
	description = seo.get("description") or DEFAULT_DESCRIPTION
	image = _absolute(seo.get("image") or DEFAULT_IMAGE)
	canonical = _canonical(seo.get("path") or "/")
	esc = lambda value: escape(str(value), quote=True)  # noqa: E731

	tags = [
		f"<title>{esc(title)}</title>",
		f'<meta name="description" content="{esc(description)}">',
	]

	if seo.get("noindex"):
		tags.append('<meta name="robots" content="noindex, follow">')
		return "\n    ".join(tags)

	tags += [
		f'<link rel="canonical" href="{esc(canonical)}">',
		f'<meta property="og:site_name" content="{SITE_NAME}">',
		f'<meta property="og:type" content="{esc(seo.get("og_type") or "website")}">',
		f'<meta property="og:title" content="{esc(title)}">',
		f'<meta property="og:description" content="{esc(description)}">',
		f'<meta property="og:url" content="{esc(canonical)}">',
		f'<meta property="og:image" content="{esc(image)}">',
		'<meta name="twitter:card" content="summary_large_image">',
		f'<meta name="twitter:title" content="{esc(title)}">',
		f'<meta name="twitter:description" content="{esc(description)}">',
		f'<meta name="twitter:image" content="{esc(image)}">',
	]

	if seo.get("price"):
		price, currency = seo["price"]
		tags += [
			f'<meta property="product:price:amount" content="{price:.2f}">',
			f'<meta property="product:price:currency" content="{esc(currency)}">',
		]

	for block in seo.get("json_ld") or []:
		# Escape "</" so record text can never close the script tag early.
		payload = json.dumps(block, ensure_ascii=False).replace("</", "<\\/")
		tags.append(f'<script type="application/ld+json">{payload}</script>')

	return "\n    ".join(tags)


# ---------------------------------------------------------------------------
# Sitemap
# ---------------------------------------------------------------------------

SITEMAP_STATIC_SECTIONS = ("", "categories", "brands", "stores", "essentials")
SITEMAP_LIMIT = 45000  # Google's cap is 50,000 URLs per sitemap file.


def get_sitemap_links():
	"""Storefront URLs for sitemap.xml: [{"loc", "lastmod"}]. Cached until the catalog changes."""
	from buy_in_minutes.catalog_cache import get_cached_catalog_value

	# Cache the site-relative paths only; the origin is added per request so each domain
	# gets its own absolute URLs.
	paths = get_cached_catalog_value("sitemap", {}, _get_sitemap_paths)
	return [{"loc": _canonical(path), "lastmod": lastmod} for path, lastmod in paths]


def _get_sitemap_paths():
	paths = [(f"/{section}" if section else "/", None) for section in SITEMAP_STATIC_SECTIONS]

	def add(section, name, modified=None):
		if name:
			# Raw paths; _canonical() URL-encodes them the same way as the page's canonical tag.
			paths.append((f"/{section}/{name}", _date(modified)))

	items = _published_items()
	for row in items:
		add("products", row.get("custom_slug") or row.name, row.modified)

	for row in _published_item_groups({row.item_group for row in items}):
		add("categories", row.get(SLUG_FIELD) or row.name, row.modified)

	for brand in api._get_brands(limit_page_length=SITEMAP_LIMIT, published=1):
		add("brands", brand.get(SLUG_FIELD) or brand.get("name"), brand.get("modified"))

	if frappe.db.exists("DocType", "Supplier Store"):
		for store in api._get_supplier_stores(limit_page_length=SITEMAP_LIMIT, published=1):
			add("stores", store.get("store_code") or store.get("name"))

	return paths[:SITEMAP_LIMIT]


def _published_items():
	if not frappe.get_meta("Item").has_field(api.ITEM_WEBSITE_PUBLISH_FIELD):
		return []

	return frappe.get_all(
		"Item",
		filters={"disabled": 0, api.ITEM_WEBSITE_PUBLISH_FIELD: 1},
		fields=["name", "item_group", "modified"]
		+ (["custom_slug"] if frappe.get_meta("Item").has_field("custom_slug") else []),
		order_by="modified desc",
		limit_page_length=SITEMAP_LIMIT,
	)


def _published_item_groups(item_groups_with_products):
	"""Published groups that hold at least one published product, directly or in a subgroup.

	Empty category pages are thin content, so they are left out of the sitemap."""
	if not item_groups_with_products:
		return []

	table = frappe.qb.DocType("Item Group")
	query = (
		frappe.qb.from_(table)
		.select(
			table.name,
			table.modified,
			table.lft,
			table.rgt,
			*([table[SLUG_FIELD]] if has_slug_field("Item Group") else []),
		)
		.where(table.name != "All Item Groups")
		.limit(SITEMAP_LIMIT)
	)
	publish_fields = api._get_item_group_publish_fields()
	if publish_fields:
		query = query.where(api._get_publish_criterion(table, "Item Group", publish_fields))

	groups = query.run(as_dict=True)
	product_positions = [
		row.lft
		for row in frappe.get_all(
			"Item Group",
			filters={"name": ["in", list(item_groups_with_products)]},
			fields=["lft"],
		)
	]

	return [
		group
		for group in groups
		if any(group.lft <= position <= group.rgt for position in product_positions)
	]


def _date(value):
	return f"{value:%Y-%m-%d}" if hasattr(value, "strftime") else None


def _render_body(seo):
	"""Plain, lightly styled HTML placed inside #app. Vue clears it when it mounts."""
	if seo.get("noindex") or not seo.get("heading"):
		return ""

	esc = lambda value: escape(str(value), quote=True)  # noqa: E731
	href = lambda path: esc(_canonical(path))  # noqa: E731
	parts = ['<div class="bim-ssr-fallback">']

	crumbs = seo.get("crumbs") or []
	if crumbs:
		parts.append(
			'<nav aria-label="Breadcrumb">'
			+ " &rsaquo; ".join(f'<a href="{href(path)}">{esc(label)}</a>' for label, path in crumbs)
			+ "</nav>"
		)

	parts.append(f"<h1>{esc(seo['heading'])}</h1>")

	if seo.get("image") and seo.get("og_type") == "product":
		parts.append(
			f'<img src="{esc(_absolute(seo["image"]))}" alt="{esc(seo["heading"])}" width="320" height="320">'
		)

	if seo.get("facts"):
		parts.append("<p>" + " &middot; ".join(esc(fact) for fact in seo["facts"]) + "</p>")

	if seo.get("body_text"):
		parts.append(f"<p>{esc(seo['body_text'])}</p>")

	links = seo.get("links") or []
	if links:
		parts.append(
			"<ul>" + "".join(f'<li><a href="{href(path)}">{esc(label)}</a></li>' for label, path in links) + "</ul>"
		)

	parts.append("</div>")
	return "".join(parts)
