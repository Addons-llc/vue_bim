# Overrides Frappe's /sitemap.xml: keeps every page Frappe lists (web pages, blogs, ...)
# and adds the storefront's products, categories, brands and stores.
from urllib.parse import urlsplit, urlunsplit

import frappe
from frappe.www.sitemap import get_context as get_frappe_sitemap_context

from buy_in_minutes.seo import _absolute, get_sitemap_links

no_cache = 1
base_template_path = "www/sitemap.xml"


def get_context(context):
	links = get_sitemap_links()
	seen = {link["loc"] for link in links}

	try:
		frappe_links = get_frappe_sitemap_context(context).get("links") or []
	except Exception:
		frappe.log_error(title="Buy In Minutes: Frappe sitemap links failed")
		frappe_links = []

	# Frappe builds its links from the site's default host (e.g. *.frappe.cloud); Google
	# ignores sitemap URLs on another host, so serve them on the domain being visited.
	for link in frappe_links:
		link["loc"] = _on_request_origin(link.get("loc"))
		if link["loc"] and link["loc"] not in seen:
			seen.add(link["loc"])
			links.append(link)

	return {"links": links}


def _on_request_origin(url):
	if not url:
		return url
	parts = urlsplit(url)
	return _absolute(urlunsplit(("", "", parts.path or "/", parts.query, parts.fragment)))
