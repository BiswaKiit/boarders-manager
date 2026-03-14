from flask import Flask, render_template, request, jsonify
import pandas as pd
import os

app = Flask(__name__)

EXCEL_FILE = "Student Master Export Final.xlsx"
ADMIN_PASSWORD = "hostel@123"


def clean_number(series):
    return series.astype(str).str.replace(".0", "", regex=False)


def load_data():

    if not os.path.exists(EXCEL_FILE):
        return pd.DataFrame()

    df = pd.read_excel(EXCEL_FILE, dtype=str)

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
            "total_students": 0,
            "year_count": {}
        })

    # Clean numeric columns
    df["Roll No"] = clean_number(df["Roll No"])
    df["Student Mobile No"] = clean_number(df["Student Mobile No"])
    df["Parent Contact No"] = clean_number(df["Parent Contact No"])
    df["Mobile No"] = clean_number(df["Mobile No"])

    # Vacant bed logic
    vacant_beds_df = df[df["Student Name"].str.lower() == "bed vacant"]
    vacant_beds = vacant_beds_df["Room No"].tolist()

    # Vacant room logic
    vacant_rooms_df = df[df["Student Name"].str.lower() == "vacant room"]
    vacant_rooms = vacant_rooms_df["Room No"].tolist()

    # Total students
    total_students = df[df["Roll No"] != ""].shape[0]

    # Year stats
    year_df = df[df["Roll No"] != ""]
    year_count = year_df["Year"].value_counts().to_dict()

    # Students list (fast conversion)
    students = []

    for _, row in df.iterrows():

        students.append({

            "roll": row.get("Roll No", ""),
            "name": row.get("Student Name", ""),
            "room": row.get("Room No", ""),
            "room_type": row.get("Room Type", ""),
            "student_contact": row.get("Student Mobile No", ""),
            "year": row.get("Year", ""),
            "branch": row.get("Branch", ""),
            "parent_name": row.get("Parent Name", ""),
            "parent_contact": row.get("Parent Contact No", ""),
            "parent_email": row.get("Parent Email", ""),
            "state": row.get("State", ""),
            "mentor_name": row.get("Mentor Name", ""),
            "mentor_contact": row.get("Mobile No", ""),
            "mentor_email": row.get("Mentor Email", "")

        })

    return jsonify({
        "students": students,
        "vacant_beds": vacant_beds,
        "vacant_rooms": vacant_rooms,
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