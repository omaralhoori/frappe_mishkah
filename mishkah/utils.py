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