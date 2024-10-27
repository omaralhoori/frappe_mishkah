// Copyright (c) 2023, Omar Alhori and contributors
// For license information, please see license.txt

frappe.ui.form.on("Mishkah Level Enrollment", {
	refresh(frm) {
        frm.add_custom_button(__("Generate Certificate"), function() {
            //frm.set_value("application_status", "Approved");
            frm.events.generate_certificate(frm)
        });
	},
    generate_certificate(frm){
        frappe.call({
            "method": "generate_certificate",
            "doc": frm.doc,
            "callback": res=>{
                frm.reload_doc()
            }
        })
    }
});
