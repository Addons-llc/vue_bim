import frappe
from frappe import _
from frappe.model.document import Document

from bim_supplier_store.utils import normalize_hostname, normalize_store_code, validate_store_code


class SupplierStore(Document):
	def validate(self):
		self.store_code = normalize_store_code(self.store_code or self.store_name)
		if not validate_store_code(self.store_code):
			frappe.throw(_("Store Code must contain lowercase letters, numbers, and single hyphens only."))
		self._validate_warehouse()
		self._validate_price_list()
		self._validate_domains()
		self._validate_products()

	def _validate_warehouse(self):
		if not self.default_warehouse:
			return
		warehouse = frappe.db.get_value(
			"Warehouse",
			self.default_warehouse,
			["company", "is_group", "disabled"],
			as_dict=True,
		)
		if not warehouse or warehouse.is_group or warehouse.disabled:
			frappe.throw(_("Default Warehouse must be an enabled, non-group warehouse."))
		if warehouse.company != self.company:
			frappe.throw(_("Default Warehouse must belong to Company {0}.").format(self.company))

	def _validate_price_list(self):
		if not self.selling_price_list:
			return
		price_list = frappe.db.get_value(
			"Price List",
			self.selling_price_list,
			["selling", "enabled"],
			as_dict=True,
		)
		if not price_list or not price_list.selling or not price_list.enabled:
			frappe.throw(_("Selling Price List must be enabled and marked as a selling price list."))

	def _validate_domains(self):
		seen = set()
		primary_count = 0
		for row in self.domains:
			row.domain_name = normalize_hostname(row.domain_name)
			if not row.domain_name:
				frappe.throw(_("Enter a valid hostname in domain row {0}.").format(row.idx))
			if row.domain_name in seen:
				frappe.throw(_("Domain {0} is repeated in this store.").format(row.domain_name))
			seen.add(row.domain_name)
			existing = frappe.db.get_value(
				"Store Domain",
				{
					"domain_name": row.domain_name,
					"parent": ["!=", self.name or ""],
				},
				"parent",
			)
			if existing:
				frappe.throw(_("Domain {0} is already assigned to another Supplier Store.").format(row.domain_name))
			if not row.verification_token:
				row.verification_token = frappe.generate_hash(length=32)
			primary_count += int(bool(row.primary_domain))
		if primary_count > 1:
			frappe.throw(_("Only one Store Domain can be marked as Primary Domain."))

	def _validate_products(self):
		seen = set()
		for row in self.products:
			if row.item_code in seen:
				frappe.throw(_("Item {0} is repeated in Store Products.").format(row.item_code))
			seen.add(row.item_code)
			row.route_slug = normalize_store_code(row.route_slug or row.item_code)

