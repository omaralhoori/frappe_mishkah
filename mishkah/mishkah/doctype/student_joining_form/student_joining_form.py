# Copyright (c) 2024, Omar Alhori and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document

class StudentJoiningForm(Document):
	def on_submit(self):
		student = self.create_student()
		self.add_student_to_group(student)

	def create_student(self):
		student_doc = frappe.get_doc({
			"doctype": "Mishkah Student",
			"student_mobile": self.mobile_phone,
			"first_name": self.first_name,
			"middle_name": self.middle_name,
			"last_name": self.last_name,
			"nationality": self.nationality,
			"country_of_residence": self.country_of_residence,
			"age_category": self.age_category,
			"educational_level": self.educational_level,
			"employed": self.employed,
			"marital_status": self.marital_status,
			"childrenif_exist": self.childrenif_exist,
			"specialty": self.specialty
		})
		student_doc.insert(ignore_permissions=True)
		return student_doc

	def add_student_to_group(self, student):
		student_group = frappe.get_doc("Mishkah Student Group", self.student_group)
		student_row = student_group.append("students")
		student_row.student = student.name
		student_row.is_active = 1
		student_group.save(ignore_permissions=True)