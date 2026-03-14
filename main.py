from flask import Flask, render_template, request, jsonify
import pandas as pd
import os

app = Flask(__name__)

EXCEL_FILE = "Student Master Export Final.xlsx"
ADMIN_PASSWORD = "hostel@123"


def clean_number(value):
    if pd.isna(value):
        return ""
    text = str(value)
    if text.endswith(".0"):
        text = text[:-2]
    return text


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

    if df.empty:
        return jsonify({
            "students": [],
            "vacant_beds": [],
            "vacant_rooms": [],
            "vacant_rooms_3s": [],
            "vacant_rooms_2s": [],
            "total_students": 0,
            "year_count": {}
        })

    students = []
    vacant_beds = []
    room_data = {}

    for _, row in df.iterrows():

        roll = clean_number(row.get("Roll No", ""))
        name = str(row.get("Student Name", "")).strip()
        room = str(row.get("Room No", "")).strip()
        room_type = str(row.get("Room Type", "")).strip()

        student = {
            "roll": roll,
            "name": name,
            "room": room,
            "room_type": room_type,
            "student_contact": clean_number(row.get("Student Mobile No", "")),
            "year": str(row.get("Year", "")),
            "branch": str(row.get("Branch", "")),
            "parent_name": str(row.get("Parent Name", "")),
            "parent_contact": clean_number(row.get("Parent Contact No", "")),
            "parent_email": str(row.get("Parent Email", "")),
            "state": str(row.get("State", "")),
            "mentor_name": str(row.get("Mentor Name", "")),
            "mentor_contact": clean_number(row.get("Mobile No", "")),
            "mentor_email": str(row.get("Mentor Email", ""))
        }

        students.append(student)

        # Vacant bed detection
        if name.lower() == "bed vacant":
            vacant_beds.append(room)

        # Room data collection
        if room not in room_data:
            room_data[room] = {
                "room_type": room_type,
                "beds": []
            }

        room_data[room]["beds"].append(name.lower())

    vacant_rooms = []
    vacant_rooms_3s = []
    vacant_rooms_2s = []

    for room, info in room_data.items():

        beds = info["beds"]
        room_type = info["room_type"]

        # room vacant if all beds = "bed vacant"
        if all(b == "bed vacant" for b in beds):

            vacant_rooms.append(room)

            if room_type == "3S":
                vacant_rooms_3s.append(room)

            if room_type == "2S":
                vacant_rooms_2s.append(room)

    # Total students = Roll No present
    total_students = df["Roll No"].replace("", pd.NA).dropna().count()

    year_count = {}

    for _, row in df.iterrows():

        roll = row.get("Roll No", "")
        year = str(row.get("Year", "")).strip()

        if roll == "" or year == "":
            continue

        year_count[year] = year_count.get(year, 0) + 1

    return jsonify({
        "students": students,
        "vacant_beds": vacant_beds,
        "vacant_rooms": vacant_rooms,
        "vacant_rooms_3s": vacant_rooms_3s,
        "vacant_rooms_2s": vacant_rooms_2s,
        "total_students": int(total_students),
        "year_count": year_count
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