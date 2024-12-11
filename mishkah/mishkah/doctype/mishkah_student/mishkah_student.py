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
		self.update_student_name_in_doctypes()
	def update_student_name_in_doctypes(self):
		old_doc = self.get_doc_before_save()
		if not old_doc or old_doc.student_name == self.student_name:
			return
		# student groups
		students = frappe.db.get_all("Mishkah Student Group Student", {"student": self.name}, ['name'])
		for student in students:
			frappe.db.set_value("Mishkah Student Group Student", student.name, "student_name", self.student_name)
		#program enrollment
		students = frappe.db.get_all("Mishkah Program Enrollment", {"student": self.name}, ['name'])
		for student in students:
			frappe.db.set_value("Mishkah Program Enrollment", student.name, "student_name", self.student_name)