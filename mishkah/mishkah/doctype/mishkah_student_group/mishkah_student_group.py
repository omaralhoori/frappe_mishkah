# Copyright (c) 2023, Omar Alhori and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document

class MishkahStudentGroup(Document):
	def remove_student(self, student):
		for s in self.students:
			if s.student == student:
				self.students.remove(s)
				return True
			
	def validate(self):
		self.validate_group_order()
		self.set_group_permissions()
	def validate_group_order(self):
		if self.parent_mishkah_student_group:
			parent_group_type = frappe.db.get_value("Mishkah Student Group", self.parent_mishkah_student_group, "group_type")
			if self.group_type == parent_group_type:
				frappe.throw("Group type cannot be same as the parent group")
			order_false = False
			if parent_group_type == 'Student Subgroup' and self.group_type in ('Program Group', 'Level Group', 'Student Main Group', 'Student Group'):
				order_false = True
			if parent_group_type == 'Student Group' and self.group_type in ('Program Group', 'Level Group', 'Student Main Group'):
				order_false = True
			if parent_group_type == 'Student Main Group' and self.group_type in ('Program Group', 'Level Group'):
				order_false = True
			if parent_group_type == 'Level Group' and self.group_type =='Program Group':
				order_false = True
			if order_false:
				frappe.throw("There is an error in the order of the groups")
			
	def on_update(self):
		self.students_count = len(self.students)
		self.db_set("students_count", self.students_count)
	
	@frappe.whitelist()
	def set_group_permissions(self, current_instruct = None):
		if self.group_type == 'Student Subgroup':
			self.create_instructor_permissions(current_instruct)
		else:
			groups = frappe.db.get_all("Mishkah Student Group", {"parent_mishkah_student_group": self.name})
			for group in groups:
				group_doc = frappe.get_doc("Mishkah Student Group", group.name)
				group_doc.set_group_permissions(current_instruct or self.instructors)
	
	def create_instructor_permissions(self, current_instruct = None):
		instructors = self.instructors
		if current_instruct:
			instructors = current_instruct
		for instructor in instructors:
			user = frappe.db.get_value("Mishkah Instructor", instructor.instructor, "user")
			if not frappe.db.exists("User Permission", {"user": user, "allow": "Mishkah Student Group", "for_value": self.name}):
				frappe.get_doc({
					"doctype": "User Permission",
					"user": user, 
					"allow": "Mishkah Student Group", 
					"for_value": self.name,
					"apply_to_all_doctypes": 1,
				}).insert(ignore_permissions=True)


def update_student_group_in_student():
	frappe.db.sql("""
		UPDATE `tabMishkah Student` as std
			   INNER JOIN `tabMishkah Student Group Student` as grp ON std.name=grp.student
			SET std.student_group=grp.parent
""")