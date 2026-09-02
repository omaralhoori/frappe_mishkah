# Copyright (c) 2023, Omar Alhori and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document
import time
import json 

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
		ORDER BY tbl1.idx
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
	# start = time.time()
	
	if progress_name:
		progress = frappe.get_doc("Mishkah Course Progress",progress_name)
		progress.points = points
		progress.save(ignore_permissions=True)
		# end = time.time()
		# print("time1:", end - start)
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
	# end = time.time()
	# print("time2:", end - start)
	return {
		"is_success": 1,
		"points": points,
		"progress_name": progress.name
	}

import random
import string

@frappe.whitelist()
def save_progress(results, enrollments):
	if type(results) == str:
		results = json.loads(results)
	for res in results:
		if not res.get("name") or res.get("name") == "":
			res['name'] =  res.get('level_enrollment') + "-" + res.get("course") #''.join(random.choices(string.ascii_letters + string.digits, k=10))
		res['creation'] = frappe.utils.now()
		res['modified'] = frappe.utils.now()
		res['modified_by'] = frappe.session.user
		res['owner'] = frappe.session.user
		frappe.db.sql("""
			INSERT INTO `tabMishkah Course Progress` (name, creation, modified, modified_by, owner, student, level_enrollment, course, points, student_group)
				VALUES (%(name)s, %(creation)s, %(modified)s, %(modified_by)s, %(owner)s, %(student)s, %(level_enrollment)s, %(course)s, {points}, %(student_group)s)
			ON DUPLICATE KEY UPDATE
				points={points}, 
				modified=%(modified)s,
				modified_by=%(modified_by)s;
		""".format(points=float(res['points'])), res)
	if type(enrollments) == str:
		enrollments = json.loads(enrollments)
	for enrollment in enrollments:
		total = frappe.db.sql("""
			SELECT SUM(points) as total
			FROM `tabMishkah Course Progress`
			WHERE level_enrollment=%(level_enrollment)s
		""", {"level_enrollment": enrollment}, as_dict=True)
		basic_total = frappe.db.sql("""
			SELECT SUM(points) as total
			FROM `tabMishkah Course Progress` as tbl1
			INNER JOIN `tabMishkah Course` as tbl2 on tbl1.course=tbl2.name
			WHERE tbl1.level_enrollment=%(level_enrollment)s and tbl2.basic_course=1
		""", {"level_enrollment": enrollment}, as_dict=True)
		total_points = total[0]['total']
		basic_total_points = basic_total[0]['total'] or 0
		frappe.db.set_value("Mishkah Level Enrollment", enrollment, {"total_level_points": total_points, "basic_total_level_points": basic_total_points})


MISMATCH_WHERE = """
	SUBSTRING_INDEX(name, '-', -1) != course
	AND name LIKE CONCAT(level_enrollment, '-%')
"""


def _get_course_progress_name_mismatches():
	return frappe.db.sql(f"""
		SELECT
			name,
			level_enrollment,
			course,
			SUBSTRING_INDEX(name, '-', -1) AS name_course_id,
			CONCAT(level_enrollment, '-', course) AS expected_name,
			points,
			student
		FROM `tabMishkah Course Progress`
		WHERE {MISMATCH_WHERE}
		ORDER BY level_enrollment, course
	""", as_dict=True)


@frappe.whitelist()
def get_course_progress_name_mismatch_report(sample_limit=50):
	"""تقرير عن سجلات Course Progress التي لا يطابق فيها الجزء بعد '-' حقل course."""
	mismatches = _get_course_progress_name_mismatches()
	breakdown = frappe.db.sql(f"""
		SELECT
			SUBSTRING_INDEX(name, '-', -1) AS old_course_id_in_name,
			course AS actual_course_id,
			COUNT(*) AS count
		FROM `tabMishkah Course Progress`
		WHERE {MISMATCH_WHERE}
		GROUP BY old_course_id_in_name, actual_course_id
		ORDER BY count DESC, old_course_id_in_name, actual_course_id
	""", as_dict=True)

	target_names = {}
	conflicts = []
	for row in mismatches:
		target = row["expected_name"]
		if target in target_names and target_names[target] != row["name"]:
			conflicts.append({
				"target_name": target,
				"records": [target_names[target], row["name"]],
			})
		target_names[target] = row["name"]

	return {
		"total_mismatches": len(mismatches),
		"breakdown": breakdown,
		"rename_conflicts": conflicts,
		"sample_records": mismatches[:int(sample_limit or 50)],
	}


@frappe.whitelist()
def fix_course_progress_names(dry_run=True):
	"""
	إعادة تسمية سجلات Course Progress لتصبح: level_enrollment-course
	عندما يكون الجزء الأخير من الاسم (بعد '-') لا يساوي course.

	التشغيل:
		# عرض التقرير فقط
		bench --site SITE execute mishkah.mishkah.doctype.mishkah_progress_editing_tool.mishkah_progress_editing_tool.get_course_progress_name_mismatch_report

		# معاينة الإصلاح بدون تنفيذ
		bench --site SITE execute mishkah.mishkah.doctype.mishkah_progress_editing_tool.mishkah_progress_editing_tool.fix_course_progress_names

		# تنفيذ الإصلاح
		bench --site SITE execute mishkah.mishkah.doctype.mishkah_progress_editing_tool.mishkah_progress_editing_tool.fix_course_progress_names --kwargs "{'dry_run': False}"
	"""
	report = get_course_progress_name_mismatch_report()
	mismatches = _get_course_progress_name_mismatches()

	if report["rename_conflicts"]:
		frappe.throw(
			"يوجد تعارض في الأسماء المستهدفة. راجع rename_conflicts في التقرير قبل التنفيذ.",
			title="تعارض في إعادة التسمية",
		)

	renames = [
		{
			"old_name": row["name"],
			"new_name": row["expected_name"],
			"old_course_id_in_name": row["name_course_id"],
			"actual_course_id": row["course"],
			"level_enrollment": row["level_enrollment"],
			"student": row["student"],
			"points": row["points"],
		}
		for row in mismatches
		if row["name"] != row["expected_name"]
	]

	result = {
		"dry_run": bool(int(dry_run) if isinstance(dry_run, str) else dry_run),
		"total_mismatches": report["total_mismatches"],
		"breakdown": report["breakdown"],
		"renames_planned": len(renames),
		"renamed": 0,
		"rename_details": renames,
	}

	if result["dry_run"]:
		return result

	temp_prefix = "__fix_name__"
	for row in renames:
		frappe.db.sql(
			"UPDATE `tabMishkah Course Progress` SET name=%s WHERE name=%s",
			(temp_prefix + row["old_name"], row["old_name"]),
		)

	for row in renames:
		frappe.db.sql(
			"UPDATE `tabMishkah Course Progress` SET name=%s WHERE name=%s",
			(row["new_name"], temp_prefix + row["old_name"]),
		)
		result["renamed"] += 1

	frappe.db.commit()
	return result