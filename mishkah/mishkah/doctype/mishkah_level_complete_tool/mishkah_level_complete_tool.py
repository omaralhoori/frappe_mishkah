# Copyright (c) 2023, Omar Alhori and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document
import json
class MishkahLevelCompleteTool(Document):
	pass


@frappe.whitelist()
def get_students(level):
	students = frappe.db.sql("""
			SELECT tbl1.name as enrollment, tbl1.total_level_points as points, tbl2.student
			FROM `tabMishkah Level Enrollment` tbl1
			INNER JOIN `tabMishkah Program Enrollment` tbl2 ON tbl1.program_enrollment = tbl2.name
			WHERE tbl1.level = %(level)s AND tbl1.enrollment_status='Ongoing'
						  """, {"level": level}, as_dict=True)
	return students

@frappe.whitelist()
def create_level_progress(level, enrollments):
	if type(enrollments) == str:
		level_enrollments = json.loads(enrollments)
	else:
		level_enrollments = enrollments
	completion_settings = frappe.get_single('Mishkah Level Completion')
	level_min_points = None
	next_level = None
	for setting in completion_settings.levels:
		if setting.level == level:
			level_min_points = setting.completion_min_points
			next_level = setting.next_level
			break
	if not level_min_points:
		frappe.throw("Level not found")
	failed_students = []
	for enrollment in level_enrollments:
		lvl = frappe.db.get_value("Mishkah Level Enrollment", enrollment, ["total_level_points", "program_enrollment"])
		if lvl[0] >= level_min_points:
			handle_level_completion(enrollment, level, lvl[1], next_level)
		else:
			failed_students.append(enrollment)
			handle_failed_students(enrollment, level)
	return {
		"is_success": True,
		"failed_students": failed_students
	}

def handle_level_completion(enrollment, level,program_enrollment, next_level=None):
	frappe.db.set_value("Mishkah Level Enrollment", enrollment, "enrollment_status", "Completed")
	if next_level:
		new_level_doc = frappe.get_doc({
			"doctype": "Mishkah Level Enrollment",
			"program_enrollment": program_enrollment,
			"enrollment_date": frappe.utils.nowdate(),
			"level": next_level,
			"educational_term": frappe.db.get_single_value("Mishkah Settings", "current_educational_term"),
			"enrollment_status": "Ongoing"
		})
		new_level_doc.insert(ignore_permissions=True)


def handle_failed_students(enrollment, level):
	frappe.db.set_value("Mishkah Level Enrollment", enrollment, "enrollment_status", "Failed")