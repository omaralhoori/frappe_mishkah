# Copyright (c) 2023, Omar Alhori and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document


def trim_name_part(value):
	"""Strip leading/trailing spaces and collapse repeated spaces inside a name part."""
	if not value:
		return ""
	return " ".join(str(value).split())


def build_student_fullname(first_name=None, middle_name=None, last_name=None):
	parts = [
		trim_name_part(first_name),
		trim_name_part(middle_name),
		trim_name_part(last_name),
	]
	return " ".join(part for part in parts if part)


class MishkahStudent(Document):
	def validate(self):
		self.trim_and_set_fullname()

	def on_update(self):
		if (
			self.has_value_changed("student_name")
			or self.has_value_changed("first_name")
			or self.has_value_changed("middle_name")
			or self.has_value_changed("last_name")
		):
			self.update_student_name_in_doctypes()

	def trim_and_set_fullname(self):
		self.first_name = trim_name_part(self.first_name)
		self.middle_name = trim_name_part(self.middle_name)
		self.last_name = trim_name_part(self.last_name)
		self.student_name = build_student_fullname(
			self.first_name, self.middle_name, self.last_name
		)

	def update_student_name_in_doctypes(self):
		"""Sync trimmed student_name to related documents."""
		update_related_student_names(self.name, self.student_name)


def update_related_student_names(student, student_name):
	"""Update student_name in related Mishkah doctypes for one student."""
	frappe.db.sql(
		"""
		UPDATE `tabMishkah Student Group Student`
		SET student_name = %(student_name)s
		WHERE student = %(student)s
		""",
		{"student": student, "student_name": student_name},
	)
	frappe.db.sql(
		"""
		UPDATE `tabMishkah Program Enrollment`
		SET student_name = %(student_name)s
		WHERE student = %(student)s
		""",
		{"student": student, "student_name": student_name},
	)
	frappe.db.sql(
		"""
		UPDATE `tabMishkah Level Enrollment` lvl
		INNER JOIN `tabMishkah Program Enrollment` pe
			ON pe.name = lvl.program_enrollment
		SET lvl.student_name = %(student_name)s
		WHERE pe.student = %(student)s
		""",
		{"student": student, "student_name": student_name},
	)


@frappe.whitelist()
def trim_all_student_names():
	"""Trim all Mishkah Student name parts, rebuild student_name, and sync related docs."""
	students = frappe.db.sql(
		"""
		SELECT name, first_name, middle_name, last_name, student_name
		FROM `tabMishkah Student`
		""",
		as_dict=True,
	)

	updated_students = 0
	for student in students:
		first_name = trim_name_part(student.first_name)
		middle_name = trim_name_part(student.middle_name)
		last_name = trim_name_part(student.last_name)
		student_name = build_student_fullname(first_name, middle_name, last_name)

		changed = (
			first_name != (student.first_name or "")
			or middle_name != (student.middle_name or "")
			or last_name != (student.last_name or "")
			or student_name != (student.student_name or "")
		)
		if not changed:
			continue

		frappe.db.sql(
			"""
			UPDATE `tabMishkah Student`
			SET
				first_name = %(first_name)s,
				middle_name = %(middle_name)s,
				last_name = %(last_name)s,
				student_name = %(student_name)s
			WHERE name = %(name)s
			""",
			{
				"name": student.name,
				"first_name": first_name,
				"middle_name": middle_name,
				"last_name": last_name,
				"student_name": student_name,
			},
		)
		update_related_student_names(student.name, student_name)
		updated_students += 1

	# Final sync pass for any related rows still out of date
	frappe.db.sql(
		"""
		UPDATE `tabMishkah Student Group Student` sgs
		INNER JOIN `tabMishkah Student` s ON s.name = sgs.student
		SET sgs.student_name = s.student_name
		WHERE IFNULL(sgs.student_name, '') != IFNULL(s.student_name, '')
		"""
	)
	frappe.db.sql(
		"""
		UPDATE `tabMishkah Program Enrollment` pe
		INNER JOIN `tabMishkah Student` s ON s.name = pe.student
		SET pe.student_name = s.student_name
		WHERE IFNULL(pe.student_name, '') != IFNULL(s.student_name, '')
		"""
	)
	frappe.db.sql(
		"""
		UPDATE `tabMishkah Level Enrollment` lvl
		INNER JOIN `tabMishkah Program Enrollment` pe
			ON pe.name = lvl.program_enrollment
		INNER JOIN `tabMishkah Student` s ON s.name = pe.student
		SET lvl.student_name = s.student_name
		WHERE IFNULL(lvl.student_name, '') != IFNULL(s.student_name, '')
		"""
	)

	frappe.db.commit()
	return {
		"updated_students": updated_students,
		"total_students": len(students),
	}
