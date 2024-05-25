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
			
	def on_update(self):
		self.students_count = len(self.students)
		self.db_set("students_count", self.students_count)