# import pandas as pd
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


def update_course_progress():
    frappe.db.sql("""
        update `tabMishkah Course Progress` as tbl1
            INNER JOIN `tabMishkah Level Enrollment` as tbl2 ON tbl1.level_enrollment=tbl2.name
            INNER JOIN `tabMishkah Program Enrollment` as tbl3 ON tbl2.program_enrollment=tbl3.name
            INNER JOIN `tabMishkah Student Group Student` as tbl4 ON tbl3.student=tbl4.student
        SET tbl1.student=tbl3.student, 
            tbl1.student_group=tbl4.parent
        WHERE tbl1.creation>'2024-09-15 10:06:48.239159'
""")

def update_course_student():
    frappe.db.sql("""
        update `tabMishkah Course Progress` as tbl1
            INNER JOIN `tabMishkah Level Enrollment` as tbl2 ON tbl1.level_enrollment=tbl2.name
            INNER JOIN `tabMishkah Program Enrollment` as tbl3 ON tbl2.program_enrollment=tbl3.name
        SET tbl1.student=tbl3.student
""")

def update_course_group():
    frappe.db.sql("""
        update `tabMishkah Course Progress` as tbl1
            INNER JOIN `tabMishkah Student Group Student` as tbl4 ON tbl1.student=tbl4.student
        SET tbl1.student_group=tbl4.parent
""")
 
    
def update_course_studentold():
    enrollments = frappe.db.get_all("Mishkah Program Enrollment", ["name", "student"])
    for enrollment in enrollments:
        level_enrollments = frappe.db.get_all("Mishkah Level Enrollment", {"program_enrollment": enrollment.name}, ['name'])
        for level_enrollment in level_enrollments:
            print(level_enrollment)
            frappe.db.sql("""
            UPDATE `tabMishkah Course Progress`
                SET student=%(student)s
            WHERE level_enrollment=%(level_enrollment)s
""", {"level_enrollment": level_enrollment.name, "student": enrollment.student})
            #frappe.db.set_value("Mishkah Course Progress", {"level_enrollment": level_enrollment.name}, "student", enrollment.student)
            frappe.db.commit()