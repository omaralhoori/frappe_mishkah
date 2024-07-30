frappe.ready(function() {
	frappe.web_form.handle_success = (e) => {
		//frappe.msgprint(__('Thank You for applying!'));
		console.log(e)
		if (e.whatsapp_group){
			window.location = e.whatsapp_group
		}
		//frappe.web_form.success_url;
		}
})
