# Copyright (c) 2023, Omar Alhori and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document
from frappe import _
class MishkahStudentJoiningRequest(Document):
	def before_insert(self):
		if self.gender == 'Male':
			frappe.throw("هذا برنامج مخصص للإناث فقط")
		if self.age_category == 'Under 18':
			frappe.throw("لا يمكننا اسقبال طلبك")
		# if frappe.db.exists("Mishkah Student Joining Request", {"mobile_phone": self.mobile_phone}):
		# 	frappe.throw(_("This mobile number has been registered in Mishkah before"))
	def after_insert(self):
		if frappe.db.get_single_value("Mishkah Settings", "auto_approve_new_requests"):
			self.approve_request(program=frappe.db.get_single_value("Mishkah Settings", "default_joining_program"),
						level=frappe.db.get_single_value("Mishkah Settings", "default_joining_level"))
			if self.whatsapp_group:
				frappe.msgprint(_("Your whatsapp group link:") + "\n" + f"<a href='{self.whatsapp_group}'>{self.whatsapp_group}</a>")	
	@frappe.whitelist()
	def approve_request(self, program, level=None):
		student = self.create_student()
		program_enrollment = self.create_program_enrollment(student, program)
		if level:
			self.create_level_enrollment(program_enrollment, level)
			self.add_student_to_group(program=program, level=level, student=student.name)
		self.db_set("status", "Approved")
		return {"success_key": 1}
	
	def create_student(self):
		mobile = str(self.mobile_phone)
		# if mobile.startswith("0"):
		# 	mobile = mobile[1:]
		# if mobile.startswith("\u0660"):
		# 	mobile = mobile[1:]
		mobile = self.country_code + mobile
		if frappe.db.exists("Mishkah Student", {"student_mobile": mobile}):
			frappe.throw("Student already exists!")
		student_doc = frappe.get_doc({
			"doctype": "Mishkah Student",
			"first_name": self.first_name,
			"middle_name": self.middle_name,
			"last_name": self.last_name,
			"student_mobile": mobile,
			"nationality": self.nationality,
			"employed": 1 if self.employed == "Yes" else 0,
			"marital_status": self.marital_status,
			 "childrenif_exist": self.childrenif_exist,
			 "specialty": self.specialty,
			 "age_category": self.age_category,
			 "educational_level": self.educational_level,
			 "country_of_residence": self.country_of_residence,
			 "enrollment_status":"عضوية فعالة"
		})
		student_doc.save(ignore_permissions=True)
		return student_doc
		
	def create_program_enrollment(self, student, program):
		enrollment = frappe.get_doc({
			"doctype": "Mishkah Program Enrollment",
			"program": program,
			"student": student.name,
			"enrollment_date": frappe.utils.nowdate()
		})

		enrollment.insert(ignore_permissions=True)
		return enrollment
	
	def create_level_enrollment(self, program_enrollment, level):
		enrollment = frappe.get_doc({
			"doctype": "Mishkah Level Enrollment",
			"program_enrollment": program_enrollment.name,
			"level": level,
			"enrollment_date": frappe.utils.nowdate(),
			"educational_term": frappe.db.get_single_value("Mishkah Settings", "current_educational_term"),
			"enrollment_status": "Ongoing"
		})

		enrollment.insert(ignore_permissions=True)
		return enrollment
	
	def add_student_to_group(self, program, level, student):
		groups = frappe.db.sql("""
		SELECT name FROM `tabMishkah Student Group` 
					  WHERE 
						 program=%(program)s 
						 AND level=%(level)s 
						 AND group_type='Student Subgroup'
						 AND students_count < max_students
					  ORDER BY cast(student_group_name as unsigned)
		""", {"program": program, "level": level}, as_dict=True) #students_count desc
		if len(groups) == 0:
			frappe.get_doc({
				"doctype": "Mishkah Errors",
				"reference_doctype": self.doctype,
				"reference_name": self.name,
				"error": f"""Cannot find available group for student:{self.country_code} - {str(self.mobile_phone)}, program:{program}, level :{level}"""
			}).insert(ignore_permissions=True)
			return
		student_group = frappe.get_doc("Mishkah Student Group", groups[0].get('name'), )
		student_row = student_group.append("students")
		student_row.student = student
		student_row.is_active = 1
		student_group.save(ignore_permissions=True)
		self.db_set("whatsapp_group", student_group.whatsapp_link)

# @frappe.whitelist(allow_guest=True)
# def test_groups(program, level):
# 	return frappe.db.sql("""
# 		SELECT name FROM `tabMishkah Student Group` 
# 					  WHERE program=%(program)s AND level=%(level)s AND students_count < max_students
# 					  ORDER BY students_count desc
# 		""", {"program": program, "level": level}, as_dict=True)
	

@frappe.whitelist()
def mark_student_whatsapp_send(group_student):
	frappe.db.set_value("Mishkah Student Group Student", group_student, "link_sent", 1)