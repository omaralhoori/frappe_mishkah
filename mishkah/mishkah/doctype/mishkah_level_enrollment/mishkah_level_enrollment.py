# Copyright (c) 2023, Omar Alhori and contributors
# For license information, please see license.txt

from mishkah.mishkah.doctype.mishkah_certificate.graduation_certificate import create_mishkah_certificate
import frappe
from frappe.model.document import Document

class MishkahLevelEnrollment(Document):
	@frappe.whitelist()
	def generate_certificate(self):
		certificate_template = None
		certificates = frappe.db.sql("""
			SELECT min_points, certificate
				FROM `tabMishkah Level Certificate Item` tbl1
				INNER JOIN `tabMishkah Level Certificate` tbl2 ON tbl1.parent=tbl2.name
			WHERE tbl2.level=%(level)s
			ORDER BY min_points desc
		""", {"level": self.level}, as_dict=True)
		for certificate in certificates:
			if self.total_level_points >= certificate['min_points']:
				certificate_template = certificate
				break
		if not certificate_template:
			return
		
		student_name = frappe.db.sql("""
			SELECT concat(tbl2.first_name, " ", tbl2.middle_name," ", tbl2.last_name ) as student_name
			FROM `tabMishkah Program Enrollment` as tbl1
			INNER JOIN `tabMishkah Student` as tbl2 ON tbl1.student=tbl2.name
			WHERE tbl1.name=%(enrollment)s
			""", {"enrollment": self.program_enrollment},as_dict=True)[0]["student_name"]
		file = create_mishkah_certificate(certificate_template.certificate, student_name, self.instructor_name or "", frappe.utils.nowdate(), self.level)
		self.certificate = file
		self.certificate_name = certificate_template.certificate
		self.certificate_type = certificate_template.certificate
		self.db_set("certificate", file)
		self.db_set("certificate_name", certificate_template.certificate)
		self.db_set("certificate_type", certificate_template.certificate)