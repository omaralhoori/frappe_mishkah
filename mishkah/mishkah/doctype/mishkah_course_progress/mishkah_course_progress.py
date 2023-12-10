# Copyright (c) 2023, Omar Alhori and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document

class MishkahCourseProgress(Document):
	def on_update(self):
		total = frappe.db.sql("""
			SELECT SUM(points) as total
			FROM `tabMishkah Course Progress`
			WHERE level_enrollment=%(level_enrollment)s
		""", {"level_enrollment": self.level_enrollment}, as_dict=True)
		total_points = total[0]['total']
		frappe.db.set_value("Mishkah Level Enrollment", self.level_enrollment, {"total_level_points": total_points})
		