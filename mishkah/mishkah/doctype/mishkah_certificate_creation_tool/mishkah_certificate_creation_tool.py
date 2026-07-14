# Copyright (c) 2024, Omar Alhori and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document

class MishkahCertificateCreationTool(Document):
	pass



def get_total_basic_courses(level):
	cache = frappe.cache()
	cache_key = f"mishkah:total_basic_courses:{level}"
	total = cache.get_value(cache_key)
	if total is not None:
		return int(total)

	total = frappe.db.sql("""
		SELECT COUNT(DISTINCT lps.course) as total
		FROM `tabMishkah Learning Path Stage` lps
		INNER JOIN `tabMishkah Course` c ON c.name = lps.course AND c.basic_course = 1
		WHERE lps.parent = %(level)s
	""", {"level": level}, as_dict=True)[0].total or 0
	cache.set_value(cache_key, total, expires_in_sec=3600)
	return total


@frappe.whitelist()
def get_students(student_group):
	"""
		return: {student, student_name, level-enrollment, instructor-name, total-points,
		         certificate_type, certificate(if-exists), completed_basic_courses,
		         total_basic_courses, all_basic_completed}
	"""
	level = frappe.db.get_value("Mishkah Student Group", student_group, "level")
	total_basic_courses = get_total_basic_courses(level)

	students = frappe.db.sql("""
		SELECT tbl2.student_name, tbl4.total_level_points, tbl4.basic_total_level_points,
			   tbl4.certificate_name, tbl4.certificate,
			   tbl6.instructor_name, tbl4.name as level_enrollment, tbl2.name as student,
			   COALESCE(basic_progress.completed_basic_courses, 0) as completed_basic_courses,
			   %(total_basic_courses)s as total_basic_courses,
			   CASE
				   WHEN %(total_basic_courses)s = 0 THEN 0
				   WHEN COALESCE(basic_progress.completed_basic_courses, 0) >= %(total_basic_courses)s THEN 1
				   ELSE 0
			   END as all_basic_completed
		FROM
			`tabMishkah Student Group Student` as tbl1
			INNER JOIN `tabMishkah Student` as tbl2 ON tbl1.student=tbl2.name
			INNER JOIN `tabMishkah Student Group` as tbl3 ON tbl1.parent=tbl3.name
			INNER JOIN `tabMishkah Program Enrollment` as prog on prog.student=tbl1.student
			INNER JOIN `tabMishkah Level Enrollment` as tbl4 ON tbl4.program_enrollment=prog.name and tbl4.level=tbl3.level and tbl4.enrollment_status="Ongoing"
			INNER JOIN `tabMishkah Student Group Instructor` as tbl5 ON tbl5.parent=tbl1.parent
			INNER JOIN `tabMishkah Instructor` as tbl6 ON tbl6.name=tbl5.instructor
			LEFT JOIN (
				SELECT cp.level_enrollment, COUNT(DISTINCT cp.course) as completed_basic_courses
				FROM `tabMishkah Course Progress` cp
				INNER JOIN `tabMishkah Course` c ON c.name = cp.course AND c.basic_course = 1
				INNER JOIN `tabMishkah Learning Path Stage` lps ON lps.course = c.name AND lps.parent = %(level)s
				INNER JOIN `tabMishkah Level Enrollment` le ON le.name = cp.level_enrollment
					AND le.level = %(level)s AND le.enrollment_status = "Ongoing"
				INNER JOIN `tabMishkah Program Enrollment` pe ON pe.name = le.program_enrollment
				INNER JOIN `tabMishkah Student Group Student` sgs ON sgs.student = pe.student
					AND sgs.parent = %(student_group)s AND sgs.is_active = 1
				WHERE cp.points >= c.course_points
				GROUP BY cp.level_enrollment
			) as basic_progress ON basic_progress.level_enrollment = tbl4.name
		WHERE
			tbl1.parent=%(student_group)s and tbl1.is_active=1 and tbl2.enrollment_status="عضوية فعالة"
	""", {
		"student_group": student_group,
		"level": level,
		"total_basic_courses": total_basic_courses,
	}, as_dict=True)
	return students

@frappe.whitelist()
def create_certificate(level_enrollment, instructor_name):
	enrollment_doc = frappe.get_doc("Mishkah Level Enrollment", level_enrollment)
	enrollment_doc.instructor_name = instructor_name
	enrollment_doc.save(ignore_permissions=True)
	return enrollment_doc.generate_certificate()
	
