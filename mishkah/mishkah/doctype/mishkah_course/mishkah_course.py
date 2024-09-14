# Copyright (c) 2023, Omar Alhori and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document

class MishkahCourse(Document):
	@frappe.whitelist()
	def update_course_enrollment_points(self, old_points, new_points):
		frappe.only_for("Mishkah Data Manager")
		new_point_ratio = new_points / old_points
		frappe.db.sql("""
			UPDATE `tabMishkah Course Progress`
				SET points=points*{new_ratio}
			WHERE course=%(course_name)s;
			""".format(new_ratio=new_point_ratio), {"course_name": self.name})
		frappe.db.sql("""
			UPDATE
				`tabMishkah Level Enrollment` as lvl
			INNER JOIN (
				select level_enrollment, SUM(points) as total
				FROM `tabMishkah Course Progress`
				GROUP BY  level_enrollment
				) as crs ON  crs.level_enrollment=lvl.name
			set lvl.total_level_points=total
		""")
		