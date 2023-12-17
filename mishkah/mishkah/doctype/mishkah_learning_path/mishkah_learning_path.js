// Copyright (c) 2023, Omar Alhori and contributors
// For license information, please see license.txt

// frappe.ui.form.on("Mishkah Learning Path", {
// 	refresh(frm) {

// 	},
// });


frappe.ui.form.on('Mishkah Learning Path Stage', {
	stages_add: function(frm){
		frm.fields_dict['stages'].grid.get_field('course').get_query = function(doc){
			var courses_list = [];
			$.each(doc.stages, function(idx, val){
				if (val.course) courses_list.push(val.course);
			});
			return { filters: [['Mishkah Course', 'name', 'not in', courses_list]] };
		};
	}
});