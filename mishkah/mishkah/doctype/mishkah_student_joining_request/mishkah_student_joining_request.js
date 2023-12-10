// Copyright (c) 2023, Omar Alhori and contributors
// For license information, please see license.txt

frappe.ui.form.on("Mishkah Student Joining Request", {
	refresh(frm) {
            if (!frm.is_new() && frm.doc.status==="Applied") {
                frm.add_custom_button(__("Approve"), function() {
                    frm.events.approve(frm)
                }, 'Actions');
                
    
                frm.add_custom_button(__("Reject"), function() {
                    frm.set_value("status", "Rejected");
                    frm.save_or_update();
                }, 'Actions');
            }
        },
            
        
        async approve(frm) {
            let d = new frappe.ui.Dialog({
                title: 'Enter details',
                fields: [
                    {
                        label: 'Program',
                        fieldname: 'joining_program',
                        fieldtype: 'Link',
                        options: 'Mishkah Program',
                        reqd: 1,
                        default: await frappe.db.get_single_value("Mishkah Settings", "default_joining_program")
                    },
                    {
                        label: 'Level',
                        fieldname: 'joining_level',
                        fieldtype: 'Link',
                        options: 'Mishkah Program Level',
                        default: await frappe.db.get_single_value("Mishkah Settings", "default_joining_level")
                    },
                ],
                size: 'small', // small, large, extra-large 
                primary_action_label: 'Submit',
                primary_action(values) {
                    frm.call({
                        method: "approve_request",
                        doc: frm.doc,
                        args: {
                            program: values.joining_program,
                            level: values.joining_level,
                        },
                        callback: (res) => {
                            if(res.message.success_key){
                                frappe.msgprint("Student Created Successfully")
                                frm.reload_doc()
                            }
                        }
                    })
                    d.hide();
                }
            });
            
            d.show();

           
        }
});
