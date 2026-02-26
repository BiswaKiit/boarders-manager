from flask import Flask, jsonify, render_template, request, redirect
import pandas as pd
import sqlite3
import os

app = Flask(__name__)

DATABASE = "boarders.db"
ADMIN_PASSWORD = "hostel@123"


# ---------------- DATABASE ---------------- #

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


# ---------------- HOME ---------------- #

@app.route("/")
def home():
    return render_template("index.html")


# ---------------- SEARCH + VACANCY API ---------------- #

@app.route("/students")
def get_students():
    search_by = request.args.get("search_by", "").lower()
    query = request.args.get("query", "").lower()

    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM students")
    rows = cursor.fetchall()
    conn.close()

    results = []
    vacant_rooms = []
    vacant_beds = []

    for row in rows:
        student = {
            "roll": str(row[0]).replace(".0", "") if row[0] else "",
            "name": row[1] or "",
            "student_contact": str(row[2]).replace(".0", "") if row[2] else "",
            "room": row[3] or "",
            "room_type": row[4] or "",
            "year": row[5] or "",
            "branch": row[6] or "",
            "parent_name": row[7] or "",
            "parent_contact": str(row[8]).replace(".0", "") if row[8] else "",
            "parent_email": row[9] or "",
            "state": row[10] or "",
            "mentor_name": row[11] or "",
            "mentor_contact": str(row[12]).replace(".0", "") if row[12] else "",
            "mentor_email": row[13] or "",
        }

        upper_name = student["name"].upper()

        if "VACANT ROOM" in upper_name:
            vacant_rooms.append(student["room"])
        elif "BED VACANT" in upper_name:
            vacant_beds.append(student["room"])

        match = True

        if query:
            match = False

            if search_by == "roll" and query in student["roll"].lower():
                match = True
            elif search_by == "room" and query in student["room"].lower():
                match = True
            elif search_by == "name" and query in student["name"].lower():
                match = True
            elif search_by == "mobile" and (
                query in student["student_contact"].lower() or
                query in student["parent_contact"].lower() or
                query in student["mentor_contact"].lower()
            ):
                match = True
            elif search_by == "state" and query in student["state"].lower():
                match = True
            elif search_by == "mentor" and query in student["mentor_name"].lower():
                match = True

        if match:
            results.append(student)

    return jsonify({
        "students": results,
        "vacant_rooms": vacant_rooms,
        "vacant_beds": vacant_beds
    })


# ---------------- ADMIN ---------------- #

@app.route("/admin", methods=["GET", "POST"])
def admin():
    if request.method == "POST":
        if request.form.get("password") == ADMIN_PASSWORD:
            return render_template("admin.html", authorized=True)
        else:
            return render_template("admin.html", authorized=False, error="Wrong Password")

    return render_template("admin.html", authorized=False)


# ---------------- UPLOAD ---------------- #

@app.route("/upload", methods=["POST"])
def upload_excel():
    file = request.files.get("file")

    if file:
        df = pd.read_excel(file)

        conn = sqlite3.connect(DATABASE)
        cursor = conn.cursor()
        cursor.execute("DELETE FROM students")

        for _, row in df.iterrows():
            cursor.execute("""
            INSERT INTO students VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?)
            """, (
                str(row.get("Roll No", "")).replace(".0",""),
                str(row.get("Student Name", "")),
                str(row.get("Student Mobile No", "")).replace(".0",""),
                str(row.get("Room No", "")),
                str(row.get("Room Type", "")),
                str(row.get("Year", "")),
                str(row.get("Branch", "")),
                str(row.get("Parent Name", "")),
                str(row.get("Parent Contact No", "")).replace(".0",""),
                str(row.get("Parent Email", "")),
                str(row.get("State", "")),
                str(row.get("Mentor Name", "")),
                str(row.get("Mobile No", "")).replace(".0",""),
                str(row.get("Mentor Email", "")),
            ))

        conn.commit()
        conn.close()

    return redirect("/")


# ---------------- RENDER ---------------- #

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)