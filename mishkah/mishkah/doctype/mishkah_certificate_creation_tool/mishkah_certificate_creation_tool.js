// Copyright (c) 2024, Omar Alhori and contributors
// For license information, please see license.txt

frappe.ui.form.on("Mishkah Certificate Creation Tool", {
	refresh(frm) {
		frm.disable_save();
		frm._is_graduation_level = false;
	},
	get_students(frm) {
		$('button[data-fieldname="get_students"]').prop("disabled", true);
		$(frm.fields_dict["students"].wrapper).html(`Loading...`);
		frappe.call({
			method:
				"mishkah.mishkah.doctype.mishkah_certificate_creation_tool.mishkah_certificate_creation_tool.get_students",
			args: {
				student_group: frm.doc.student_group,
			},
			callback: (res) => {
				$('button[data-fieldname="get_students"]').prop("disabled", false);
				if (res.message) {
					frm._is_graduation_level = !!res.message.is_graduation_level;
					frm.events.render_students_table(frm, res.message.students || []);
				} else {
					frm.events.render_error_message(frm);
				}
			},
		});
	},
	render_students_table(frm, table_data) {
		var header = frm.events.render_excel_table_header(frm);
		var body = frm.events.render_excel_table_body(frm, table_data);
		$(frm.fields_dict["students"].wrapper).html(`
			<div class="table-responsive wrapper">
			<table class="table table-striped">
			${header}
			${body}
			</table>
			</div>
			`);
	},
	render_error_message(frm) {
		$(frm.fields_dict["students"].wrapper).html("<div>Unable to find data</div>");
	},
	render_excel_table_header(frm) {
		var graduation_cols = "";
		if (frm._is_graduation_level) {
			graduation_cols = `
				<th>${__("Graduation Certificate")}</th>
				<th>${__("Graduation Action")}</th>
			`;
		}
		return `
            <thead>
            <tr>
				<th>${__("Student Name")}</th>
                <th>${__("Instructor Name")}</th>
				<th>${__("Points")}</th>
                <th>${__("Basic Points")}</th>
                <th>${__("Basic Courses")}</th>
                <th>${__("All Basic Completed")}</th>
                <th>${__("Certificate Type")}</th>
                <th>${__("Certificate")}</th>
                <th>${__("Action")}</th>
				${graduation_cols}
            </tr>
            </thead>
        `;
	},

	render_excel_table_body(frm, data) {
		var html = ``;
		for (var row of data) {
			var certificate = "";
			if (row.certificate) {
				certificate = `<a href="${row.certificate}" target="_blank">${row.certificate}</a>`;
			}
			var basicCourses = `${row.completed_basic_courses || 0}/${row.total_basic_courses || 0}`;
			var allBasicCompleted = row.all_basic_completed ? "Yes" : "No";
			var basicCoursesClass = row.all_basic_completed ? "text-success" : "";

			var graduation_cols = "";
			if (frm._is_graduation_level) {
				var graduation_cert = "";
				if (row.graduation_certificate) {
					graduation_cert = `<a href="${row.graduation_certificate}" target="_blank">${row.graduation_certificate}</a>`;
				}
				var has_level_certificate = !!row.certificate;
				var graduation_btn = has_level_certificate
					? `<button
							class="btn btn-sm btn-primary create-graduation-certificate"
							program-enrollment="${row.program_enrollment || ""}"
							instructor-name="${row.instructor_name || ""}"
							onclick="frappe.create_graduation_certificate(this)">
							${__("Create Graduation Certificate")}
						</button>`
					: `<button
							class="btn btn-sm btn-primary create-graduation-certificate"
							program-enrollment="${row.program_enrollment || ""}"
							instructor-name="${row.instructor_name || ""}"
							disabled
							title="${__("Create level certificate first")}">
							${__("Create Graduation Certificate")}
						</button>`;
				graduation_cols = `
					<td class="graduation-certificate">${graduation_cert}</td>
					<td class="graduation-action">${graduation_btn}</td>
				`;
			}

			html += ` <tr>
                    <td>${row.student_name || ""}</td>
                    <td>${row.instructor_name || ""}</td>
                    <td>${row.total_level_points || 0}</td>
                    <td>${row.basic_total_level_points || 0}</td>
                    <td class="${basicCoursesClass}">${basicCourses}</td>
                    <td class="${basicCoursesClass}">${allBasicCompleted}</td>
                    <td>${row.certificate_name || ""}</td>
                    <td class="certificate">${certificate}</td>
                    <td>
                        <button
                            class="btn btn-sm"
                            level-enrollment="${row.level_enrollment}"
                            student="${row.student}"
                            instructor-name="${row.instructor_name || ""}"
                            program-enrollment="${row.program_enrollment || ""}"
                            onclick="frappe.create_certificate(this)">
                            ${__("Create Certificate")}
                        </button>
                    </td>
					${graduation_cols}
                </tr>
            `;
		}
		return `<tbody>${html}</tbody>`;
	},
});

frappe.create_certificate = (e) => {
	var level_enrollment = e.getAttribute("level-enrollment");
	var instructor_name = e.getAttribute("instructor-name");
	e.setAttribute("disabled", true);
	frappe.call({
		method:
			"mishkah.mishkah.doctype.mishkah_certificate_creation_tool.mishkah_certificate_creation_tool.create_certificate",
		args: {
			level_enrollment: level_enrollment,
			instructor_name: instructor_name,
		},
		callback: (res) => {
			e.setAttribute("disabled", false);
			if (res.message) {
				var row = e.parentNode.parentNode;
				var certificate_field = row.querySelector("td.certificate");
				var path = res.message.certificate || res.message;
				if (certificate_field && path) {
					certificate_field.innerHTML = `<a href="${path}" target="_blank">${path}</a>`;
				}
				var graduation_field = row.querySelector("td.graduation-certificate");
				if (graduation_field && res.message.graduation_certificate) {
					graduation_field.innerHTML = `<a href="${res.message.graduation_certificate}" target="_blank">${res.message.graduation_certificate}</a>`;
				}
				var graduation_btn = row.querySelector("button.create-graduation-certificate");
				if (graduation_btn && path) {
					graduation_btn.removeAttribute("disabled");
					graduation_btn.removeAttribute("title");
					graduation_btn.setAttribute(
						"onclick",
						"frappe.create_graduation_certificate(this)"
					);
				}
			}
		},
	});
};

frappe.create_graduation_certificate = (e) => {
	var program_enrollment = e.getAttribute("program-enrollment");
	var instructor_name = e.getAttribute("instructor-name");
	if (!program_enrollment) {
		frappe.msgprint(__("Program Enrollment is missing"));
		return;
	}
	var row = e.parentNode.parentNode;
	var has_level_certificate =
		row.querySelector("td.certificate a") ||
		(row.querySelector("td.certificate") &&
			(row.querySelector("td.certificate").textContent || "").trim());
	if (!has_level_certificate) {
		frappe.msgprint(
			__("Cannot create graduation certificate before the level certificate is issued")
		);
		return;
	}
	e.setAttribute("disabled", true);
	frappe.call({
		method:
			"mishkah.mishkah.doctype.mishkah_certificate.graduation_certificate.create_graduation_certificate",
		args: {
			program_enrollment: program_enrollment,
			instructor_name: instructor_name,
		},
		callback: (res) => {
			e.setAttribute("disabled", false);
			if (res.message) {
				var graduation_field = row.querySelector("td.graduation-certificate");
				if (graduation_field) {
					graduation_field.innerHTML = `<a href="${res.message}" target="_blank">${res.message}</a>`;
				}
			}
		},
	});
};
