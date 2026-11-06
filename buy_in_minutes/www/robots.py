# Overrides Frappe's /robots.txt. Text saved in Website Settings > Robots.txt is still
# included, below the storefront rules.
import frappe

from buy_in_minutes.seo import APP_PREFIX, NOINDEX_SECTIONS, _absolute

no_cache = 1
base_template_path = "www/robots.txt"

# /api and /files stay crawlable: Google renders the Vue app, which loads data and images from them.
DISALLOWED_PATHS = ["/app", "/desk", "/login", "/update-password"] + [
	f"{APP_PREFIX}/{section}" for section in sorted(NOINDEX_SECTIONS)
]


def get_context(context):
	lines = ["User-agent: *"]
	lines += [f"Disallow: {path}" for path in DISALLOWED_PATHS]
	lines += ["Allow: /", "", f"Sitemap: {_absolute('/sitemap.xml')}"]

	custom = (frappe.db.get_single_value("Website Settings", "robots_txt") or "").strip()
	if custom:
		lines += ["", "# From Website Settings", custom]

	return {"robots_txt": "\n".join(lines) + "\n"}
