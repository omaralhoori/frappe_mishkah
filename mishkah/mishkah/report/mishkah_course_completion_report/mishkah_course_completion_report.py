# Copyright (c) 2024, Omar Alhori and contributors
# For license information, please see license.txt

import frappe
from frappe import _

def execute(filters=None):
	columns, data = get_columns(), get_data(filters)
	return columns, data

def get_columns():
	columns = [
		
		_("Group Name") + "::250",
		_("Total Completers") + ":Int:140",
		_("Student Group") + ":Link/Mishkah Student Group:180",

	]
	return columns

def get_data(filters):
	course = filters.get("Course")

	data = frappe.db.sql("""
		SELECT count(tbl1.student_group) as total_completers, tbl3.name as student_group,tbl3.student_group_name as group_name
			   FROM `tabMishkah Course Progress` as tbl1
			   INNER JOIN `tabMishkah Course` as tbl2 on tbl1.course=tbl2.name
			   INNER JOIN `tabMishkah Student Group` as tbl3 on tbl1.student_group=tbl3.name
		WHERE tbl1.points>=tbl2.course_points and tbl1.course=%(course)s
		GROUP BY tbl1.student_group
""",{"course": course}, as_dict=True )

	return data