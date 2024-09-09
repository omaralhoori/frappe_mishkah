// Copyright (c) 2023, Omar Alhori and contributors
// For license information, please see license.txt

frappe.ui.form.on("Mishkah Course", {
	refresh(frm) {
        frm.add_custom_button("Update Progress Points", function(){
            let d = new frappe.ui.Dialog({
                title: 'Enter details',
                fields: [
                    {
                        label: 'Old Points',
                        fieldname: 'old_points',
                        fieldtype: 'Int',
                        reqd: 1
                    },
                    {
                        label: 'New Points',
                        fieldname: 'new_points',
                        fieldtype: 'Int',
                        reqd: 1
                    }
                ],
                size: 'small', // small, large, extra-large 
                primary_action_label: 'Submit',
                primary_action(values) {
                    frappe.show_progress('Loading..', 70, 100, 'Please wait');
                    frappe.call({
                        "method": "update_course_enrollment_points",
                        "doc": frm.doc,
                        "args": {
                            "old_points": values.old_points,
                            "new_points": values.new_points
                        },
                        "callback": res=> {
                            frappe.hide_progress()
                        }
                    })
                    d.hide();
                }
            });
            
            d.show();
            
        })
	},
});
