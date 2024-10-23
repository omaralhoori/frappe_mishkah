frappe.listview_settings['Mishkah Level Enrollment'] = {
	onload: function(listview){
		listview.page.add_menu_item("Set Missing Data",  () => {
			//var selected = listview.get_checked_items().map(item => item.name)
            let d = new frappe.ui.Dialog({
                title: 'Enter details',
                fields: [
                    {
                        label: 'Level',
                        fieldname: 'level',
                        fieldtype: 'Link',
                        options: 'Mishkah Program Level'
                    },
                ],
                size: 'small', // small, large, extra-large 
                primary_action_label: 'Submit',
                primary_action(values) {
                    frappe.call({
                        method: "mishkah.mishkah.doctype.mishkah_level_complete_tool.mishkah_level_complete_tool.set_level_enrollment_missing_data",
                        args: {
                            level_type: values.level
                        }
                        ,callback: () => {
                            listview.refresh();
                        }
                    })
                    d.hide();
                }
            });
            
            d.show();
			
		})
	}
};
