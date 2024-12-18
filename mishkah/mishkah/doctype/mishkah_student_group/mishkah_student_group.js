// Copyright (c) 2023, Omar Alhori and contributors
// For license information, please see license.txt

frappe.ui.form.on("Mishkah Student Group", {
	refresh(frm) {
        frm.add_custom_button(__('Move Selected Students'), function() {
            frm.events.move_selected_students(frm);
        }, __('Action'));
	},
    move_selected_students(frm){
        var selected = cur_frm.get_selected()
        if (!selected.students){
            return frappe.msgprint("Please Select Students To Move")
        }
        var selected_students = selected.students
        frappe.prompt({
            label: 'New Student Group',
            fieldname: 'student_group',
            fieldtype: 'Link',
            options: "Mishkah Student Group"
        }, (values) => {
            frappe.call({
                "method": "move_students",
                "doc": frm.doc,
                "args": {
                    "students": selected_students,
                    "student_group": values.student_group
                },
                callback: res =>{
                    frm.reload_doc()
                }
            })
        })
        
    }
});
