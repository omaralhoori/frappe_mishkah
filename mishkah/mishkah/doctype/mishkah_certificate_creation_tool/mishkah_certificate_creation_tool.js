// Copyright (c) 2024, Omar Alhori and contributors
// For license information, please see license.txt

frappe.ui.form.on("Mishkah Certificate Creation Tool", {
	refresh(frm) {
        frm.disable_save()
	},
    get_students(frm){
        $('button[data-fieldname="get_students"]').prop("disabled", true)
        $(frm.fields_dict['students'].wrapper)
			.html(`Loadin...`)
        frappe.call({
			"method": "mishkah.mishkah.doctype.mishkah_certificate_creation_tool.mishkah_certificate_creation_tool.get_students",
			"args": {
				"student_group": frm.doc.student_group
			},
			callback: (res) => {
                $('button[data-fieldname="get_students"]').prop("disabled", false)
				
                if (res.message){
					frm.events.render_students_table(frm, res.message)
				}else{
					frm.events.render_error_message(frm)
				}
			}
		})
    },
    render_students_table(frm, table_data){
		var header = frm.events.render_excel_table_header(frm)
		var body = frm.events.render_excel_table_body(frm, table_data )
		$(frm.fields_dict['students'].wrapper)
			.html(`
			<div class="table-responsive wrapper">
			<table class="table table-striped">
			${header}
			${body}
			</table>
			</div>
			`)
	},
	render_error_message(frm){
		$(frm.fields_dict['students'].wrapper)
			.html(
				"<div>Unable to find data</div>"
			)
	},
    render_excel_table_header(frm){

        var html = `
            <thead> 
            <tr>
				<th>Student Name</th>
                <th>Instructor Name</th>
                <th>Points</th>
                <th>Certificate Type</th>
                <th>Certificate</th>
                <th>Action</th>
            </tr>
            </thead>
        `;
        return html;
    },

    render_excel_table_body(frm, data){
        var html = ``
        for (var row of data){
            var certificate = ""
            if(row.certificate){
                certificate = `<a href="${row.certificate}" target="_blank">${row.certificate}</a>`
            }
            html += ` <tr>
                    <td>${row.student_name}</td>
                    <td>${row.instructor_name}</td>
                    <td>${row.total_level_points}</td>
                    <td>${row.certificate_name}</td>
                    <td class="certificate">${certificate}</td>
                    <td>
                        <button 
                            class="btn btn-sm" 
                            level-enrollment="${row.level_enrollment}" 
                            student="${row.student}" 
                            instructor-name="${row.instructor_name}"
                            onclick="frappe.create_certificate(this)">
                            Create Certificate
                        </button>
                    </td>
                </tr>
            `
        }
        return `<tbody>${html}</tbody>`
    },
    
});

frappe.create_certificate = (e) => {
    var student = e.getAttribute("student")
    var level_enrollment = e.getAttribute("level-enrollment")
    var instructor_name = e.getAttribute("instructor-name")
    e.setAttribute("disabled", true)
    frappe.call({
        "method": "mishkah.mishkah.doctype.mishkah_certificate_creation_tool.mishkah_certificate_creation_tool.create_certificate",
        "args": {
            "level_enrollment": level_enrollment,
            "instructor_name": instructor_name
        },
        callback: res=>{
            e.setAttribute("disabled", false)
            if (res.message){
                var certificate_field = e.parentNode.parentNode.querySelector("td.certificate")
                certificate_field.innerHTML = `<a href="${res.message}" target="_blank">${res.message}</a>`
            }
        }
    })
}