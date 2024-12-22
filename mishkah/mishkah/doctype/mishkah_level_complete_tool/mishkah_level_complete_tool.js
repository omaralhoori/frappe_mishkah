// Copyright (c) 2023, Omar Alhori and contributors
// For license information, please see license.txt

frappe.ui.form.on("Mishkah Level Complete Tool", {
	refresh(frm) {
        frm.disable_save();
        frm.add_custom_button("Restart", ( ) => {
            frappe.call({
                method: "mishkah.mishkah.doctype.mishkah_level_complete_tool.mishkah_level_complete_tool.restart_form"
            })
        })
	},

    get_students(frm) {
        if(frm.doc.status != "Pending"){
            frappe.msgprint("Data in progress")
            return
        }
        frappe.call({
            method: "mishkah.mishkah.doctype.mishkah_level_complete_tool.mishkah_level_complete_tool.get_students",
            args: {
                "level": frm.doc.level
            },
            callback: function(r) {
                for (var student of r.message) {
                    var row = frm.add_child("level_students");
                    row.student = student.student;
                    row.enrollment = student.enrollment;
                    row.level_points = student.points;
                    row.instructor = student.instructor_name;
                }
                frm.refresh_field("level_students");
            }
        });
    },
    create_level_progress(frm){
        if(frm.doc.status != "Pending"){
            frappe.msgprint("Data in progress")
            return
        }
        var enrollments = [];
        var instructors = [];
        for (var row of frm.doc.level_students){
            enrollments.push(row.enrollment);
            // instructors.push(row.instructor);
        }
        frappe.call({
            method: "mishkah.mishkah.doctype.mishkah_level_complete_tool.mishkah_level_complete_tool.create_level_progress_enqueue",
            args: {
                "level": frm.doc.level,
                "enrollments": enrollments,
                "old_group_names": frm.doc.group_old_names,
                "new_group_names": frm.doc.group_new_names
            },
            callback: function(r) {
                frm.reload_doc();
                // if (r.message.is_success){
                //     frappe.msgprint("Level Progress Created Successfully");
                //     frm.reload_doc();
                // }else{
                //     frappe.msgprint("Error Creating Level Progress");
                // }
            }
        });

    }
});
