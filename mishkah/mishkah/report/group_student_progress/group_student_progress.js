// Copyright (c) 2025, Omar Alhori and contributors
// For license information, please see license.txt
/* eslint-disable */

frappe.query_reports["Group Student Progress"] = {
	"filters": [
		{
			"label": __("Level"),
			"fieldname": "level",
			"fieldtype": "Link",
			"options": "Mishkah Program Level",
			"reqd": 1
		},
		{
			"label": __("Term"),
			"fieldname": "term",
			"fieldtype": "Link",
			"options": "Mishkah Educational Term",
			"reqd": 1
		},
	]
};
