# Copyright (c) 2024, Omar Alhori and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document
from mishkah.mishkah.doctype.mishkah_level_enrollment.mishkah_level_enrollment import (
	get_basic_courses_for_level,
)
from mishkah.mishkah.doctype.mishkah_certificate.graduation_certificate import (
	get_graduation_config,
)


class MishkahCertificateCreationTool(Document):
	pass


def get_total_basic_courses(level):
	return len(get_basic_courses_for_level(level))


@frappe.whitelist()
def get_students(student_group):
	"""
		return: {student, student_name, level-enrollment, instructor-name, total-points,
		         certificate_type, certificate(if-exists), completed_basic_courses,
		         total_basic_courses, all_basic_completed, graduation fields}
	"""
	level = frappe.db.get_value("Mishkah Student Group", student_group, "level")
	basic_courses = get_basic_courses_for_level(level)
	total_basic_courses = len(basic_courses)
	graduation_config = get_graduation_config()
	is_graduation_level = 1 if (
		graduation_config.get("level") and graduation_config.get("level") == level
	) else 0

	students = frappe.db.sql("""
		SELECT tbl2.student_name, tbl4.total_level_points, tbl4.basic_total_level_points,
			   tbl4.certificate_name, tbl4.certificate,
			   tbl6.instructor_name, tbl4.name as level_enrollment, tbl2.name as student,
			   prog.name as program_enrollment, prog.program,
			   prog.graduation_certificate, prog.graduated, prog.graduation_date
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

	completed_by_enrollment = {}
	if students and basic_courses:
		enrollment_names = tuple({row.level_enrollment for row in students})
		progress_rows = frappe.db.sql("""
			SELECT level_enrollment, COUNT(*) as completed_basic_courses
			FROM `tabMishkah Course Progress`
			WHERE level_enrollment IN %(enrollments)s
				AND points > 0
				AND course IN %(courses)s
			GROUP BY level_enrollment
		""", {
			"enrollments": enrollment_names,
			"courses": tuple(basic_courses),
		}, as_dict=True)
		completed_by_enrollment = {
			row.level_enrollment: row.completed_basic_courses
			for row in progress_rows
		}

	for row in students:
		completed = completed_by_enrollment.get(row.level_enrollment, 0)
		row.completed_basic_courses = completed
		row.total_basic_courses = total_basic_courses
		row.all_basic_completed = (
			1 if total_basic_courses > 0 and completed >= total_basic_courses else 0
		)
		row.is_graduation_level = is_graduation_level

	return {
		"students": students,
		"is_graduation_level": is_graduation_level,
		"graduation_level": graduation_config.get("level"),
	}


@frappe.whitelist()
def create_certificate(level_enrollment, instructor_name):
	enrollment_doc = frappe.get_doc("Mishkah Level Enrollment", level_enrollment)
	enrollment_doc.instructor_name = instructor_name
	enrollment_doc.save(ignore_permissions=True)
	level_cert = enrollment_doc.generate_certificate()
	pe = frappe.db.get_value(
		"Mishkah Level Enrollment",
		level_enrollment,
		"program_enrollment",
	)
	graduation_cert = frappe.db.get_value(
		"Mishkah Program Enrollment", pe, "graduation_certificate"
	) if pe else None
	return {
		"certificate": level_cert,
		"graduation_certificate": graduation_cert,
		"program_enrollment": pe,
	}
