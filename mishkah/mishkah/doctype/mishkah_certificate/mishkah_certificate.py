# Copyright (c) 2023, Omar Alhori and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document
from PIL import Image, ImageDraw, ImageFont
import json
from io import BytesIO
import base64
import re
class MishkahCertificate(Document):
	pass


@frappe.whitelist()
def generate_certificate(certificate,student_name, reason_for_certificate,certificate_date, save_as_file=False):
	certificate_doc = frappe.get_doc("Mishkah Certificate", certificate)
	template = Image.open(get_file_path(certificate_doc.certificate_image))
	draw = ImageDraw.Draw(template)
	certificate_configurations = json.loads(certificate_doc.certificate_configuration)
	if certificate_configurations.get("name-font-size"):
		name_font_size = int(certificate_configurations.get("name-font-size"))
	else:
		name_font_size = 12
	if certificate_configurations.get("reason-font-size"):
		reason_font_size = int(certificate_configurations.get("reason-font-size"))
	else:
		reason_font_size = 12
	if certificate_configurations.get("date-font-size"):
		date_font_size = int(certificate_configurations.get("date-font-size"))
	else:
		date_font_size = 12
	name_font_path = get_file_path(frappe.db.get_value("Mishkah Font", certificate_doc.name_font, "font_file",cache=True))
	reason_font_path = get_file_path(frappe.db.get_value("Mishkah Font", certificate_doc.reason_font, "font_file",cache=True))
	date_font_path = get_file_path(frappe.db.get_value("Mishkah Font", certificate_doc.date_font, "font_file",cache=True))
	name_font = ImageFont.truetype(name_font_path, int(name_font_size))
	reason_font = ImageFont.truetype(reason_font_path, int(reason_font_size))
	date_font = ImageFont.truetype(date_font_path, int(date_font_size))

	if certificate_configurations.get("font-color"):
		font_color = certificate_configurations.get("font-color")
	else:
		font_color = "black"
	if certificate_configurations.get("name-position"):
		name_position = tuple(certificate_configurations.get("name-position"))
	else:
		name_position = (0,0)
	if certificate_configurations.get("reason-position"):
		reason_position = certificate_configurations.get("reason-position")
	else:
		reason_position = (0,0)
	if certificate_configurations.get("date-position"):
		date_position = certificate_configurations.get("date-position")
	else:
		date_position = (0,0)
	if certificate_configurations.get("date-format"):
		date_format = certificate_configurations.get("date-format")
	else:
		date_format = "%d %B %Y"
	_, _, text_width, text_height = draw.textbbox((0, 0), student_name, font=name_font)
	#text_width, text_height = draw.textsize(student_name, name_font)
	margin = text_width//4
	# name_position = (name_position[0] - margin, name_position[1])
	name_position = (name_position[0] - margin, name_position[1])
	text_width, text_height = draw.textsize(reason_for_certificate, reason_font)
	margin = text_width//4
	reason_position = (reason_position[0] - margin, reason_position[1])

	draw.text(name_position, student_name, font_color, font=name_font)
	draw.text(reason_position, reason_for_certificate, font_color, font=reason_font)
	draw.text(date_position, certificate_date, font_color, font=date_font)
	if save_as_file:
		filename = certificate_doc.name + "-" + student_name + ".png"
		filename = re.sub(r'[^\w_. -]', '_', filename)
		certificate_file_path = frappe.get_site_path("public", "files", filename)
		template.save(certificate_file_path)
		return  f"/files/{filename}"
	else:
		return pil_image_to_base64(template)
	


def get_file_path(file_name):
	if file_name.startswith("/files"):
		return frappe.get_site_path("public", "files", file_name.split("/")[-1])
	else:
		return frappe.get_site_path("private", "files", file_name.split("/")[-1])
	

# Convert the PIL.Image to a base64 string
def pil_image_to_base64(image):
    buffered = BytesIO()
    image.save(buffered, format="JPEG")  # You can specify the desired image format (JPEG, PNG, etc.)
    return base64.b64encode(buffered.getvalue()).decode("utf-8")

def get_x_position(x_position, text, font_size, image_width):
	text_count = len(text)
	text_width = text_count * font_size
	margin = text_width//8
	return x_position - margin