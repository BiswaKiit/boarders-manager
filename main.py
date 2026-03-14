from flask import Flask, render_template, request, jsonify
import pandas as pd
import os

app = Flask(__name__)

EXCEL_FILE = "Student Master Export Final.xlsx"
ADMIN_PASSWORD = "hostel@123"


def load_data():

    if not os.path.exists(EXCEL_FILE):
        return pd.DataFrame()

    df = pd.read_excel(EXCEL_FILE)

    df.columns = df.columns.str.strip()

    df = df.fillna("")

    return df


@app.route("/")
def home():
    return render_template("index.html")


@app.route("/students")
def students():

    df = load_data()

    students = []

    vacant_beds = 0

    for _, row in df.iterrows():

        roll = str(row.get("Roll No", "")).replace(".0", "").strip()
        name = str(row.get("Student Name", "")).strip()

        if name.lower() == "bed vacant":
            vacant_beds += 1

        student = {
            "roll": roll,
            "name": name,
            "room": str(row.get("Room No", "")),
            "room_type": str(row.get("Room Type", "")),
            "student_contact": str(row.get("Student Mobile No", "")).replace(".0",""),
            "year": str(row.get("Year", "")),
            "branch": str(row.get("Branch", "")),
            "parent_name": str(row.get("Parent Name", "")),
            "parent_contact": str(row.get("Parent Contact No", "")).replace(".0",""),
            "parent_email": str(row.get("Parent Email", "")),
            "state": str(row.get("State", "")),
            "mentor_name": str(row.get("Mentor Name", "")),
            "mentor_contact": str(row.get("Mobile No", "")).replace(".0",""),
            "mentor_email": str(row.get("Mentor Email", ""))
        }

        students.append(student)

    total_students = df["Roll No"].replace("", pd.NA).dropna().count()

    room_groups = df.groupby("Room No")

    vacant_rooms = 0

    for room, group in room_groups:

        students_in_room = group["Student Name"].astype(str).str.lower()

        if (students_in_room == "bed vacant").all():
            vacant_rooms += 1

    return jsonify({
        "students": students,
        "total_students": int(total_students),
        "vacant_beds": vacant_beds,
        "vacant_rooms": vacant_rooms
    })


@app.route("/admin")
def admin():
    return render_template("admin.html")


@app.route("/upload", methods=["POST"])
def upload():

    password = request.form.get("password")

    if password != ADMIN_PASSWORD:
        return "Wrong Password"

    file = request.files.get("file")

    if not file:
        return "No file selected"

    file.save(EXCEL_FILE)

    return "Excel Updated Successfully"


if __name__ == "__main__":
    app.run(debug=True)