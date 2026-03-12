from flask import Flask, request, jsonify, render_template, redirect
import pandas as pd
import psycopg2
import os

app = Flask(__name__)

DATABASE_URL = os.environ.get("DATABASE_URL")


def get_conn():
    return psycopg2.connect(DATABASE_URL)


@app.route("/")
def home():
    return render_template("index.html")


@app.route("/students")
def students():

    search_by = request.args.get("search_by","")
    query = request.args.get("query","").lower()

    conn = get_conn()
    cur = conn.cursor()

    cur.execute("SELECT * FROM students")
    rows = cur.fetchall()

    cur.close()
    conn.close()

    students = []
    vacant_rooms = []
    vacant_beds = []
    year_count = {}

    total_students = 0

    for r in rows:

        roll = str(r[0] or "").replace(".0","")
        name = str(r[1] or "")
        student_mobile = str(r[2] or "").replace(".0","")
        room = str(r[3] or "")
        room_type = str(r[4] or "")
        year = str(r[5] or "")
        branch = str(r[6] or "")
        parent_name = str(r[7] or "")
        parent_contact = str(r[8] or "").replace(".0","")
        parent_email = str(r[9] or "")
        state = str(r[10] or "")
        mentor_name = str(r[11] or "")
        mentor_contact = str(r[12] or "").replace(".0","")
        mentor_email = str(r[13] or "")

        # ignore blank roll numbers
        if roll and roll.lower() != "nan":
            total_students += 1

            if year and year.lower() != "nan":
                year_count[year] = year_count.get(year,0) + 1

        # detect vacant
        if "VACANT ROOM" in name.upper():
            vacant_rooms.append(room)

        if "BED VACANT" in name.upper():
            vacant_beds.append(room)

        student = {
            "roll":roll,
            "name":name,
            "student_contact":student_mobile,
            "room":room,
            "room_type":room_type,
            "year":year,
            "branch":branch,
            "parent_name":parent_name,
            "parent_contact":parent_contact,
            "parent_email":parent_email,
            "state":state,
            "mentor_name":mentor_name,
            "mentor_contact":mentor_contact,
            "mentor_email":mentor_email
        }

        # search filter
        match = True

        if query:
            match = False

            if search_by == "roll" and query in roll.lower():
                match = True
            elif search_by == "room" and query in room.lower():
                match = True
            elif search_by == "name" and query in name.lower():
                match = True
            elif search_by == "state" and query in state.lower():
                match = True
            elif search_by == "mentor" and query in mentor_name.lower():
                match = True
            elif search_by == "mobile" and (
                query in student_mobile.lower()
                or query in parent_contact.lower()
                or query in mentor_contact.lower()
            ):
                match = True

        if match:
            students.append(student)

    return jsonify({
        "students":students,
        "vacant_rooms":vacant_rooms,
        "vacant_beds":vacant_beds,
        "total_students":total_students,
        "year_count":year_count
    })


@app.route("/admin")
def admin():
    return render_template("admin.html")


@app.route("/upload", methods=["POST"])
def upload():

    file = request.files["file"]

    df = pd.read_excel(file)

    conn = get_conn()
    cur = conn.cursor()

    cur.execute("DELETE FROM students")

    for _,row in df.iterrows():

        cur.execute("""
        INSERT INTO students VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
        """,(

        str(row.get("Roll No","")).replace(".0",""),
        row.get("Student Name",""),
        str(row.get("Student Mobile No","")).replace(".0",""),
        row.get("Room No",""),
        row.get("Room Type",""),
        row.get("Year",""),
        row.get("Branch",""),
        row.get("Parent Name",""),
        str(row.get("Parent Contact No","")).replace(".0",""),
        row.get("Parent Email",""),
        row.get("State",""),
        row.get("Mentor Name",""),
        str(row.get("Mobile No","")).replace(".0",""),
        row.get("Mentor Email","")

        ))

    conn.commit()
    cur.close()
    conn.close()

    return redirect("/")


if __name__ == "__main__":
    port = int(os.environ.get("PORT",10000))
    app.run(host="0.0.0.0", port=port)