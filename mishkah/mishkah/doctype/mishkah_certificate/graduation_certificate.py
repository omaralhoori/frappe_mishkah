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
    configuration = {
	'delete_harakat': False,
	'support_ligatures': True,
	'RIAL SIGN': True,  # Replace ر ي ا ل with ﷼
	}
    reshaper = arabic_reshaper.ArabicReshaper(configuration=configuration)
	
    reshaped_text = reshaper.reshape(data.name)#arabic_reshaper.reshape(data.name)
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
    configuration = {
    'delete_harakat': False,
    'support_ligatures': True,
    'RIAL SIGN': True,  # Replace ر ي ا ل with ﷼
    }
    reshaper = arabic_reshaper.ArabicReshaper(configuration=configuration)
    reshaped_text = reshaper.reshape(text)#arabic_reshaper.reshape(text)
    bidi_text = get_display(reshaped_text)
    canvas.setFillColor(color)
    canvas.drawString(position[0], position[1], bidi_text)


def get_graduation_config(program=None):
	"""Return graduation level and template (program override, else Settings)."""
	graduation_level = frappe.db.get_single_value("Mishkah Settings", "graduation_level")
	template = None
	if program:
		template = frappe.db.get_value("Mishkah Program", program, "graduation_certificate")
	if not template:
		template = frappe.db.get_single_value("Mishkah Settings", "graduation_certificate")
	return {
		"level": graduation_level,
		"template": template,
	}


def get_student_full_name(student):
	row = frappe.db.get_value(
		"Mishkah Student",
		student,
		["first_name", "middle_name", "last_name", "student_name"],
		as_dict=True,
	)
	if not row:
		return ""
	parts = [
		" ".join(str(row.first_name or "").split()),
		" ".join(str(row.middle_name or "").split()),
		" ".join(str(row.last_name or "").split()),
	]
	name = " ".join(p for p in parts if p) or (row.student_name or "")
	return name.replace("\u200f", "")


def get_graduation_level_certificate_enrollment(program_enrollment):
	"""Return graduation-level enrollment that already has a level certificate, if any."""
	config = get_graduation_config()
	graduation_level = config.get("level")
	if not graduation_level:
		return None

	rows = frappe.db.sql(
		"""
		SELECT name, certificate, instructor_name
		FROM `tabMishkah Level Enrollment`
		WHERE program_enrollment = %(program_enrollment)s
			AND level = %(graduation_level)s
			AND IFNULL(certificate, '') != ''
		ORDER BY modified DESC
		LIMIT 1
		""",
		{
			"program_enrollment": program_enrollment,
			"graduation_level": graduation_level,
		},
		as_dict=True,
	)
	return rows[0] if rows else None


@frappe.whitelist()
def can_regenerate_graduation_certificate(program_enrollment):
	"""Whether PE may regenerate graduation cert (has graduation-level cert already)."""
	level_enrollment = get_graduation_level_certificate_enrollment(program_enrollment)
	config = get_graduation_config(
		frappe.db.get_value("Mishkah Program Enrollment", program_enrollment, "program")
	)
	eligible = bool(level_enrollment and config.get("template"))
	return {
		"eligible": eligible,
		"instructor_name": (level_enrollment.instructor_name if level_enrollment else "") or "",
		"has_level_certificate": bool(level_enrollment),
		"has_template": bool(config.get("template")),
	}


@frappe.whitelist()
def regenerate_graduation_certificate(program_enrollment):
	"""Force-regenerate graduation certificate if graduation-level cert already exists."""
	level_enrollment = get_graduation_level_certificate_enrollment(program_enrollment)
	if not level_enrollment:
		frappe.throw(
			frappe._(
				"Cannot regenerate graduation certificate: student has no certificate "
				"for the configured graduation level"
			)
		)

	return create_student_graduation_certificate(
		program_enrollment,
		instructor_name=level_enrollment.instructor_name or "",
		force=True,
	)


