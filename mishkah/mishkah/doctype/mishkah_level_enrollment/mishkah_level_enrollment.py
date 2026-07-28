# Copyright (c) 2023, Omar Alhori and contributors
# For license information, please see license.txt

from mishkah.mishkah.doctype.mishkah_certificate.graduation_certificate import create_mishkah_certificate
import frappe
from frappe.model.document import Document


def get_basic_courses_for_level(level):
	"""Cached basic course names for a level (learning path + basic_course=1)."""
	cache = frappe.cache()
	cache_key = f"mishkah:basic_courses:{level}"
	courses = cache.get_value(cache_key)
	if courses is not None:
		return courses

	courses = frappe.db.sql_list("""
		SELECT DISTINCT lps.course
		FROM `tabMishkah Learning Path Stage` lps
		INNER JOIN `tabMishkah Course` c ON c.name = lps.course AND c.basic_course = 1
		WHERE lps.parent = %(level)s
	""", {"level": level}) or []
	cache.set_value(cache_key, courses, expires_in_sec=3600)
	return courses


class MishkahLevelEnrollment(Document):
	def has_completed_all_basic_courses(self):
		"""True when every basic course for this level has progress on this
		enrollment with points > 0. Uses indexed level_enrollment filter only.
		"""
		basic_courses = get_basic_courses_for_level(self.level)
		if not basic_courses:
			return False

		# level_enrollment is indexed; one enrollment has ~50 rows, not millions
		completed = frappe.db.sql("""
			SELECT COUNT(*)
			FROM `tabMishkah Course Progress`
			WHERE level_enrollment = %(level_enrollment)s
				AND points > 0
				AND course IN %(courses)s
		""", {
			"level_enrollment": self.name,
			"courses": tuple(basic_courses),
		})[0][0]

		return completed >= len(basic_courses)

	@frappe.whitelist()
	def generate_certificate(self):
		certificates = frappe.db.sql("""
			SELECT min_points, certificate, min_basic_points
				FROM `tabMishkah Level Certificate Item` tbl1
				INNER JOIN `tabMishkah Level Certificate` tbl2 ON tbl1.parent=tbl2.name
			WHERE tbl2.level=%(level)s
			ORDER BY min_points asc
		""", {"level": self.level}, as_dict=True)

		if not certificates:
			frappe.throw("Cannot find certificate")

		all_basic_completed = self.has_completed_all_basic_courses()
		certificate_template = None

		if all_basic_completed:
			# All certificates available; use total_level_points
			for certificate in reversed(certificates):
				if self.total_level_points >= certificate["min_points"]:
					certificate_template = certificate
					break
		else:
			# Only silver (lowest min_points); use basic_total_level_points
			silver_certificate = certificates[0]
			if self.basic_total_level_points >= silver_certificate["min_basic_points"]:
				certificate_template = silver_certificate

		if not certificate_template:
			frappe.throw("Cannot find certificate")

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
		return self.certificate
