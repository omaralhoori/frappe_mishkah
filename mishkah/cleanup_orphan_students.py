# Copyright (c) 2026, Omar Alhori and contributors
# For license information, please see license.txt

"""
Delete Mishkah students who are not in any group and have no course progress,
along with their joining requests and enrollments.

Designed for large / busy sites:
- one student per short transaction (avoids long locks)
- retry on lock wait timeout
- small job batches on the long queue, then re-enqueue
"""

import time

import frappe
from frappe.exceptions import QueryTimeoutError

BATCH_SIZE = 20
MAX_RETRIES = 5
RETRY_SLEEP_SEC = 2
BETWEEN_STUDENTS_SLEEP_SEC = 0.05
EMPTY_JOB_BACKOFF_SEC = 5
JOB_NAME = "mishkah_delete_orphan_students"

ORPHAN_WHERE = """
	NOT EXISTS (
		SELECT 1
		FROM `tabMishkah Student Group Student` sgs
		WHERE sgs.student = s.name
	)
	AND NOT EXISTS (
		SELECT 1
		FROM `tabMishkah Course Progress` cp
		WHERE cp.student = s.name
	)
	AND NOT EXISTS (
		SELECT 1
		FROM `tabMishkah Course Progress` cp
		INNER JOIN `tabMishkah Level Enrollment` le ON le.name = cp.level_enrollment
		INNER JOIN `tabMishkah Program Enrollment` pe ON pe.name = le.program_enrollment
		WHERE pe.student = s.name
	)
"""


def count_orphan_students():
	"""Return how many students match the orphan criteria."""
	return frappe.db.sql(f"""
		SELECT COUNT(*) as total
		FROM `tabMishkah Student` s
		WHERE {ORPHAN_WHERE}
	""")[0][0]


def get_orphan_students(limit=BATCH_SIZE):
	"""Fetch one batch of orphan students (name + mobile for joining-request match)."""
	return frappe.db.sql(f"""
		SELECT s.name as student, s.student_name, s.student_mobile
		FROM `tabMishkah Student` s
		WHERE {ORPHAN_WHERE}
		ORDER BY s.creation
		LIMIT %(limit)s
	""", {"limit": int(limit)}, as_dict=True)


def delete_one_orphan_student(student, student_mobile=None):
	"""
	Delete a single orphan student and related rows in one short transaction.
	Returns True if deleted, False if skipped after lock retries.
	"""
	for attempt in range(1, MAX_RETRIES + 1):
		try:
			if student_mobile:
				frappe.db.sql("""
					DELETE FROM `tabMishkah Student Joining Request`
					WHERE CONCAT(IFNULL(country_code, ''), IFNULL(mobile_phone, '')) = %(mobile)s
				""", {"mobile": student_mobile})

			program_enrollments = frappe.db.sql("""
				SELECT name
				FROM `tabMishkah Program Enrollment`
				WHERE student = %(student)s
			""", {"student": student}, as_dict=True)

			for pe in program_enrollments:
				frappe.db.sql("""
					DELETE FROM `tabMishkah Level Enrollment`
					WHERE program_enrollment = %(program_enrollment)s
				""", {"program_enrollment": pe.name})
				frappe.db.sql("""
					DELETE FROM `tabMishkah Program Enrollment`
					WHERE name = %(program_enrollment)s
				""", {"program_enrollment": pe.name})

			frappe.db.sql("""
				DELETE FROM `tabMishkah Level Complete Tool Student`
				WHERE student = %(student)s
			""", {"student": student})

			frappe.db.sql("""
				DELETE FROM `tabMishkah Student`
				WHERE name = %(student)s
			""", {"student": student})

			frappe.db.commit()
			return True

		except QueryTimeoutError:
			frappe.db.rollback()
			if attempt >= MAX_RETRIES:
				frappe.logger("mishkah").warning(
					f"Orphan cleanup skipped {student} after {MAX_RETRIES} lock timeouts"
				)
				return False
			time.sleep(RETRY_SLEEP_SEC * attempt)


def delete_orphan_students_batch(students):
	"""Delete students one-by-one with short commits to avoid lock contention."""
	if not students:
		return {"deleted": 0, "skipped": 0}

	deleted = 0
	skipped = 0

	for row in students:
		ok = delete_one_orphan_student(row.student, row.student_mobile)
		if ok:
			deleted += 1
		else:
			skipped += 1
		time.sleep(BETWEEN_STUDENTS_SLEEP_SEC)

	return {"deleted": deleted, "skipped": skipped}


def delete_orphan_students_job(batch_size=BATCH_SIZE, empty_streak=0):
	"""Process one batch, then enqueue the next until no orphans remain."""
	batch_size = int(batch_size or BATCH_SIZE)
	empty_streak = int(empty_streak or 0)
	students = get_orphan_students(limit=batch_size)

	if not students:
		frappe.logger("mishkah").info("Orphan student cleanup finished: nothing left to delete")
		return {"deleted": 0, "remaining": 0, "done": True}

	result = delete_orphan_students_batch(students)
	remaining = count_orphan_students()

	frappe.logger("mishkah").info(
		f"Orphan student cleanup: deleted {result['deleted']}, "
		f"skipped {result['skipped']}, remaining ~{remaining}"
	)

	if remaining == 0:
		return {
			"deleted": result["deleted"],
			"skipped": result["skipped"],
			"remaining": 0,
			"done": True,
		}

	# If nothing was deleted (all locked), back off and retry a few times then stop
	if result["deleted"] == 0:
		empty_streak += 1
		if empty_streak >= 5:
			frappe.logger("mishkah").error(
				"Orphan student cleanup stopped: repeated lock timeouts. Re-run later."
			)
			return {
				"deleted": 0,
				"skipped": result["skipped"],
				"remaining": remaining,
				"done": False,
				"stopped": True,
			}
		time.sleep(EMPTY_JOB_BACKOFF_SEC * empty_streak)
	else:
		empty_streak = 0
		time.sleep(1)

	frappe.enqueue(
		"mishkah.cleanup_orphan_students.delete_orphan_students_job",
		queue="long",
		timeout=2000,
		batch_size=batch_size,
		empty_streak=empty_streak,
		job_name=JOB_NAME,
		enqueue_after_commit=True,
	)

	return {
		"deleted": result["deleted"],
		"skipped": result["skipped"],
		"remaining": remaining,
		"done": False,
	}


@frappe.whitelist()
def enqueue_delete_orphan_students(batch_size=BATCH_SIZE):
	"""
	Start background cleanup. Safe to call from Desk / console.
	Preview first with: mishkah.cleanup_orphan_students.count_orphan_students()
	"""
	frappe.only_for("System Manager")
	batch_size = int(batch_size or BATCH_SIZE)
	total = count_orphan_students()

	if total == 0:
		return {"queued": False, "total": 0, "message": "No orphan students found"}

	frappe.enqueue(
		"mishkah.cleanup_orphan_students.delete_orphan_students_job",
		queue="long",
		timeout=2000,
		batch_size=batch_size,
		empty_streak=0,
		job_name=JOB_NAME,
	)

	return {
		"queued": True,
		"total": total,
		"batch_size": batch_size,
		"message": f"Queued cleanup for ~{total} orphan students (batch size {batch_size})",
	}
