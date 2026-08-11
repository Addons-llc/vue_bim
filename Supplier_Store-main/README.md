# BIM Supplier Store

A minimal Frappe/ERPNext application that installs the `Supplier Store` master
DocType and its `Store Domain` and `Store Product` child tables.

## Included

- Supplier/store identity and status
- ERPNext Supplier, Company, Warehouse, Price List, and Currency links
- Commission percentage
- Store logo, banner, colours, contact number, and WhatsApp number
- Multiple domains with primary, verification, SSL, and active status fields
- Multiple ERPNext Items with published, featured, slug, and display-order fields
- Validation for store codes, warehouse/company ownership, selling price lists,
  duplicate products, duplicate domains, and primary domains
- Automatic domain verification-token generation

## Deliberately not included

- Storefront pages or Vue components
- Cart, checkout, Sales Orders, or Purchase Orders
- Payment, Stripe, or Payment Entry logic
- OTP, Twilio, login, or customer registration
- DNS lookup or automatic SSL provisioning
- Public APIs
- ERPNext transaction custom fields
- Homepage or website-route hooks

## Install

Install this app on a site that has ERPNext installed:

```bash
cd /path/to/frappe-bench
cp -R /absolute/path/bim_supplier_store apps/bim_supplier_store
./env/bin/pip install -e apps/bim_supplier_store
bench --site your-site.local install-app bim_supplier_store
bench --site your-site.local migrate
bench --site your-site.local clear-cache
```

Then open ERPNext Desk and search for **Supplier Store**.

## Important compatibility note

Do not install this app on the same site as `bim_multi_store`; both own DocTypes
named `Supplier Store`, `Store Domain`, and `Store Product`. For a demo site with no
important data, uninstall the larger app first or create a clean site.

```bash
bench --site your-site.local backup
bench --site your-site.local uninstall-app bim_multi_store --yes
bench --site your-site.local install-app bim_supplier_store
```

Uninstalling an app removes the DocTypes owned by that app. Export or back up any
Supplier Store records that must be retained before uninstalling.

## Tests

```bash
bench --site your-site.local run-tests --app bim_supplier_store
```

