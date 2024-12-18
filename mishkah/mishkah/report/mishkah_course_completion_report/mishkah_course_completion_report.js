// Copyright (c) 2024, Omar Alhori and contributors
// For license information, please see license.txt
/* eslint-disable */

frappe.query_reports["Mishkah Course Completion Report"] = {
	"filters": [
		{
			"fieldname":"Course",
			"label": __("Course"),
			"fieldtype": "Link",
			"options":"Mishkah Course",
			"reqd": 1
		}
	]
};
