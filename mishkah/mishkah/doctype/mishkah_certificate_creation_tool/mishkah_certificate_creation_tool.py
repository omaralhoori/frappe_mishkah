# Copyright (c) 2024, Omar Alhori and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document

class MishkahCertificateCreationTool(Document):
	pass



@frappe.whitelist()
def get_students(student_group):
	"""
		return: {student, student_name, level-enrollment, instructor-name, total-points, certificate_type, certificate(if-exists)}
	"""

	students = frappe.db.sql("""
		SELECT tbl2.student_name, tbl4.total_level_points, 
			   tbl4.certificate_name, tbl4.certificate,
			   tbl6.instructor_name, tbl4.name as level_enrollment, tbl2.name as student
		FROM 
			`tabMishkah Student Group Student` as tbl1
			INNER JOIN `tabMishkah Student` as tbl2 ON tbl1.student=tbl2.name
			INNER JOIN `tabMishkah Student Group` as tbl3 ON tbl1.parent=tbl3.name
			INNER JOIN `tabMishkah Program Enrollment` as prog on prog.student=tbl1.student
			INNER JOIN `tabMishkah Level Enrollment` as tbl4 ON tbl4.program_enrollment=prog.name and tbl4.level=tbl3.level and tbl4.enrollment_status="Ongoing"
			INNER JOIN `tabMishkah Student Group Instructor` as tbl5 ON tbl5.parent=tbl1.parent
			INNER JOIN `tabMishkah Instructor` as tbl6 ON tbl6.name=tbl5.instructor
		WHERE
			tbl1.parent=%(student_group)s and tbl1.is_active=1 and tbl2.enrollment_status="عضوية فعالة"
""", {"student_group": student_group}, as_dict=True)
	return students

@frappe.whitelist()
def create_certificate(level_enrollment, instructor_name):
	enrollment_doc = frappe.get_doc("Mishkah Level Enrollment", level_enrollment)
	enrollment_doc.instructor_name = instructor_name
	enrollment_doc.save(ignore_permissions=True)
	return enrollment_doc.generate_certificate()
	
