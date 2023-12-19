// Copyright (c) 2023, Omar Alhori and contributors
// For license information, please see license.txt

frappe.ui.form.on("Mishkah Certificate", {
	refresh(frm) {
        frm.add_custom_button(__("Test Certificate"), function(){
            let d = new frappe.ui.Dialog({
                title: 'Enter details',
                fields: [
                    {
                        label: 'Student Name',
                        fieldname: 'student_name',
                        fieldtype: 'Data',
                        reqd: 1
                    },
                    {
                        label: 'Reason for Certificate',
                        fieldname: 'reason_for_certificate',
                        fieldtype: 'Data',
                        reqd: 1
                    },
                    {
                        label: 'Certificate Date',
                        fieldname: 'certificate_date',
                        fieldtype: 'Date',
                        reqd: 1
                    }
                ],
                size: 'small', // small, large, extra-large 
                primary_action_label: 'Submit',
                primary_action(values) {
                    frappe.call({
                        "method": "mishkah.mishkah.doctype.mishkah_certificate.mishkah_certificate.generate_certificate",
                        "args": {
                            "student_name": values.student_name,
                            "reason_for_certificate": values.reason_for_certificate,
                            "certificate_date": values.certificate_date,
                            "certificate": frm.doc.name
                        },
                        callback: (res) => {
                            if (res.message){
                                frappe.msgprint({
                                    title: __('Success'),
                                    indicator: 'green',
                                    message: __('Certificate Generated')
                                })
                                frm.reload_doc()
                            }else{
                                frappe.msgprint({
                                    title: __('Error'),
                                    indicator: 'red',
                                    message: __('Unable to generate certificate')
                                })
                            }
                        }
                    })
                    d.hide();
                }
            });
            
            d.show();
          });
          if (frm.doc.test_certificate){
            frm.add_custom_button(__("Preview Certificate"), function(){
                window.open(frm.doc.test_certificate, "_blank")
            })
          }
	},
});
