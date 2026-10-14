# Copyright (c) 2023, Omar Alhori and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document


class MishkahCourseProgress(Document):
	def on_update(self):
		recalculate_enrollment_points(self.level_enrollment)

	def after_delete(self):
		# Recalculate after delete so enrollment totals stay correct
		if self.level_enrollment:
			recalculate_enrollment_points(self.level_enrollment)


def recalculate_enrollment_points(level_enrollment):
	"""Recalculate total and basic points for one Mishkah Level Enrollment."""
	if not level_enrollment:
		return None

	total = frappe.db.sql(
		"""
		SELECT IFNULL(SUM(points), 0) as total
		FROM `tabMishkah Course Progress`
		WHERE level_enrollment=%(level_enrollment)s
		""",
		{"level_enrollment": level_enrollment},
		as_dict=True,
	)
	basic_total = frappe.db.sql(
		"""
		SELECT IFNULL(SUM(tbl1.points), 0) as total
		FROM `tabMishkah Course Progress` as tbl1
		INNER JOIN `tabMishkah Course` as tbl2 ON tbl1.course=tbl2.name
		WHERE tbl1.level_enrollment=%(level_enrollment)s AND tbl2.basic_course=1
		""",
		{"level_enrollment": level_enrollment},
		as_dict=True,
	)
	total_points = total[0]["total"] or 0
	basic_total_points = basic_total[0]["total"] or 0
	frappe.db.set_value(
		"Mishkah Level Enrollment",
		level_enrollment,
		{
			"total_level_points": total_points,
			"basic_total_level_points": basic_total_points,
		},
		update_modified=False,
	)
	return {
		"level_enrollment": level_enrollment,
		"total_level_points": total_points,
		"basic_total_level_points": basic_total_points,
	}


@frappe.whitelist()
def recalculate_level_points(level=None, level_enrollment=None):
	"""Recalculate total_level_points and basic_total_level_points.

	Use after deleting course progress / achievements so enrollment totals stay correct.

	Examples:
	  # All enrollments for a level
	  bench --site <site> execute \\
	    mishkah.mishkah.doctype.mishkah_course_progress.mishkah_course_progress.recalculate_level_points \\
	    --kwargs "{'level': 'LEVEL-NAME'}"

	  # One enrollment
	  bench --site <site> execute \\
	    mishkah.mishkah.doctype.mishkah_course_progress.mishkah_course_progress.recalculate_level_points \\
	    --kwargs "{'level_enrollment': 'ENROLLMENT-NAME'}"
	"""
	if not level and not level_enrollment:
		frappe.throw(frappe._("Please provide level or level_enrollment"))

	if level_enrollment:
		result = recalculate_enrollment_points(level_enrollment)
		frappe.db.commit()
		return {"updated": 1, "results": [result]}

	if not frappe.db.exists("Mishkah Program Level", level):
		frappe.throw(frappe._("Level {0} not found").format(level))

	frappe.db.sql(
		"""
		UPDATE `tabMishkah Level Enrollment` AS le
		LEFT JOIN (
			SELECT level_enrollment, IFNULL(SUM(points), 0) AS total
			FROM `tabMishkah Course Progress`
			GROUP BY level_enrollment
		) AS t ON t.level_enrollment = le.name
		LEFT JOIN (
			SELECT tbl1.level_enrollment, IFNULL(SUM(tbl1.points), 0) AS basic_total
			FROM `tabMishkah Course Progress` AS tbl1
			INNER JOIN `tabMishkah Course` AS tbl2
				ON tbl1.course = tbl2.name AND tbl2.basic_course = 1
			GROUP BY tbl1.level_enrollment
		) AS b ON b.level_enrollment = le.name
		SET
			le.total_level_points = IFNULL(t.total, 0),
			le.basic_total_level_points = IFNULL(b.basic_total, 0)
		WHERE le.level = %(level)s
		""",
		{"level": level},
	)
	updated = frappe.db.sql(
		"""
		SELECT COUNT(*) FROM `tabMishkah Level Enrollment`
		WHERE level = %(level)s
		""",
		{"level": level},
	)[0][0]
	frappe.db.commit()
	return {
		"level": level,
		"updated": updated,
	}


def update_level_enrollment_points(level_enrollment=None, level=None):
	"""Backward-compatible wrapper; prefer recalculate_level_points."""
	return recalculate_level_points(level=level, level_enrollment=level_enrollment)
