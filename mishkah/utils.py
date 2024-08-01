import pandas as pd
import frappe
def cancel_students():
    sheet = pd.read_excel("cancel_students.xlsx", )
    students = sheet.values[:,0]
    #groups = sheet.values[:,2]
    for student in students:
        student_groups = frappe.db.get_all("Mishkah Student Group Student", {"student": student}, ['parent'])
        print(student_groups)
        for group in student_groups:
            group_doc = frappe.get_doc("Mishkah Student Group", group.get('parent'))
            for ss in group_doc.students:
                if ss.student == student:
                    print("found")
                    group_doc.remove(ss)
                    group_doc.save()
                    break
        program_enrollment = frappe.db.get_value("Mishkah Program Enrollment", {"student": student}, ['name'])
        if program_enrollment:
            levels = frappe.db.get_all("Mishkah Level Enrollment", {"program_enrollment": program_enrollment}, ['name'])
            for level in levels:
                frappe.delete_doc("Mishkah Level Enrollment", level['name'])
            frappe.delete_doc("Mishkah Program Enrollment",program_enrollment)
        frappe.delete_doc("Mishkah Student", student)
        frappe.db.commit()


def fix_numbers():
    data = frappe.db.get_all("Mishkah Student Joining Request", ["name","country_code", "mobile_phone"])
    for item in data:
        name, code, mobile = item.get('name'), item.get('country_code'), item.get('mobile_phone')
        if margin:=check_mobile(mobile):
            new_mobile = fix_mobile_no(mobile,margin)
            student = frappe.db.get_value("Mishkah Student", {"student_mobile": code + mobile}, ["name"])
            # if frappe.db.exists("Mishkah Student", {"student_mobile": code + new_mobile}):
            #     continue
            try:
                frappe.db.set_value("Mishkah Student", student, "student_mobile", code + new_mobile)
                frappe.db.set_value("Mishkah Student Joining Request", name, "mobile_phone", new_mobile)
            except:
                pass

def check_mobile(mobile):
    if mobile.startswith("+"): return 1
    if mobile.startswith("0"): return 1
    if mobile.startswith("00"): return 2
    if mobile.startswith("\u0660"): return 1
    if mobile.startswith("\u0660\u0660"): return 2
    return 0

def fix_mobile_no(mobile, margin):
    return mobile[margin:]