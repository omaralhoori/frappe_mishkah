# Copyright (c) 2023, Omar Alhori and contributors
# For license information, please see license.txt

from mishkah.mishkah.doctype.mishkah_certificate.mishkah_certificate import generate_certificate
import frappe
from frappe.model.document import Document
import json
class MishkahLevelCompleteTool(Document):
	pass


@frappe.whitelist()
def get_students(level):
	students = frappe.db.sql("""
			SELECT tbl1.name as enrollment, tbl1.total_level_points as points, tbl2.student, tbl1.instructor_name
			FROM `tabMishkah Level Enrollment` tbl1
			INNER JOIN `tabMishkah Program Enrollment` tbl2 ON tbl1.program_enrollment = tbl2.name
			WHERE tbl1.level = %(level)s AND tbl1.enrollment_status='Ongoing'
			LIMIT 100
						  """, {"level": level}, as_dict=True)
	return students


@frappe.whitelist()
def create_level_progress_enqueue(level, enrollments):
	if frappe.db.get_single_value("Mishkah Level Complete Tool", "status") == "In Progress": 
		return
	frappe.db.set_single_value("Mishkah Level Complete Tool", "status", "In Progress")
	frappe.enqueue(
		"create_level_progress", # python function or a module path as string
		queue="long", # one of short, default, long
		timeout=None, # pass timeout manually
		is_async=True, # if this is True, method is run in worker
		now=False, # if this is True, method is run directly (not in a worker) 
		job_name=None, # specify a job name
		enqueue_after_commit=False, # enqueue the job after the database commit is done at the end of the request
		at_front=True, # put the job at the front of the queue
		level=level,
		 enrollments=enrollments # kwargs are passed to the method as arguments
	)
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
		frappe.db.commit()
	frappe.db.set_single_value("Mishkah Level Complete Tool", "status", "Pending")
	return {
		"is_success": True,
		"failed_students": failed_students
	}

def handle_level_completion(enrollment, level,program_enrollment, next_level=None):
	frappe.db.set_value("Mishkah Level Enrollment", enrollment, "enrollment_status", "Completed")
	handle_level_completion_certificate(enrollment)
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


def handle_level_completion_certificate(enrollment):
	level_enrollment = frappe.db.get_value("Mishkah Level Enrollment", enrollment, ["total_level_points", "level", "program_enrollment", "instructor_name"], as_dict=True)
	if not level_enrollment:
		frappe.throw("Level Enrollment not found")
	level_certificate = frappe.db.get_value("Mishkah Level Certificate", {"level": level_enrollment['level']},'name', cache=True) 
	if not level_certificate:
		frappe.throw("Level Certificate not found")
	certificate_doc = frappe.get_doc("Mishkah Level Certificate", level_certificate)
	graduation_certificate = None
	for certificate in certificate_doc.certificates:
		if level_enrollment['total_level_points'] >= certificate.min_points:
			graduation_certificate = certificate
			break
	if not graduation_certificate:
		return
	student = frappe.db.get_value("Mishkah Program Enrollment", level_enrollment['program_enrollment'], "student_name")
	certificate_path = generate_certificate(graduation_certificate.certificate, student, level_enrollment.instructor_name or "", frappe.utils.nowdate(), save_as_file=True)
	frappe.db.set_value("Mishkah Level Enrollment", enrollment, "certificate", certificate_path)
	frappe.db.set_value("Mishkah Level Enrollment", enrollment, "certificate_name", graduation_certificate.certificate)
def handle_failed_students(enrollment, level):
	enrollment_doc = frappe.get_doc("Mishkah Level Enrollment", enrollment)
	enrollment_doc.enrollment_status =  "Failed"
	enrollment_doc.save(ignore_permissions=True)
	new_level_doc = frappe.get_doc({
			"doctype": "Mishkah Level Enrollment",
			"program_enrollment": enrollment_doc.program_enrollment,
			"enrollment_date": frappe.utils.nowdate(),
			"level": enrollment_doc.level,
			"educational_term": frappe.db.get_single_value("Mishkah Settings", "current_educational_term"),
			"enrollment_status": "Ongoing"
		})
	new_level_doc.insert(ignore_permissions=True)
	drop_student_from_groups(enrollment_doc.program_enrollment, level)

def drop_student_from_groups(program_enrollment, level):
	groups = frappe.db.sql("""
			SELECT tbl1.name as group_name
			FROM `tabMishkah Student Group` tbl1
			WHERE tbl1.level = %(level)s
			""", {"level": level}, as_dict=True)
	program_enrollment_doc = frappe.get_doc("Mishkah Program Enrollment", program_enrollment)
	for group in groups:
		group_doc = frappe.get_doc("Mishkah Student Group", group.group_name)
		group_doc.remove_student(program_enrollment_doc.student)
		group_doc.save(ignore_permissions=True)


@frappe.whitelist()
def set_level_enrollment_missing_data(level_type):
	frappe.only_for("System Manager")
	levels = frappe.db.get_all("Mishkah Level Enrollment", {"level" : level_type})
	for level in levels:
		# get student
		frappe.db.sql("""
			UPDATE `tabMishkah Level Enrollment` lvl
				INNER JOIN `tabMishkah Program Enrollment` prog ON lvl.program_enrollment=prog.name
				INNER JOIN `tabMishkah Student` as std ON std.name=prog.student
				INNER JOIN `tabMishkah Student Group Student` as grpStd ON grpStd.student=std.name
				INNER JOIN `tabMishkah Student Group` as grp1 ON grp1.name=grpStd.parent
				INNER JOIN `tabMishkah Student Group` as grp2 ON grp2.name=grp1.parent_mishkah_student_group
				INNER JOIN `tabMishkah Student Group` as grp3 ON grp3.name=grp2.parent_mishkah_student_group
				INNER JOIN `tabMishkah Student Group Instructor` as grpInst ON grpInst.parent=grp1.name
				INNER JOIN `tabMishkah Instructor` as inst on inst.name=grpInst.instructor
			SET lvl.student_name=std.student_name, 
				lvl.instructor_name=inst.instructor_name,
				lvl.main_group=grp3.student_group_name,
				lvl.group=grp2.student_group_name,
				lvl.subgroup=grp1.student_group_name
			WHERE lvl.name=%(level)s
""", {"level": level.name})
	frappe.msgprint("All data has been set")



def set_certificate_type():
	levels = frappe.db.sql("""
		select name, total_level_points, level
				FROM `tabMishkah Level Enrollment`
			WHERE total_level_points > 0 AND (certificate_type = "" or certificate_type is null)
""", as_dict=True)
	certificates = frappe.db.sql("""
		select tbl1.certificate, tbl1.min_points, tbl2.level
			FROM `tabMishkah Level Certificate Item` as tbl1
			INNER JOIN `tabMishkah Level Certificate` as tbl2 ON tbl1.parent=tbl2.name
			order BY tbl1.min_points desc
	""", as_dict=True)
	for level in levels:
		graduation_certificate = None
		for certificate in certificates:
			if level['level'] == certificate['level'] and level['total_level_points'] >= certificate.min_points:
				graduation_certificate = certificate
				break
		if not graduation_certificate:
			continue
		frappe.db.set_value("Mishkah Level Enrollment", level['name'], "certificate_type",graduation_certificate.certificate)
		
