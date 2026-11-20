from frappe.model.document import Document


class BIMTwilioWhatsAppSettings(Document):
	def validate(self):
		self.account_sid = (self.account_sid or "").strip()
		self.from_whatsapp_number = (self.from_whatsapp_number or "").strip()
