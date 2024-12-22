# Copyright (c) 2024, Omar Alhori and contributors
# For license information, please see license.txt

import frappe
from frappe import _

def execute(filters=None):
	columns, data = get_columns(), get_data(filters)
	return columns, data

def get_columns():
	columns = [
		
		_("Student Name") + "::250",
		_("Student Id") + "::140",
		_("Level") + "::180",
	]

	return columns

def get_data(filters=None):
	data = frappe.db.sql("""
		SELECT tbl1.student_name, tbl1.name as student_id, tbl3.level FROM `tabMishkah Student` tbl1
			INNER JOIN `tabMishkah Program Enrollment` as tbl2 on tbl1.name=tbl2.student
			INNER JOIN `tabMishkah Level Enrollment` as tbl3 on tbl3.program_enrollment=tbl2.name
			WHERE tbl1.enrollment_status="عضوية فعالة" and tbl3.enrollment_status="Ongoing" and tbl1.name not in (select student from `tabMishkah Student Group Student`)
""", as_dict=True )

	return data