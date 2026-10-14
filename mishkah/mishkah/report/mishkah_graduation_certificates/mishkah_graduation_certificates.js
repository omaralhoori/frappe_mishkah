// Copyright (c) 2024, Omar Alhori and contributors
// For license information, please see license.txt
/* eslint-disable */

frappe.query_reports["Mishkah Graduation Certificates"] = {
	filters: [
		{
			fieldname: "program",
			label: __("Program"),
			fieldtype: "Link",
			options: "Mishkah Program",
		},
		{
			fieldname: "graduated",
			label: __("Graduated"),
			fieldtype: "Select",
			options: "\nYes\nNo",
		},
		{
			fieldname: "has_file",
			label: __("Has File"),
			fieldtype: "Select",
			options: "\nYes\nNo",
		},
	],
};
