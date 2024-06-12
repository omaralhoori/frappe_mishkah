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