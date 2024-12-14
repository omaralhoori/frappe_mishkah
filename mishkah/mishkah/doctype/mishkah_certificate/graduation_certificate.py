from reportlab.pdfgen import canvas # pip install reportlab
from reportlab.lib.pagesizes import C9
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfbase import pdfmetrics

from PyPDF2 import PdfReader, PdfWriter

import arabic_reshaper # pip install arabic-reshaper
from bidi.algorithm import get_display # pip install python-bidi
import unittest
import frappe
from frappe.tests.test_commands import BaseTestCommands
import io
from frappe.utils import get_site_name
# Create a canvas to draw on the PDF
from frappe.utils import cstr
# bench --site alrewaq.erp  execute education.certificate.test_create_certificate
import json
import re
import random

from pathlib import Path

def create_mishkah_certificate(certificate_template, student_name, instructor_name, certificate_date, level):
    certificate_doc = frappe.get_doc("Mishkah Certificate", certificate_template)
    certificate_configuration = certificate_doc.certificate_configuration
    if type(certificate_configuration) == str:
        certificate_configuration = json.loads(certificate_configuration)
    name_font = frappe.db.get_value("Mishkah Font", certificate_doc.name_font,"font_file",cache=True)
    instructor_font = frappe.db.get_value("Mishkah Font", certificate_doc.reason_font,"font_file",cache=True)
    date_font = frappe.db.get_value("Mishkah Font", certificate_doc.date_font,"font_file",cache=True)
    configuration = {
        "position": {
            "name": certificate_configuration['name-position'],
            "instructor": certificate_configuration['reason-position'],
            "date": certificate_configuration['date-position'],
        },
        "font": {
            "name": name_font,
            "instructor": instructor_font,
            "date": date_font,
        },
        "size": {
            "name": certificate_configuration['name-font-size'],
            "instructor": certificate_configuration['reason-font-size'],
            "date": certificate_configuration['date-font-size'],
        },
        "color": {
            "name": "#c3923e",
            "instructor": "#444444",
            "date": "#444444",

        }
    }
    randint = random.randint(11111, 99999)
    site_name = cstr(frappe.local.site)
    filename = student_name + "_"+ certificate_template + "_" + str(randint) +".pdf"
    filename = re.sub(r'[^\w_. -]', '_', filename)
    dir_name =  level + "/" +instructor_name
    dirname = re.sub(r'[^\w_. -]', '_', dir_name)
    output = site_name + '/public/files/student_certificate/' + dirname 
    file_name = "/files/student_certificate/" + dirname + "/"  + filename
    Path(output).mkdir(parents=True, exist_ok=True)
    output = output + "/"  + filename
    create_pdf_certificate(certificate_doc.certificate_pdf, output, configuration,  frappe._dict({
            "name": student_name,
            "date": str(certificate_date),
            "instructor": instructor_name
        }))
    return file_name


def create_pdf_certificate(template_path, output_path, configs, data):
    print(data)
    print(configs)
    reader = PdfReader(get_file_path(template_path))
    writer = PdfWriter()
    template_page = reader.pages[0]
    writer.add_page(template_page)
    template_width = template_page.mediabox.width
    template_height = template_page.mediabox.height
    packet = io.BytesIO()
    c = canvas.Canvas(packet, pagesize=(template_width,  template_height), lang="ar")
    print(template_width, template_height)
    # Register and set the font (ensure this font supports Arabic characters)
    pdfmetrics.registerFont(TTFont(configs['font']['name'], get_file_path(configs['font']['name'])))
    pdfmetrics.registerFont(TTFont(configs['font']['instructor'], get_file_path(configs['font']['instructor'])))
    pdfmetrics.registerFont(TTFont(configs['font']['date'], get_file_path(configs['font']['date'])))

    # Draw Name
    c.setFont(configs['font']['name'], configs['size']['name'])

    # Draw text on the canvas
    # c.drawString(configs.get("name_position")[0], configs.get("name_position")[1], f"{data.student_name}")
    # c.drawString(configs.date_position[0], configs.date_position[1], f"Date: {data.date}")
    # c.drawString(configs.grade_position[0], configs.grade_position[1], f"Grade: {data.grade}")
    reshaped_text = arabic_reshaper.reshape(data.name)
    bidi_text = get_display(reshaped_text)
    text_width = pdfmetrics.stringWidth(bidi_text, configs['font']['name'], configs['size']['name'])

    x_position = (float(template_width) - float(text_width)) / 2  
    print((x_position,configs['position']["name"][1]))
    draw_arabic_text(c, data.name, (x_position,configs['position']["name"][1]), configs["color"]['name'])
    c.setFont(configs['font']['date'], configs['size']['date'])
    draw_arabic_text(c, data.date, configs['position']["date"], configs["color"]['date'])

    c.setFont(configs['font']['instructor'], configs['size']['instructor'])
    
    draw_arabic_text(c, data.instructor, configs['position']['instructor'], configs['color']['instructor'])

    # Save the canvas to the output file
    c.save()

    # with open(output_path, "wb") as f:
    #     writer.write(f)
    packet.seek(0)

    # Create a new PDF with the text overlay
    overlay_pdf = PdfReader(packet)
    overlay_page = overlay_pdf.pages[0]

    # Merge the overlay PDF with the template PDF
    writer = PdfWriter()

    # Add the template page
    template_page.merge_page(overlay_page)
    writer.add_page(template_page)

    # Save the final output to a file
    with open(output_path, "wb") as output_file:
        writer.write(output_file)


    print(f"Certificate saved as {output_path}")

