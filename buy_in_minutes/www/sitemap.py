# Overrides Frappe's /sitemap.xml: keeps every page Frappe lists (web pages, blogs, ...)
# and adds the storefront's products, categories, brands and stores.
import frappe
from frappe.www.sitemap import get_context as get_frappe_sitemap_context

from buy_in_minutes.seo import get_sitemap_links

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

	links.extend(link for link in frappe_links if link.get("loc") not in seen)
	return {"links": links}
