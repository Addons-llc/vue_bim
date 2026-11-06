import frappe

from buy_in_minutes.seo import build_seo_head

# Every /buy-in-minutes/* URL renders this one page (website_route_rules), and Frappe's
# page cache is keyed on the resolved page, not the URL, so caching would serve one
# product's tags for every product.
no_cache = 1


def get_context(context):
	request = getattr(frappe.local, "request", None)
	seo_head, status_code, redirect_url = build_seo_head(request.path if request else "/")

	if redirect_url:
		# Old /products/<item_code> links: move them (and their ranking) to the slug URL.
		query = request.query_string.decode() if request and request.query_string else ""
		frappe.flags.redirect_location = f"{redirect_url}?{query}" if query else redirect_url
		raise frappe.Redirect(301)

	context.seo_head = seo_head
	if status_code != 200:
		context.http_status_code = status_code
