// Copyright (c) 2023, Omar Alhori and contributors
// For license information, please see license.txt

frappe.ui.form.on("Mishkah Progress Editing Tool", {
	refresh(frm) {
        frm.disable_save()
		frm.add_custom_button('Save', function() {
            frm.events.save_progress(frm);
        },);
		frm.events.generate_save_uid(frm)
	},
	save_progress(frm){
		$(`button[data-label='Save'].btn-default`).prop("disabled", true)

		var results = [];
		var enrollments = [];
		var inputs = document.querySelectorAll(".course-point-input")
		var save_uuid = $(`button[data-label='Save'].btn-default`).attr("uuid")
		for (var input of inputs){
			if (input.getAttribute("uuid") == save_uuid){
				results.push({
					"points": input.value,
					"name": input.getAttribute("progress-name"),
					"course": input.getAttribute("course"),
					"level_enrollment": input.getAttribute("enrollment-id"),
					"student_group": input.getAttribute("group-id"),
					"student": input.parentNode.getAttribute("student-id")
				})
			}
			if (!enrollments.includes(input.getAttribute("enrollment-id"))){
				enrollments.push(input.getAttribute("enrollment-id"))
			}
		}
		frappe.call({
			"method": "mishkah.mishkah.doctype.mishkah_progress_editing_tool.mishkah_progress_editing_tool.save_progress",
			"args": {
				"results": results,
				"enrollments": enrollments
			},
			callback: res =>{
				frm.events.generate_save_uid(frm)
				$(`button[data-label='Save'].btn-default`).prop("disabled", false)
				frappe.msgprint("Progress saved successfully")
				window.location.reload();
			}
		})
		
	},
	
	generate_save_uid(frm){
		var uuid = 'xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx'.replace(/[xy]/g, function (c) {
			const r = Math.random() * 16 | 0, 
				v = c == 'x' ? r : (r & 0x3 | 0x8);
			return v.toString(16);
		});
		$(`button[data-label='Save'].btn-default`).attr("uuid", uuid)
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
			<div class="table-responsive wrapper">
			<table class="table table-striped">
			${header}
			${body}
			</table>
			</div>
			`)
		var enrollments = document.querySelectorAll(".enrollment-row")
		for (var enrollment of enrollments){
			var enrollmentId = enrollment.getAttribute("enrollment-id")
			frappe.update_enrollment_stage_total(enrollmentId)
		}
		var courses = document.querySelectorAll(".course-point-input")
		for (var course of courses){
			var courseId = course.getAttribute("course")
			frappe.update_course_complete_total(courseId)
		}
	},
	render_error_message(frm){
		$(frm.fields_dict['students'].wrapper)
			.html(
				"<div>Unable to find data</div>"
			)
	},
    render_excel_table_header(frm, courses){
        var columns= '';
		for (var course of courses){
            columns += `<th course-id="${course.course}" class="first-row sticky-col" course-points="${course.course_points}" >${course.course_name} <small>(${course.course_points})</small></th>`
		}
        var html = `
            <thead> 
            <tr>
				<th>Student Name</th>
                ${columns}
				<th>Total</th>
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
			var student_progresses = [];
			if (row['courses']){
				student_courses = row['courses'].split(',')
				student_points = row['points'].split(',')
				student_progresses = row['progresses'].split(',')
			}
			var studentName = row['student_name']
			var studentId = row['student']
			var levelEnrollment = row['level_enrollment']
			var groupId = row['group_id']
            for (var i in courses){
				var course = courses[i]
				var secondClass = ""
				if (i == 0){
					//secondClass = "second-col"
				}
				var courseIndex = student_courses.indexOf(course['course'])
				if (courseIndex >= 0){
					var studentPoints = parseFloat(student_points[courseIndex]).toFixed(1)
					var progressName = student_progresses[courseIndex]
					columns += `<td style="min-width:150px;" class="${secondClass}" group-id="${groupId}" student-id="${studentId}" enrollment-id="${levelEnrollment}" course="${course['course']}" max-points=${course['course_points']}>
					${frappe.render_mark_input(levelEnrollment,groupId, studentPoints, course['course'], course['course_points'], progressName)}
					</td>`
				}else{
					columns += `<td style="min-width:200px;" class="${secondClass}" group-id="${groupId}" student-id="${studentId}" enrollment-id="${levelEnrollment}" course="${course['course']}" max-points=${course['course_points']}>
					<button class="btn btn-sm" onclick="frappe.setCourseMark(this, 100)" >Full</button>
					<button class="btn btn-sm" onclick="frappe.setCourseMark(this, 50)">Half</button>
					<button class="btn btn-sm" onclick="frappe.setCourseMark(this, 0)">Zero</button>
					</td>`
				}
                
            }
			
            html += ` <tr class="enrollment-row" enrollment-id="${levelEnrollment}">
				<td style="min-width:150px;" class="first-col sticky-col" student-id="${studentId}">${studentName}</td>
                ${columns}
				<td class="total-points">0</td>
            </tr>
            `
        }
		var courseTotal = '';
		for (var course of courses){
			courseTotal += `<td course-id="${course.course}" class="course-total">0</td>`
		}
		html += `
			<tr>
				<td>Total</td>
				${courseTotal}
			</tr>
		`
        return `<tbody>${html}</tbody>`
    },
});

