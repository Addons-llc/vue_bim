"""Google Analytics 4 tag for the storefront page.

Set the measurement ID per site (dev and staging sites stay untracked):

    bench --site <site> set-config buy_in_minutes_ga_measurement_id G-XXXXXXXXXX

The frontend (frontend/src/analytics) sends page views and ecommerce events through the
gtag() defined here. Consent Mode v2 starts every storage type "denied"; the cookie banner
grants analytics_storage when the visitor accepts. Ads storage is never granted.
"""

import json
import re

import frappe

CONFIG_KEY = "buy_in_minutes_ga_measurement_id"
MEASUREMENT_ID = re.compile(r"^G-[A-Z0-9]{4,20}$")


def get_measurement_id():
	value = str(frappe.conf.get(CONFIG_KEY) or "").strip().upper()
	return value if MEASUREMENT_ID.match(value) else ""


def get_analytics_head():
	measurement_id = get_measurement_id()
	if not measurement_id:
		return ""

	ga_id = json.dumps(measurement_id)
	return f"""<script>
      window.BIM_GA_ID = {ga_id};
      window.dataLayer = window.dataLayer || [];
      function gtag() {{ dataLayer.push(arguments); }}
      (function () {{
        var choice = null;
        try {{ choice = localStorage.getItem("bim_analytics_consent"); }} catch (e) {{}}
        gtag("consent", "default", {{
          analytics_storage: choice === "granted" ? "granted" : "denied",
          ad_storage: "denied",
          ad_user_data: "denied",
          ad_personalization: "denied",
          wait_for_update: 500
        }});
      }})();
      gtag("js", new Date());
      // The Vue router sends page_view itself on every in-app navigation.
      gtag("config", {ga_id}, {{ send_page_view: false }});
    </script>
    <script async src="https://www.googletagmanager.com/gtag/js?id={measurement_id}"></script>"""
