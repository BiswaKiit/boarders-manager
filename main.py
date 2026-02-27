from flask import Flask, jsonify, render_template, request, redirect
import pandas as pd
import psycopg2
import os

app = Flask(__name__)

DATABASE_URL = os.environ.get("DATABASE_URL")
ADMIN_PASSWORD = "hostel@123"


def get_connection():
    return psycopg2.connect(DATABASE_URL)


def init_db():
    conn = get_connection()
    cur = conn.cursor()

    cur.execute("""
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
    cur.close()
    conn.close()


init_db()


@app.route("/")
def home():
    return render_template("index.html")


@app.route("/students")
def get_students():
    search_by = request.args.get("search_by", "").lower()
    query = request.args.get("query", "").lower()

    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT * FROM students")
    rows = cur.fetchall()
    cur.close()
    conn.close()

    results = []
    vacant_rooms = []
    vacant_beds = []
    total_students = 0
    year_count = {}

    for row in rows:
        roll = str(row[0] or "").replace(".0", "")

        student = {
            "roll": roll,
            "name": row[1] or "",
            "student_contact": str(row[2] or "").replace(".0", ""),
            "room": row[3] or "",
            "room_type": row[4] or "",
            "year": row[5] or "",
            "branch": row[6] or "",
            "parent_name": row[7] or "",
            "parent_contact": str(row[8] or "").replace(".0", ""),
            "parent_email": row[9] or "",
            "state": row[10] or "",
            "mentor_name": row[11] or "",
            "mentor_contact": str(row[12] or "").replace(".0", ""),
            "mentor_email": row[13] or "",
        }

        upper_name = student["name"].upper()

        if "VACANT ROOM" in upper_name:
            vacant_rooms.append(student["room"])
        elif "BED VACANT" in upper_name:
            vacant_beds.append(student["room"])
        elif roll:
            total_students += 1
            year = student["year"]
            year_count[year] = year_count.get(year, 0) + 1

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
                query in student["student_contact"].lower()
                or query in student["parent_contact"].lower()
                or query in student["mentor_contact"].lower()
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
        "vacant_beds": vacant_beds,
        "total_students": total_students,
        "year_count": year_count
    })


@app.route("/admin", methods=["GET", "POST"])
def admin():
    if request.method == "POST":
        if request.form.get("password") == ADMIN_PASSWORD:
            return render_template("admin.html", authorized=True)
        else:
            return render_template("admin.html", authorized=False, error="Wrong Password")
    return render_template("admin.html", authorized=False)


@app.route("/upload", methods=["POST"])
def upload_excel():
    file = request.files.get("file")

    if file:
        df = pd.read_excel(file)

        conn = get_connection()
        cur = conn.cursor()

        # Clear old data
        cur.execute("DELETE FROM students")

        data = []

        for _, row in df.iterrows():
            data.append((
                str(row.get("Roll No", "")).replace(".0", ""),
                str(row.get("Student Name", "")),
                str(row.get("Student Mobile No", "")).replace(".0", ""),
                str(row.get("Room No", "")),
                str(row.get("Room Type", "")),
                str(row.get("Year", "")),
                str(row.get("Branch", "")),
                str(row.get("Parent Name", "")),
                str(row.get("Parent Contact No", "")).replace(".0", ""),
                str(row.get("Parent Email", "")),
                str(row.get("State", "")),
                str(row.get("Mentor Name", "")),
                str(row.get("Mobile No", "")).replace(".0", ""),
                str(row.get("Mentor Email", "")),
            ))

        # Bulk insert (FAST)
        cur.executemany("""
        INSERT INTO students VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
        """, data)

        conn.commit()
        cur.close()
        conn.close()

    return redirect("/")


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)