def get_file_path(file_path):
    site_name = cstr(frappe.local.site)
    if file_path.startswith("/files"):
        return site_name + "/public" + file_path
    if file_path.startswith("/private"):
        return site_name +  file_path
    return file_path

def draw_arabic_text(canvas, text, position, color):
    reshaped_text = arabic_reshaper.reshape(text)
    bidi_text = get_display(reshaped_text)
    canvas.setFillColor(color)
    canvas.drawString(position[0], position[1], bidi_text)


def generate_all_enrollments_certificates(length=100, one_batch=False):
    skip = 0
    while True:
        enrollments = frappe.db.sql("""
            SELECT name from `tabMishkah Level Enrollment`
        WHERE certificate is null and total_level_points > 0 and (instructor_name is not null or instructor_name != "")
        LIMIT {skip},{length}
        """.format(length=length, skip=skip), as_dict=True)
        print(len(enrollments))
        for enrollment in enrollments:
            enrollment_doc = frappe.get_doc("Mishkah Level Enrollment", enrollment.name)
            enrollment_doc.generate_certificate()
            enrollment_doc.save()
            frappe.db.commit()
        skip += length
        if len(enrollments) < length or one_batch:
            break

def generate_level_enrollments_certificates(level, batch,  length=100, one_batch=False):
    skip = 0
    while True:
        enrollments = frappe.db.sql("""
            SELECT name from `tabMishkah Level Enrollment`
        WHERE 
            level=%(level)s
            and batch={batch} and total_level_points > 0 
            and (instructor_name is not null or instructor_name != "")
        LIMIT {skip},{length}
        """.format(length=length, skip=skip, batch=batch),{"level": level}, as_dict=True)
        print(len(enrollments))
        for enrollment in enrollments:
            enrollment_doc = frappe.get_doc("Mishkah Level Enrollment", enrollment.name)
            enrollment_doc.generate_certificate()
            enrollment_doc.batch= batch + 1
            enrollment_doc.save()
            frappe.db.commit()
        skip += length
        if len(enrollments) < length or one_batch:
            break

def generate_level_enrollments_certificates_instructor_name(instructor_name, batch, length=100, one_batch=False):
    skip = 0
    while True:
        enrollments = frappe.db.sql("""
            SELECT name from `tabMishkah Level Enrollment`
        WHERE 
            instructor_name=%(instructor_name)s
            and total_level_points > 0  and batch={batch}
        LIMIT {skip},{length}
        """.format(length=length, skip=skip, batch=batch),{"instructor_name": instructor_name}, as_dict=True)
        print(len(enrollments))
        for enrollment in enrollments:
            enrollment_doc = frappe.get_doc("Mishkah Level Enrollment", enrollment.name)
            enrollment_doc.generate_certificate()
            enrollment_doc.batch= batch + 1
            enrollment_doc.save()
            frappe.db.commit()
        skip += length
        if len(enrollments) < length or one_batch:
            break