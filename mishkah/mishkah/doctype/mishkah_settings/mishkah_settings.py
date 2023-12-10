# Copyright (c) 2023, Omar Alhori and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document

education_keydict = {
	"joining_program": "default_joining_program",
	"joining_level": "default_joining_level",
	"educational_term": "current_educational_term"
}

class MishkahSettings(Document):
	def on_update(self):
		"""update defaults"""
		for key in education_keydict:
			frappe.db.set_default(key, self.get(education_keydict[key], ""))

	# clear cache
	frappe.clear_cache()
