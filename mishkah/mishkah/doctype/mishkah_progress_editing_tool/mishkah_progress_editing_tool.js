// Copyright (c) 2023, Omar Alhori and contributors
// For license information, please see license.txt

frappe.ui.form.on("Mishkah Progress Editing Tool", {
	refresh(frm) {
        frm.disable_save()

	},
	get_students(frm){
		frappe.call({
			"method": "mishkah.mishkah.doctype.mishkah_progress_editing_tool.mishkah_progress_editing_tool.get_students",
			"args": {
				"student_group": frm.doc.student_group,
				"level_stage": frm.doc.level_stage
			},
			callback: (res) => {
				if (res.message){
					frm.events.render_students_table(frm, res.message)
				}else{
					frm.events.render_error_message(frm)
				}
			}
		})
	},
	render_students_table(frm, table_data){
		var header = frm.events.render_excel_table_header(frm, table_data['courses'])
		var body = frm.events.render_excel_table_body(frm, table_data['students'], table_data['courses'])
		$(frm.fields_dict['students'].wrapper)
			.html(`
			<div class="table-responsive">
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
    render_excel_table_header(frm, courses){
        var columns= '';
		console.log(courses)
        for (var course of courses){
            columns += `<th course-id="${course.course}" course-points="${course.course_points}" >${course.course_name} <small>(${course.course_points})</small></th>`
        }
        var html = `
            <thead> 
            <tr>
				<th>Student Name</th>
                ${columns}
            </tr>
            </thead>
        `;
        return html;
    },
    render_excel_table_body(frm, data, courses){
        var html = ``
		// var courses_map = {}
		// for (var course of courses){
		// 	courses_map[course['course_id']] = {
		// 		"points": course['course_points'],
		// 		"name": courses['course_name']
		// 	}
		// }
		// map courses to header
        for (var row of data){
            var columns = ''
			var student_courses = [];
			var student_points = [];
			if (row['courses']){
				student_courses = row['courses'].split(',')
				student_points = row['points'].split(',')
			}
			var studentName = row['student_name']
			var studentId = row['student']
			var levelEnrollment = row['level_enrollment']
            for (var i in courses){
				var course = courses[i]
				
				var courseIndex = student_courses.indexOf(course['course'])
				if (courseIndex >= 0){
					var studentPoints = parseFloat(student_points[courseIndex]).toFixed(1)
					columns += `<td style="min-width:150px;"><input type="number" step=".01" class="form-control"  value="${studentPoints}" course="${course['course']}" min="0"  max="${course['course_points']}" max-points=${course['course_points']} onchange="coursePointChanged(this)" /></td>`
				}else{
					columns += `<td style="min-width:200px;" enrollment-id="${levelEnrollment}" course="${course['course']}" max-points=${course['course_points']}>
					<button class="btn btn-sm" onclick="frappe.setCourseMark(this, 100)" >Full</button>
					<button class="btn btn-sm" onclick="frappe.setCourseMark(this, 50)">Half</button>
					<button class="btn btn-sm" onclick="frappe.setCourseMark(this, 0)">Zero</button>
					</td>`
				}
                
            }
			
            html += ` <tr>
				<td style="min-width:150px;" student-id="${studentId}">${studentName}</td>
                ${columns}
            </tr>
            `
        }

        return `<tbody>${html}</tbody>`
    }
});


frappe.setCourseMark = (e, markPercentage) => {
	var parentNode = e.parentNode
	var enrollment = parentNode.getAttribute('enrollment-id')
	var maxPoints = parentNode.getAttribute('max-points')
	var courseId = parentNode.getAttribute('course')
	var points = Number(maxPoints) * markPercentage / 100
	if (enrollment && maxPoints && courseId){
		parentNode.innerHTML = ''
		frappe.call({
			"method": "mishkah.mishkah.doctype.mishkah_progress_editing_tool.mishkah_progress_editing_tool.set_student_mark",
			args: {
				"enrollment": enrollment,
				"points": points,
				"course": courseId
			},
			callback: res => {
				parentNode.innerHTML = res.message
			}
		})
	}
	
}