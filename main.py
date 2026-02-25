from flask import Flask, jsonify, render_template, request, redirect
import pandas as pd
import sqlite3
import os

app = Flask(__name__)

DATABASE = "boarders.db"
ADMIN_PASSWORD = "hostel@123"


# ---------------- DATABASE SETUP ---------------- #

def init_db():
    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS students (
        roll TEXT,
        name TEXT,
        student_contact TEXT,
        room TEXT,
        room_type TEXT,
        year TEXT,
        branch TEXT,
        parent_name TEXT,
        parent_contact TEXT,
        parent_email TEXT,
        state TEXT,
        mentor_name TEXT,
        mentor_contact TEXT,
        mentor_email TEXT
    )
    """)

    conn.commit()
    conn.close()


init_db()


# ---------------- PUBLIC DASHBOARD ---------------- #

@app.route("/")
def home():
    return render_template("index.html")


@app.route("/students")
def get_students():
    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM students")
    rows = cursor.fetchall()
    conn.close()

    students = []
    occupied = 0
    vacant_rooms = []
    vacant_beds = []

    for row in rows:
        student = {
            "roll": row[0],
            "name": row[1],
            "student_contact": row[2],
            "room": row[3],
            "room_type": row[4],
            "year": row[5],
            "branch": row[6],
            "parent_name": row[7],
            "parent_contact": row[8],
            "parent_email": row[9],
            "state": row[10],
            "mentor_name": row[11],
            "mentor_contact": row[12],
            "mentor_email": row[13],
        }

        students.append(student)

        upper_name = student["name"].upper()

        if "VACANT ROOM" in upper_name:
            vacant_rooms.append({
                "room": student["room"],
                "room_type": student["room_type"]
            })

        elif "BED VACANT" in upper_name:
            vacant_beds.append({
                "room": student["room"],
                "room_type": student["room_type"]
            })

        elif student["roll"]:
            occupied += 1

    return jsonify({
        "students": students,
        "occupied": occupied,
        "vacant_rooms": vacant_rooms,
        "vacant_beds": vacant_beds
    })


# ---------------- ADMIN LOGIN ---------------- #

@app.route("/admin", methods=["GET", "POST"])
def admin():
    if request.method == "POST":
        password = request.form.get("password")

        if password == ADMIN_PASSWORD:
            return render_template("admin.html", authorized=True)
        else:
            return render_template("admin.html", authorized=False, error="Wrong Password")

    return render_template("admin.html", authorized=False)


# ---------------- EXCEL UPLOAD ---------------- #

@app.route("/upload", methods=["POST"])
def upload_excel():
    file = request.files.get("file")

    if file:
        df = pd.read_excel(file)

        conn = sqlite3.connect(DATABASE)
        cursor = conn.cursor()

        # Delete old data (Option A - Replace All)
        cursor.execute("DELETE FROM students")

        for _, row in df.iterrows():

            student_mobile = str(int(row["Student Mobile No"])) if pd.notna(row["Student Mobile No"]) else ""
            mentor_mobile = str(int(row["Mobile No"])) if pd.notna(row["Mobile No"]) else ""
            roll = str(int(row["Roll No"])) if pd.notna(row["Roll No"]) else ""

            cursor.execute("""
            INSERT INTO students VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?)
            """, (
                roll,
                str(row["Student Name"]),
                student_mobile,
                str(row["Room No"]),
                str(row["Room Type"]),
                str(row["Year"]),
                str(row["Branch"]),
                str(row["Parent Name"]),
                str(row["Parent Contact No"]),
                str(row["Parent Email"]),
                str(row["State"]),
                str(row["Mentor Name"]),
                mentor_mobile,
                str(row["Mentor Email"]),
            ))

        conn.commit()
        conn.close()

    return redirect("/")


# ---------------- RENDER PRODUCTION RUN ---------------- #

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)