# Copyright (c) 2023, Omar Alhori and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document

class MishkahCourseProgress(Document):
	def on_update(self):
		return
		total = frappe.db.sql("""
			SELECT SUM(points) as total
			FROM `tabMishkah Course Progress`
			WHERE level_enrollment=%(level_enrollment)s
		""", {"level_enrollment": self.level_enrollment}, as_dict=True)
		total_points = total[0]['total']
		frappe.db.set_value("Mishkah Level Enrollment", self.level_enrollment, {"total_level_points": total_points})
		

def update_level_enrollment_points(level_enrollment=None):
	frappe.db.sql("""
		UPDATE `tabMishkah Level Enrollment` as tbl1 
		INNER JOIN (
		SELECT level_enrollment, SUM(points) as total
			FROM `tabMishkah Course Progress`
		GROUP BY level_enrollment
		) as tbl2 ON tbl1.name=tbl2.level_enrollment
		SET total_level_points=tbl2.total
""")