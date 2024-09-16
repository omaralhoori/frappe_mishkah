# Copyright (c) 2023, Omar Alhori and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document
import time

class MishkahProgressEditingTool(Document):
	pass


@frappe.whitelist()
def get_students(student_group, level_stage):
	groups = get_groups(student_group)
	if len(groups) == 0:
		frappe.throw("Unable to find student groups")
	students = get_student_progresses(groups)
	courses = get_courses_per_stage(level_stage, groups)
	return {
		"students": students,
		"courses": courses
	}

def get_courses_per_stage(level_stage, groups):
	group = groups[0].replace("'", "")
	level = frappe.db.get_value("Mishkah Student Group", group, "level")
	return frappe.db.sql("""
		SELECT tbl1.course, tbl3.course_name, tbl3.course_points 
		FROM `tabMishkah Learning Path Stage` as tbl1
		INNER JOIN `tabMishkah Learning Path` as tbl2 ON tbl1.parent=tbl2.name
		INNER JOIN `tabMishkah Course` as tbl3 ON tbl1.course=tbl3.name
		WHERE tbl2.level=%(level)s AND tbl1.stage=%(stage)s
	""", {"level": level, "stage": level_stage}, as_dict=True)


def get_student_progresses(groups):
	groups_joined = ",".join(groups)
	return frappe.db.sql("""
		SELECT tbl1.student,tbl1.parent as group_id, tbl4.name as level_enrollment, tbl1.student_name, GROUP_CONCAT(tbl5.name) as progresses,GROUP_CONCAT(tbl5.course) as courses, GROUP_CONCAT(tbl5.points) as points
		FROM `tabMishkah Student Group Student` as tbl1
		INNER JOIN `tabMishkah Student Group` as tbl2 on tbl2.name=tbl1.parent
		INNER JOIN `tabMishkah Program Enrollment` as tbl3 ON tbl1.student=tbl3.student AND tbl2.program=tbl3.program
		INNER JOIN `tabMishkah Student` as tbl6 ON tbl6.name=tbl1.student
		INNER JOIN `tabMishkah Level Enrollment` as tbl4 ON tbl4.program_enrollment=tbl3.name AND tbl4.level=tbl2.level AND tbl4.enrollment_status='Ongoing'
		LEFT JOIN `tabMishkah Course Progress` as tbl5 ON tbl5.level_enrollment=tbl4.name
		WHERE tbl1.parent IN ({groups_joined}) AND tbl1.is_active=1 AND tbl6.enrollment_status="عضوية فعالة"
		GROUP BY tbl1.student
		ORDER BY tbl1.student_name
	""".format(groups_joined=groups_joined), as_dict=True)

def get_groups(student_group, current_level=None):
	group_type = frappe.db.get_value("Mishkah Student Group", student_group, ['group_type' ])#frappe.get_doc("Mishkah Student Group", student_group)
	if group_type == 'Student Subgroup':
		return [f"'{student_group}'"]#[student.student for student in group_doc.students if student.is_active]
	child_level = group_type
	all_groups= []
	child_groups = frappe.db.get_all("Mishkah Student Group", {"parent_mishkah_student_group": student_group}, ['name'])
	for group in child_groups:
		if current_level:
			check_group_order(current_level, child_level)
		groups = get_groups(group.name, child_level)
		all_groups.extend(groups)
	return all_groups

def get_groups_by_child(student_group, current_level=None):
	group_doc = frappe.get_doc("Mishkah Student Group", student_group)
	if group_doc.group_type == 'Student Subgroup':
		return [f"'{student_group}'"]#[student.student for student in group_doc.students if student.is_active]
	child_level = group_doc.group_type
	all_groups= []
	for group in group_doc.groups:
		if current_level:
			check_group_order(current_level, child_level)
		groups = get_groups(group.group, child_level)
		all_groups.extend(groups)
	return all_groups

def check_group_order(current_level, child_level):
	if current_level == child_level:
		return frappe.throw("Groups contain each other")
	if child_level == 'Program Group': return frappe.throw("Groups contain each other")
	if current_level == 'Student Main Group' and (child_level == 'Program Group' or child_level == 'Student Main Group'):
		frappe.throw("Groups contain each other")
	return True


@frappe.whitelist()
def set_student_mark(enrollment, points, course, group, student, progress_name=None):
	print("99999999999999999999999999999")
	print(group, student)
	start = time.time()
	
	if progress_name:
		progress = frappe.get_doc("Mishkah Course Progress",progress_name)
		progress.points = points
		progress.save(ignore_permissions=True)
		end = time.time()
		print("time1:", end - start)
		return {
			"is_success": 1,
			"points": points,
			"progress_name": progress.name
		}
	if frappe.db.exists("Mishkah Course Progress", {"level_enrollment": enrollment, "course": course}):
		return {
			"is_success": 0,
			"message": "already exists"
		}
	progress = frappe.get_doc({
		"doctype": "Mishkah Course Progress",
		"level_enrollment": enrollment, 
		"course": course,
		"points": points,
		"student_group": group,
		"student": student
	})
	progress.insert(ignore_permissions=True)
	end = time.time()
	print("time2:", end - start)
	return {
		"is_success": 1,
		"points": points,
		"progress_name": progress.name
	}
