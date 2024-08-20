# Copyright (c) 2024, Omar Alhori and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document

class StudentJoiningForm(Document):
	def on_submit(self):
		student = self.create_student()
		group = self.add_student_to_group(student)
		program_enrollment = frappe.get_doc({
					"doctype": "Mishkah Program Enrollment",
					"student": student.name,
					"program": group.program,
					"enrollment_date": frappe.utils.now()
				})

		program_enrollment.save(ignore_permissions=True)
		frappe.get_doc({
			"doctype": "Mishkah Level Enrollment",
			"program_enrollment": program_enrollment.name,
			"enrollment_date": frappe.utils.now(),
			"enrollment_status": "Ongoing",
			"level": group.level,
			"educational_term": frappe.db.get_single_value("Mishkah Settings", "current_educational_term")
		}).save(ignore_permissions=True)

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
			"specialty": self.specialty,
			"enrollment_status":"عضوية فعالة"
		})
		student_doc.insert(ignore_permissions=True)
		return student_doc

	def add_student_to_group(self, student):
		student_group = frappe.get_doc("Mishkah Student Group", self.student_group)
		student_row = student_group.append("students")
		student_row.student = student.name
		student_row.is_active = 1
		student_group.save(ignore_permissions=True)
		return student_group


def create_enrollments():
	groups = frappe.db.get_all("Mishkah Student Group", 
							{"group_type": "Student Subgroup", 
		"level": ["!=", "الدفعة الجديدة"]},["name", "level", "program"])
	for group in groups:
		students = frappe.db.get_all("Mishkah Student Group Student", {"parent": group.name}, ["student"])
		for student in students:
			if not frappe.db.exists("Mishkah Program Enrollment", {"student": student.student}):
				program_enrollment = frappe.get_doc({
					"doctype": "Mishkah Program Enrollment",
					"student": student.student,
					"program": group.program,
					"enrollment_date": frappe.utils.now()
				})

				program_enrollment.save()
				frappe.get_doc({
					"doctype": "Mishkah Level Enrollment",
					"program_enrollment": program_enrollment.name,
					"enrollment_date": frappe.utils.now(),
					"enrollment_status": "Ongoing",
					"level": group.level,
					"educational_term": "الفصل الشتوي 2023"
				}).save()
				frappe.db.commit()