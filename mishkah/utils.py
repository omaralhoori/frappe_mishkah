# import pandas as pd
import frappe
import time
import csv
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

def delete_students_for_level_enq(level):
    frappe.enqueue(delete_students_for_level, queue="long", timeout=10000, level=level)


def delete_students_for_level(level):
    groups = frappe.db.get_all("Mishkah Student Group", {"level": level, "group_type": "Student Subgroup"})
    for group in groups:
        group_doc = frappe.get_doc("Mishkah Student Group", group.name)
        for student in group_doc.students:
            try:
                program_enrollment = frappe.get_doc("Mishkah Program Enrollment", {"student": student.student})
                # levels = frappe.db.get_all("Mishkah Level Enrollment", {
                #     "program_enrollment": program_enrollment.name,
                #     "level": ["in", "الدفعة الجديدة," + level]
                # })
                # for l in levels:
                #     #level_doc = frappe.get_doc("Mishkah Level Enrollment", {"program_enrollment": program_enrollment.name})
                #     frappe.delete_doc("Mishkah Level Enrollment", l.name)
                program_enrollment.delete()
                group_doc.remove(student)
                group_doc.save()
                frappe.delete_doc("Mishkah Student", student.student)
                
                frappe.db.commit()
            except:
                group_doc.remove(student)
                group_doc.save()
                frappe.db.commit()




import json
def delete_duplication_by_json():
    with open("duplicates.json", "r") as f:
        data = json.load(f)
    delete_names = []
    for record in data:
        same_points = len(set(record['points'].split(","))) == 1
        if not same_points: continue
        names = record['ids'].split(",")
        i = len(names) - 1
        while i > 0:
            delete_names.append(names[i])
            i -= 1
    
    batch_size = 100
    print(delete_names)
    for i in range(0, len(delete_names), batch_size):
        batch = delete_names[i:i+batch_size]
        print("Deleting ", batch)
        joined = ",".join(["'%s'" % x for x in batch])
        frappe.db.sql(f"""
            DELETE FROM `tabMishkah Course Progress`
            WHERE name in ({joined})
    """)
    frappe.db.commit()


def update_progress():
    with open("duplicates.json", "r") as f:
        data = json.load(f)
    enrollments = []
    for record in data:
        enrollments.append(record['level_enrollment'])
    enrollments = set(enrollments)

    for enrollment in enrollments:
        total = frappe.db.sql("""
            SELECT SUM(points) as total
            FROM `tabMishkah Course Progress`
            WHERE level_enrollment=%(level_enrollment)s
        """, {"level_enrollment": enrollment}, as_dict=True)
        basic_total = frappe.db.sql("""
            SELECT SUM(points) as total
            FROM `tabMishkah Course Progress` as tbl1
            INNER JOIN `tabMishkah Course` as tbl2 on tbl1.course=tbl2.name
            WHERE tbl1.level_enrollment=%(level_enrollment)s and tbl2.basic_course=1
        """, {"level_enrollment": enrollment}, as_dict=True)
        total_points = total[0]['total']
        basic_total_points = basic_total[0]['total'] or 0
        frappe.db.set_value("Mishkah Level Enrollment", enrollment, {"total_level_points": total_points, "basic_total_level_points": basic_total_points})
    
    frappe.db.commit()
"""
[
  "first_name",
  "column_break_yqja",
  "middle_name",
  "column_break_3ti7",
  "last_name",
  "section_break_jem7",
  "student_email",
  "column_break_kmlp",
  "student_mobile",
  "section_break_imvp",
  "nationality",
  "section_break_4pjq",
  "country_of_residence",
  "age_category",
  "educational_level",
  "column_break_hc15",
  "employed",
  "marital_status",
  "childrenif_exist",
  "specialty",
  "section_break_t4sn",
  "user",
  "student_name",
  "section_break_8xqv",
  "enrollment_status",
  "student_group"
 ],
"""

# get all students for a level that registered groups
# for each student, get student data and group name and add to a list
def get_students_for_level(level, limit=None):
    students = []
    groups = frappe.db.get_all("Mishkah Student Group", {"level": level, "group_type": "Student Subgroup"}, ["name", "student_group_name"])
    print(f"Found {len(groups)} groups for level {level}")
    count = 0
    for group in groups[:limit]:
        group_doc = frappe.get_doc("Mishkah Student Group", group.name)
        for student in group_doc.students:
            student_doc = frappe.get_doc("Mishkah Student", student.student)
            students.append({
                "student": student_doc.name,
                "first_name": student_doc.first_name,
                "middle_name": student_doc.middle_name,
                "last_name": student_doc.last_name,
                "student_email": student_doc.student_email,
                "student_mobile": student_doc.student_mobile,
                "nationality": student_doc.nationality,
                "country_of_residence": student_doc.country_of_residence,
                "age_category": student_doc.age_category,
                "educational_level": student_doc.educational_level,
                "employed": student_doc.employed,
                "marital_status": student_doc.marital_status,
                "childrenif_exist": student_doc.childrenif_exist,
                "specialty": student_doc.specialty,
                "user": student_doc.user,
                "student_name": student_doc.student_name,
                "enrollment_status": student_doc.enrollment_status,
                "student_group": group.name,
                "group_name": group.student_group_name})
        #print(f"Added {len(students)} students for level {level}")
        count += 1

        print(f"Processed {count} / {len(groups)} groups, Found {len(group_doc.students)} students for group {group.name}")

    # write to a csv file use timestamp as part of the filename
    if len(students) > 0:
        with open(f"students_{level}_{time.time()}.csv", "w") as f:
            writer = csv.writer(f)
            writer.writerow(students[0].keys())
            for student in students:
                writer.writerow(student.values())
    else:
        print(f"No students found for level {level}")
    return students

def delete_students_with_related_records(students):
    count = 0
    for student in students:
        # delete from student group students
        frappe.db.sql("""
            DELETE FROM `tabMishkah Student Group Student`
            WHERE student=%(student)s and parent=%(group)s
        """, {"student": student.get('student'), "group": student.get('student_group')})
        # get program enrollment
        program_enrollment = frappe.db.get_value("Mishkah Program Enrollment", {"student": student.get('student')}, "name")
        # delete from level enrollments
        frappe.db.sql("""
            DELETE FROM `tabMishkah Level Enrollment`
            WHERE program_enrollment=%(program_enrollment)s
        """, {"program_enrollment": program_enrollment})
        # delete from program enrollments
        frappe.db.sql("""
            DELETE FROM `tabMishkah Program Enrollment`
            WHERE name=%(program_enrollment)s
        """, {"program_enrollment": program_enrollment})
        # delete from students
        frappe.db.sql("""
            DELETE FROM `tabMishkah Student`
            WHERE name=%(student)s
        """, {"student": student.get('student')})
        count += 1
        if count % 100 == 0:
            print(f"Deleted {count} / {len(students)} students")
    print(f"Deleted {count} students")