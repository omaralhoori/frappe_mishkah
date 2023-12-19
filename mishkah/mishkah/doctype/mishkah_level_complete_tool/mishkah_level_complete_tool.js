// Copyright (c) 2023, Omar Alhori and contributors
// For license information, please see license.txt

frappe.ui.form.on("Mishkah Level Complete Tool", {
	refresh(frm) {
        frm.disable_save();
	},

    get_students(frm) {
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
                }
                frm.refresh_field("level_students");
            }
        });
    },
    create_level_progress(frm){
        var enrollments = [];
        for (var row of frm.doc.level_students){
            enrollments.push(row.enrollment);
        }
        frappe.call({
            method: "mishkah.mishkah.doctype.mishkah_level_complete_tool.mishkah_level_complete_tool.create_level_progress",
            args: {
                "level": frm.doc.level,
                "enrollments": enrollments
            },
            callback: function(r) {
                if (r.message.is_success){
                    frappe.msgprint("Level Progress Created Successfully");
                    frm.reload_doc();
                }else{
                    frappe.msgprint("Error Creating Level Progress");
                }
            }
        });

    }
});