frappe.render_mark_input = (enrollmentId,groupId, studentPoints, courseId, coursPoints, progressName) => {
	return `<input type="number" 
	step=".01" class="form-control course-point-input" 
	 value="${studentPoints}" 
	 course="${courseId}"
	 group-id="${groupId}"
	 enrollment-id="${enrollmentId}"
	  min="0"  max="${coursPoints}" 
	  progress-name="${progressName}"
	  max-points=${coursPoints} 
	  onchange="frappe.coursePointChanged(this)" />`;
}
frappe.coursePointChanged = (e) => {
	var parentNode = e.parentNode
	var enrollment = parentNode.getAttribute('enrollment-id')
	var group = parentNode.getAttribute('group-id')
	var student = parentNode.getAttribute('student-id')
	var maxPoints = parentNode.getAttribute('max-points')
	var courseId = parentNode.getAttribute('course')
	var progressName = e.getAttribute('progress-name')
	var points = e.value
	if (Number(maxPoints) < Number(points)){
		points = maxPoints
		e.value = maxPoints
	}else if (Number(points) < 0){
		points = 0;
		e.value = 0
	}
	if (Number(maxPoints) >= Number(points) && Number(points) >= 0){
		// if (progressName){
		// 	frappe.call({
		// 		"method": "mishkah.mishkah.doctype.mishkah_progress_editing_tool.mishkah_progress_editing_tool.set_student_mark",
		// 		args: {
		// 			"enrollment": enrollment,
		// 			"points": points,
		// 			"course": courseId,
		// 			"progress_name": progressName,
		// 			"group": group,
		// 			"student": student
		// 		},
		// 		callback: res => {
		// 			if (! res.message.is_success){
		// 				parentNode.innerHTML = res.message.message
		// 			}else{
		// 				parentNode.innerHTML = frappe.render_mark_input(enrollment, group,res.message.points, courseId, maxPoints, res.message.progress_name)
		// 			}
		// 		}
		// 	})
		// }
		frappe.update_input_uuid( e);
		
	}
	frappe.update_enrollment_stage_total(enrollment)
	frappe.update_course_complete_total(courseId)
}

frappe.update_enrollment_stage_total = (enrollment) => {
	var inputs = document.querySelectorAll(`tr[enrollment-id="${enrollment}"] .course-point-input`)
	var total = 0;
	for (var input of inputs){
		total += Number(input.value)
		frappe.set_input_color(input)
		
	}
	document.querySelector(`tr[enrollment-id="${enrollment}"] .total-points`).innerHTML = Number(total).toFixed(1);
	frappe.set_total_color(total, enrollment)
}

frappe.set_input_color = (input) =>{
	if (input.value == 0 ){
		input.style = "background: #1ed2efd6;";
	}else{
		input.style = "background: inherit";
	}
}
frappe.set_total_color = (total, enrollment) =>{
	if (total == 0 ){
		document.querySelector(`tr[enrollment-id="${enrollment}"] .first-col`).style = "background-color: #1ed2efd6;"
	}else{
		//document.querySelector(`tr[enrollment-id="${enrollment}"] .first-col`).style = "background-color: unset;"
	}
}
frappe.update_course_complete_total = (courseId) => {
	var inputs = document.querySelectorAll(`input[course="${courseId}"]`)
	var total = 0;
	for (var input of inputs){
		var courseMax = input.getAttribute("max-points")
		var points = input.value
		if (Number(points) == Number(courseMax)){
			total += 1;
		}
	}
	document.querySelector(`.course-total[course-id="${courseId}"]`).innerHTML = Number(total).toFixed(1);
}
frappe.setCourseMark = (e, markPercentage) => {
	var parentNode = e.parentNode
	var enrollment = parentNode.getAttribute('enrollment-id')
	var group = parentNode.getAttribute('group-id')
	var student = parentNode.getAttribute('student-id')
	var maxPoints = parentNode.getAttribute('max-points')
	var courseId = parentNode.getAttribute('course')
	var points = Number(maxPoints) * markPercentage / 100
	if (enrollment && maxPoints && courseId){
		parentNode.innerHTML = ''
		// frappe.call({
		// 	"method": "mishkah.mishkah.doctype.mishkah_progress_editing_tool.mishkah_progress_editing_tool.set_student_mark",
		// 	args: {
		// 		"enrollment": enrollment,
		// 		"points": points,
		// 		"course": courseId,
		// 		"group": group,
		// 		"student": student
		// 	},
		// 	callback: res => {
		// 		if (! res.message.is_success){
		// 			parentNode.innerHTML = res.message.message
		// 		}else{
		// 			//parentNode.innerHTML = frappe.render_mark_input(enrollment, group,res.message.points, courseId, maxPoints, res.message.progress_name)
		// 			parentNode.innerHTML = frappe.render_mark_input(enrollment, group,points, courseId, maxPoints, "")
		// 			frappe.update_enrollment_stage_total(enrollment)
		// 			frappe.update_course_complete_total(courseId)
		// 			frappe.update_input_uuid(parentNode.querySelector("input"))
		// 		}
				
		// 	}
		// })
		parentNode.innerHTML = frappe.render_mark_input(enrollment, group,points, courseId, maxPoints, "")
		frappe.update_enrollment_stage_total(enrollment)
		frappe.update_course_complete_total(courseId)
		frappe.update_input_uuid(parentNode.querySelector("input"))
	}
	
}

frappe.update_input_uuid = (input) => {
	var saveUUID = $(`button[data-label='Save'].btn-default`).attr("uuid");
	input.setAttribute("uuid", saveUUID);
}