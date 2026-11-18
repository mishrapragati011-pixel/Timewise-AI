
from flask import Flask, send_from_directory, jsonify, request
import os
import json
import sys

app = Flask(__name__)

PROJECT_FOLDER = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "..")
)


FRONTEND_FOLDER = os.path.join(PROJECT_FOLDER, "frontend")

# Import AKTU subject database
sys.path.insert(0, PROJECT_FOLDER)

from algorithms.subjects_data import BRANCHES, SUBJECTS
from algorithms.timetable_generator import TimetableGenerator

@app.route("/")
def home():
    return send_from_directory(FRONTEND_FOLDER, "index.html")


@app.route("/faculty")
def faculty():
    return send_from_directory(FRONTEND_FOLDER, "faculty.html")


@app.route("/student")
def student():
    return send_from_directory(FRONTEND_FOLDER, "student.html")


# API: Get branch-wise and semester-wise subjects
@app.route("/api/subjects")
def get_subjects():

    branch = request.args.get("branch", "")
    semester = request.args.get("semester", "")

    if branch not in BRANCHES:
        return jsonify({
            "error": "Please select a valid branch."
        }), 400

    try:
        semester_number = int(semester)
    except (ValueError, TypeError):
        return jsonify({
            "error": "Please select a valid semester."
        }), 400

    stream = BRANCHES[branch]

    semester_key = f"semester_{semester_number}"

    subject_data = SUBJECTS.get(stream, {}).get(
        semester_key, []
    )

    subject_list = []

    for item in subject_data:

        if isinstance(item, dict):

            for code, name in item["subjects"]:
                subject_list.append({
                    "code": code,
                    "name": name
                })

        else:
            code, name = item

            subject_list.append({
                "code": code,
                "name": name
            })

    return jsonify({
        "branch": branch,
        "semester": semester_number,
        "subjects": subject_list
    })


# API: Save faculty information
@app.route("/api/save-faculty", methods=["POST"])
def save_faculty():

    data = request.get_json() or {}

    faculty_name = data.get("faculty_name", "").strip()
    faculty_id = data.get("faculty_id", "").strip()
    branch = data.get("branch", "")
    semester = data.get("semester", "")
    subject = data.get("subject", "")
    weekly_lectures = data.get("weekly_lectures")

    if not all([faculty_name, faculty_id, branch, semester, subject, weekly_lectures]):
        return jsonify({"error": "Please fill all faculty information."}), 400

    if branch not in BRANCHES:
        return jsonify({"error": "Invalid branch selected."}), 400

    try:
        semester = int(semester)
        weekly_lectures = int(weekly_lectures)
    except (ValueError, TypeError):
        return jsonify({"error": "Invalid semester or weekly lectures."}), 400

    if not 1 <= weekly_lectures <= 40:
        return jsonify({"error": "Weekly lectures must be between 1 and 40."}), 400

    stream = BRANCHES[branch]
    subject_key = f"semester_{semester}"
    subject_data = SUBJECTS.get(stream, {}).get(subject_key, [])

    valid_subject_codes = []

    for item in subject_data:
        if isinstance(item, dict):
            valid_subject_codes.extend(code for code, name in item["subjects"])
        else:
            valid_subject_codes.append(item[0])

    if subject not in valid_subject_codes:
        return jsonify({"error": "Invalid subject selected."}), 400

    faculty_record = {
        "faculty_name": faculty_name,
        "faculty_id": faculty_id,
        "branch": branch,
        "semester": semester,
        "subject": subject,
        "weekly_lectures": weekly_lectures
    }

    data_file = os.path.join(os.path.dirname(__file__), "faculty_data.json")

    try:
        if os.path.exists(data_file):
            with open(data_file, "r", encoding="utf-8") as file:
                faculty_list = json.load(file)
        else:
            faculty_list = []

        faculty_list = [
            item for item in faculty_list
            if item.get("faculty_id") != faculty_id
        ]

        faculty_list.append(faculty_record)

        with open(data_file, "w", encoding="utf-8") as file:
            json.dump(faculty_list, file, indent=4)

        return jsonify({
            "message": "Faculty information saved successfully!"
        })

    except (OSError, json.JSONDecodeError):
        return jsonify({"error": "Unable to save faculty information."}), 500


# API: Generate weekly timetable
@app.route("/api/generate-timetable", methods=["GET"])
def generate_timetable():

    branch = request.args.get("branch", "")
    semester = request.args.get("semester", "")

    if branch not in BRANCHES:
        return jsonify({"error": "Please select a valid branch."}), 400

    try:
        semester = int(semester)
    except (ValueError, TypeError):
        return jsonify({"error": "Please select a valid semester."}), 400

    data_file = os.path.join(
        os.path.dirname(__file__),
        "faculty_data.json"
    )

    if not os.path.exists(data_file):
        return jsonify({"error": "No faculty records found."}), 404

    try:
        with open(data_file, "r", encoding="utf-8") as file:
            faculty_list = json.load(file)

        selected_faculty = [
            record for record in faculty_list
            if record["branch"] == branch
            and int(record["semester"]) == semester
        ]

        if not selected_faculty:
            return jsonify({
                "error": "No faculty records found for this branch and semester."
            }), 404

        generator = TimetableGenerator(selected_faculty)

        timetable = generator.generate_timetable()

        class_name = f"{branch} - Semester {semester}"

        return jsonify({
            "message": "Timetable generated successfully!",
            "timetable": timetable[class_name]
        })

    except (ValueError, KeyError, OSError, json.JSONDecodeError) as error:
        return jsonify({
            "error": str(error)
        }), 500


@app.route("/api/save-student-data", methods=["POST"])
def save_student_data():
    try:
        data = request.get_json(silent=True) or {}

        student_name = data.get("studentName", "").strip()

        if not student_name:
            return jsonify({
                "success": False,
                "message": "Student name is required"
            }), 400

        file_path = os.path.join(
            app.root_path,
            "student_data.json"
        )

        if os.path.exists(file_path):
            with open(file_path, "r", encoding="utf-8") as file:
                database = json.load(file)
        else:
            database = {"students": []}

        students = database.get("students", [])

        student_found = False

        for index, student in enumerate(students):
            if student.get("studentName", "").lower() == student_name.lower():
                students[index] = data
                student_found = True
                break

        if not student_found:
            students.append(data)

        database["students"] = students

        with open(file_path, "w", encoding="utf-8") as file:
            json.dump(database, file, indent=4, ensure_ascii=False)

        return jsonify({
            "success": True,
            "message": "Student data saved successfully!"
        })

    except Exception as error:
        return jsonify({
            "success": False,
            "message": str(error)
        }), 500

@app.route("/api/get-student-data", methods=["GET"])
def get_student_data():
    try:
        student_name = request.args.get("studentName", "").strip()

        if not student_name:
            return jsonify({
                "success": False,
                "message": "Student name is required"
            }), 400

        file_path = os.path.join(
            app.root_path,
            "student_data.json"
        )

        if not os.path.exists(file_path):
            return jsonify({
                "success": False,
                "message": "No saved data found"
            }), 404

        with open(file_path, "r", encoding="utf-8") as file:
            database = json.load(file)

        for student in database.get("students", []):
            if student.get("studentName", "").lower() == student_name.lower():
                return jsonify({
                    "success": True,
                    "data": student
                })

        return jsonify({
            "success": False,
            "message": "Student record not found"
        }), 404

    except Exception as error:
        return jsonify({
            "success": False,
            "message": str(error)
        }), 500

if __name__ == "__main__":

    app.run(debug=True)
