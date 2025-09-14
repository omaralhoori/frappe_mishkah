# Copyright (c) 2025, Omar Alhori and contributors
# For license information, please see license.txt

import frappe
from frappe import _

def execute(filters=None):
	data = get_data(filters)
	columns = get_columns(filters)
	return columns, data


def get_columns(filters):
	# get all courses in this level in order
	courses = frappe.db.sql("""
		SELECT crs.name, crs.course_name
		FROM `tabMishkah Learning Path Stage` as pth
		INNER JOIN `tabMishkah Course` as crs ON crs.name=pth.course
		WHERE parent=%(level)s
		ORDER BY pth.idx
""", {"level": filters.get("level")}, as_dict=True)
	columns  = [
		{
			"fieldname": "student_id",
			"label": _("Student Id"),
			"fieldtype": "Link",
			"options": "Mishkah Student",
			"width": 180 
		},
		{
			"fieldname": "student",
			"label": _("Student"),
			"fieldtype": "Data",
			"width": 250 
		},
		{
			"fieldname": "student_group_name",
			"label": _("Group"),
			"fieldtype": "Data",
			"width": 250 
		},		
	]
	for course in courses:
		columns.append( {
			"fieldname": course.name,
			"label": course.course_name,
			"fieldtype": "Float"
		})
		
	return columns

def get_data(filters=None):
	# get all progresses in this level
	# join groups, student, courses
	# MAX(CASE WHEN c.name = 'Math' THEN m.mark END) AS Math,
	courses = frappe.db.get_all("Mishkah Learning Path Stage", {"parent": filters.get("level")}, ["course"])
	course_pivot = ""
	for course in courses:
		course_pivot += f", MAX(CASE WHEN prgs.course='{course.course}' THEN prgs.points END) AS `{course.course}`"
	sql = """
		SELECT std.name as student_id, std.student_name as student, grp.student_group_name
		{course_pivot}
		FROM `tabMishkah Course Progress` as prgs
		INNER JOIN `tabMishkah Student` as std ON prgs.student=std.name
		INNER JOIN `tabMishkah Student Group` as grp ON grp.name=prgs.student_group 
		INNER JOIN `tabMishkah Level Enrollment` as enrl ON enrl.name=prgs.level_enrollment 
		WHERE enrl.level=%(level)s and enrl.educational_term=%(term)s
		GROUP BY enrl.name
	""".format(course_pivot=course_pivot)
	return frappe.db.sql(sql, {"level": filters.get("level"), "term": filters.get("term")}, as_dict=True)
