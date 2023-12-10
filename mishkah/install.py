import frappe


def after_install():
	create_roles()


def create_roles():
	desk_roles = ["Mishkah Instructor", "Mishkah Data Entry Specialist", "Mishkah Data Manager", "Mishkah Joining Request Approver"]
	other_roles = ["Mishkah Student"]
	for role in desk_roles:
		if not frappe.db.exists("Role", role):
			frappe.get_doc({"doctype": "Role", "role_name": role, "desk_access": 1}).save()
	for role in other_roles:
		if not frappe.db.exists("Role", role):
			frappe.get_doc({"doctype": "Role", "role_name": role, "desk_access": 0}).save()