def create_student_graduation_certificate(program_enrollment, instructor_name=None, force=False):
	"""Generate graduation PDF and store it on Program Enrollment."""
	pe = frappe.db.get_value(
		"Mishkah Program Enrollment",
		program_enrollment,
		["name", "program", "student", "graduation_certificate"],
		as_dict=True,
	)
	if not pe:
		frappe.throw(frappe._("Program Enrollment not found"))

	if pe.graduation_certificate and not force:
		return pe.graduation_certificate

	config = get_graduation_config(pe.program)
	if not config.get("template"):
		frappe.throw(frappe._("Graduation certificate template is not configured"))

	student_name = get_student_full_name(pe.student)
	if not student_name:
		frappe.throw(frappe._("Student name is missing"))

	instructor = instructor_name or ""
	certificate_date = frappe.utils.nowdate()
	file_path = create_mishkah_certificate(
		config["template"],
		student_name,
		instructor,
		certificate_date,
		"graduation/" + (pe.program or "program"),
	)

	frappe.db.set_value(
		"Mishkah Program Enrollment",
		pe.name,
		{
			"graduation_certificate": file_path,
			"graduation_date": certificate_date,
			"graduated": 1,
		},
		update_modified=True,
	)
	return file_path


@frappe.whitelist()
def create_graduation_certificate(program_enrollment, instructor_name=None, force=0):
	"""Whitelist wrapper for Certificate Creation Tool / API."""
	force = frappe.utils.cint(force)
	level_enrollment = get_graduation_level_certificate_enrollment(program_enrollment)
	if not level_enrollment:
		frappe.throw(
			frappe._(
				"Cannot create graduation certificate: student must have a certificate "
				"for the configured graduation level first"
			)
		)
	if not instructor_name:
		instructor_name = level_enrollment.instructor_name or ""
	return create_student_graduation_certificate(
		program_enrollment, instructor_name=instructor_name, force=force
	)


def maybe_issue_graduation_certificate(level_enrollment_doc):
	"""If this level is the graduation level, also issue graduation certificate on PE."""
	config = get_graduation_config()
	graduation_level = config.get("level")
	if not graduation_level or level_enrollment_doc.level != graduation_level:
		return None

	program = frappe.db.get_value(
		"Mishkah Program Enrollment",
		level_enrollment_doc.program_enrollment,
		"program",
	)
	config = get_graduation_config(program)
	if not config.get("template"):
		return None

	existing = frappe.db.get_value(
		"Mishkah Program Enrollment",
		level_enrollment_doc.program_enrollment,
		"graduation_certificate",
	)
	if existing:
		return existing

	return create_student_graduation_certificate(
		level_enrollment_doc.program_enrollment,
		instructor_name=level_enrollment_doc.instructor_name or "",
	)


@frappe.whitelist()
def generate_all_graduation_certificates(program=None):
	"""Issue graduation cert for students who already have a level certificate
	at Settings.graduation_level and no graduation_certificate yet.

	bench --site <site> execute mishkah.mishkah.doctype.mishkah_certificate.graduation_certificate.generate_all_graduation_certificates
	"""
	config = get_graduation_config()
	graduation_level = config.get("level")
	if not graduation_level:
		frappe.throw(frappe._("Graduation Level is not set in Mishkah Settings"))

	filters = {
		"graduation_level": graduation_level,
	}
	program_filter = ""
	if program:
		program_filter = "AND pe.program = %(program)s"
		filters["program"] = program

	rows = frappe.db.sql(
		f"""
		SELECT DISTINCT
			pe.name as program_enrollment,
			pe.program,
			lvl.instructor_name
		FROM `tabMishkah Level Enrollment` lvl
		INNER JOIN `tabMishkah Program Enrollment` pe
			ON pe.name = lvl.program_enrollment
		WHERE lvl.level = %(graduation_level)s
			AND IFNULL(lvl.certificate, '') != ''
			AND IFNULL(pe.graduation_certificate, '') = ''
			{program_filter}
		""",
		filters,
		as_dict=True,
	)

	created = 0
	skipped = 0
	errors = []
	for row in rows:
		try:
			prog_config = get_graduation_config(row.program)
			if not prog_config.get("template"):
				skipped += 1
				continue
			create_student_graduation_certificate(
				row.program_enrollment,
				instructor_name=row.instructor_name or "",
			)
			created += 1
			frappe.db.commit()
		except Exception as e:
			frappe.db.rollback()
			errors.append({"program_enrollment": row.program_enrollment, "error": str(e)})

	return {
		"created": created,
		"skipped": skipped,
		"errors": errors,
		"total_candidates": len(rows),
	}


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