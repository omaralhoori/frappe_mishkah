# Copyright (c) 2023, Omar Alhori and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document

class MishkahStudent(Document):
	def on_update(self):
		self.set_fullname()
	def set_fullname(self):
		fullname = self.first_name + " " + self.middle_name + " " + self.last_name
		self.db_set("student_name", fullname)
