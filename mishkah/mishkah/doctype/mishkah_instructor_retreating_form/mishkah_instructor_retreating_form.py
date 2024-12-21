# Copyright (c) 2024, Omar Alhori and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document

class MishkahInstructorRetreatingForm(Document):
	def on_submit(self):
		student_group_doc = frappe.get_doc("Mishkah Student Group", self.student_group)
		found = False
		for instructor in student_group_doc.instructors:
			if instructor.instructor == self.instructor:
				student_group_doc.instructors.remove(instructor)
				found =True
				student_group_doc.student_group_name = self.substitute_student_group_name
				inst_row = student_group_doc.append("instructors")
				inst_row.instructor = self.substitute_instructor
				student_group_doc.save()
				student_group_doc.set_group_permissions()
		if not found:
			frappe.throw("Cannot find instructor in the selected group")