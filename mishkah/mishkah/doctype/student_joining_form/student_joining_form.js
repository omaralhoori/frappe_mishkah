// Copyright (c) 2024, Omar Alhori and contributors
// For license information, please see license.txt

frappe.ui.form.on("Student Joining Form", {
	refresh(frm) {

	},
    onload(frm){
        frm.set_query("student_group", function() {
            return {
                "filters": {
                    "level": frm.doc.program_level || "ssss",
                    "group_type": "Student Subgroup"
                }
            };
        });
    }
});
