# Copyright (c) 2023, Omar Alhori and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document

class MishkahStudentJoiningRequest(Document):
	
	@frappe.whitelist()
	def approve_request(self, program, level=None):
		student = self.create_student()
		program_enrollment = self.create_program_enrollment(student, program)
		if level:
			self.create_level_enrollment(program_enrollment, level)
		self.db_set("status", "Approved")
		return {"success_key": 1}
	
	def create_student(self):
		if frappe.db.exists("Mishkah Student", {"student_mobile": self.mobile_phone}):
			frappe.throw("Student already exists!")
		student_doc = frappe.get_doc({
			"doctype": "Mishkah Student",
			"first_name": self.first_name,
			"middle_name": self.middle_name,
			"last_name": self.last_name,
			"student_mobile": self.mobile_phone,
			"nationality": self.nationality
		})
		student_doc.save(ignore_permissions=True)
		return student_doc
		
	def create_program_enrollment(self, student, program):
		enrollment = frappe.get_doc({
			"doctype": "Mishkah Program Enrollment",
			"program": program,
			"student": student.name,
			"enrollment_date": frappe.utils.nowdate()
		})

		enrollment.insert(ignore_permissions=True)
		return enrollment
	
	def create_level_enrollment(self, program_enrollment, level):
		enrollment = frappe.get_doc({
			"doctype": "Mishkah Level Enrollment",
			"program_enrollment": program_enrollment.name,
			"level": level,
			"enrollment_date": frappe.utils.nowdate(),
			"educational_term": frappe.db.get_single_value("Mishkah Settings", "current_educational_term"),
			"enrollment_status": "Ongoing"
		})

		enrollment.insert(ignore_permissions=True)
		return enrollment