import frappe

from buy_in_minutes.seo import build_seo_page

# Every /buy-in-minutes/* URL renders this one page (website_route_rules), and Frappe's
# page cache is keyed on the resolved page, not the URL, so caching would serve one
# product's tags for every product.
no_cache = 1


def get_context(context):
	request = getattr(frappe.local, "request", None)
	page = build_seo_page(request.path if request else "/")

	if page["redirect"]:
		# Old /products/<item_code> links: move them (and their ranking) to the slug URL.
		query = request.query_string.decode() if request and request.query_string else ""
		frappe.flags.redirect_location = f"{page['redirect']}?{query}" if query else page["redirect"]
		raise frappe.Redirect(301)

	context.seo_head = page["head"]
	context.seo_body = page["body"]
	if page["status"] != 200:
		context.http_status_code = page["status"]
