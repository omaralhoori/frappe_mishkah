# Copyright (c) 2024, Omar Alhori and contributors
# For license information, please see license.txt

import frappe
from frappe import _


def execute(filters=None):
	filters = filters or {}
	columns = get_columns()
	data = get_data(filters)
	return columns, data


def get_columns():
	return [
		{
			"label": _("Student"),
			"fieldname": "student",
			"fieldtype": "Link",
			"options": "Mishkah Student",
			"width": 140,
		},
		{
			"label": _("Student Name"),
			"fieldname": "student_name",
			"fieldtype": "Data",
			"width": 220,
		},
		{
			"label": _("Program"),
			"fieldname": "program",
			"fieldtype": "Link",
			"options": "Mishkah Program",
			"width": 160,
		},
		{
			"label": _("Graduation Date"),
			"fieldname": "graduation_date",
			"fieldtype": "Date",
			"width": 120,
		},
		{
			"label": _("Graduation Certificate"),
			"fieldname": "graduation_certificate",
			"fieldtype": "Data",
			"width": 280,
		},
		{
			"label": _("Level Certificate"),
			"fieldname": "level_certificate",
			"fieldtype": "Data",
			"width": 280,
		},
		{
			"label": _("Graduated"),
			"fieldname": "graduated",
			"fieldtype": "Check",
			"width": 90,
		},
	]


def get_data(filters):
	conditions = []
	values = {}

	graduation_level = frappe.db.get_single_value("Mishkah Settings", "graduation_level")
	values["graduation_level"] = graduation_level or ""

	if filters.get("program"):
		conditions.append("pe.program = %(program)s")
		values["program"] = filters.get("program")

	if filters.get("graduated") == "Yes":
		conditions.append("IFNULL(pe.graduated, 0) = 1")
	elif filters.get("graduated") == "No":
		conditions.append("IFNULL(pe.graduated, 0) = 0")

	if filters.get("has_file") == "Yes":
		conditions.append("IFNULL(pe.graduation_certificate, '') != ''")
	elif filters.get("has_file") == "No":
		conditions.append("IFNULL(pe.graduation_certificate, '') = ''")

	where_clause = ""
	if conditions:
		where_clause = "WHERE " + " AND ".join(conditions)

	return frappe.db.sql(
		f"""
		SELECT
			pe.student,
			st.student_name,
			pe.program,
			pe.graduation_date,
			pe.graduation_certificate,
			pe.graduated,
			(
				SELECT lvl.certificate
				FROM `tabMishkah Level Enrollment` lvl
				WHERE lvl.program_enrollment = pe.name
					AND lvl.level = %(graduation_level)s
					AND IFNULL(lvl.certificate, '') != ''
				ORDER BY lvl.modified DESC
				LIMIT 1
			) as level_certificate
		FROM `tabMishkah Program Enrollment` pe
		INNER JOIN `tabMishkah Student` st ON st.name = pe.student
		{where_clause}
		ORDER BY pe.graduation_date DESC, st.student_name ASC
		""",
		values,
		as_dict=True,
	)
