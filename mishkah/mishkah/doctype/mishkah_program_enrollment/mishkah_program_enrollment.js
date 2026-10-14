// Copyright (c) 2023, Omar Alhori and contributors
// For license information, please see license.txt

frappe.ui.form.on("Mishkah Program Enrollment", {
	refresh(frm) {
		if (frm.is_new()) {
			return;
		}
		frm.events.setup_regenerate_graduation_button(frm);
	},

	setup_regenerate_graduation_button(frm) {
		frappe.call({
			method:
				"mishkah.mishkah.doctype.mishkah_certificate.graduation_certificate.can_regenerate_graduation_certificate",
			args: {
				program_enrollment: frm.doc.name,
			},
			callback: (res) => {
				if (!(res.message && res.message.eligible)) {
					return;
				}
				frm.add_custom_button(__("Regenerate Graduation Certificate"), () => {
					frappe.confirm(
						__(
							"Regenerate the graduation certificate? The previous file will be replaced."
						),
						() => {
							frappe.call({
								method:
									"mishkah.mishkah.doctype.mishkah_certificate.graduation_certificate.regenerate_graduation_certificate",
								args: {
									program_enrollment: frm.doc.name,
								},
								freeze: true,
								freeze_message: __("Generating certificate..."),
								callback: (r) => {
									if (r.message) {
										frm.reload_doc();
										frappe.show_alert({
											message: __("Graduation certificate regenerated"),
											indicator: "green",
										});
										window.open(r.message, "_blank");
									}
								},
							});
						}
					);
				});
			},
		});
	},
});
