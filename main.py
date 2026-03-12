from flask import Flask, jsonify, render_template, request, redirect, send_from_directory
import pandas as pd
import psycopg2
import os

app = Flask(__name__)

DATABASE_URL = os.environ.get("DATABASE_URL")
ADMIN_PASSWORD = "hostel@123"


@app.route('/icon.png')
def icon():
    return send_from_directory('.', 'icon.png')

@app.route('/manifest.json')
def manifest():
    return send_from_directory('.', 'manifest.json')


def get_connection():
    return psycopg2.connect(DATABASE_URL)


def init_db():

    conn=get_connection()
    cur=conn.cursor()

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

    search_by=request.args.get("search_by","").lower()
    query=request.args.get("query","").lower()

    conn=get_connection()
    cur=conn.cursor()

    cur.execute("SELECT * FROM students")
    rows=cur.fetchall()

    cur.close()
    conn.close()

    students=[]
    total_students=0
    year_count={}

    room_data={}
    vacant_rooms=[]
    vacant_beds=[]

    for r in rows:

        roll=str(r[0] or "").replace(".0","")
        room=r[3] or ""
        room_type=r[4] or ""
        name=r[1] or ""

        student={
            "roll":roll,
            "name":name,
            "student_contact":str(r[2] or "").replace(".0",""),
            "room":room,
            "room_type":room_type,
            "year":r[5] or "",
            "branch":r[6] or "",
            "parent_name":r[7] or "",
            "parent_contact":str(r[8] or "").replace(".0",""),
            "parent_email":r[9] or "",
            "state":r[10] or "",
            "mentor_name":r[11] or "",
            "mentor_contact":str(r[12] or "").replace(".0",""),
            "mentor_email":r[13] or ""
        }

        students.append(student)

        if roll and roll.lower()!="nan":

            total_students+=1

            y=student["year"]

            if y and y.lower()!="nan":
                year_count[y]=year_count.get(y,0)+1

        if room:

            if room not in room_data:
                room_data[room]={"type":room_type,"count":0}

            if "VACANT" not in name.upper():
                room_data[room]["count"]+=1

        if "BED VACANT" in name.upper():
            vacant_beds.append(room)

        if "VACANT ROOM" in name.upper():
            vacant_rooms.append(room)

    results=[]

    for s in students:

        match=True

        if query:
            match=False

            if search_by=="roll" and query in s["roll"].lower():
                match=True
            elif search_by=="room" and query in s["room"].lower():
                match=True
            elif search_by=="name" and query in s["name"].lower():
                match=True
            elif search_by=="state" and query in s["state"].lower():
                match=True
            elif search_by=="mentor" and query in s["mentor_name"].lower():
                match=True
            elif search_by=="mobile" and (
                query in s["student_contact"].lower()
                or query in s["parent_contact"].lower()
                or query in s["mentor_contact"].lower()
            ):
                match=True

        if match:
            results.append(s)

    return jsonify({
        "students":results,
        "vacant_rooms":vacant_rooms,
        "vacant_beds":vacant_beds,
        "total_students":total_students,
        "year_count":year_count
    })


@app.route("/admin",methods=["GET","POST"])
def admin():

    if request.method=="POST":

        if request.form.get("password")==ADMIN_PASSWORD:
            return render_template("admin.html",authorized=True)

        else:
            return render_template("admin.html",authorized=False,error="Wrong Password")

    return render_template("admin.html",authorized=False)


@app.route("/upload",methods=["POST"])
def upload_excel():

    file=request.files.get("file")

    if file:

        df=pd.read_excel(file)

        conn=get_connection()
        cur=conn.cursor()

        cur.execute("DELETE FROM students")

        data=[]

        for _,row in df.iterrows():

            roll="" if pd.isna(row.get("Roll No")) else str(row.get("Roll No"))

            data.append((

                roll.replace(".0",""),
                str(row.get("Student Name","")),
                str(row.get("Student Mobile No","")).replace(".0",""),
                str(row.get("Room No","")),
                str(row.get("Room Type","")),
                str(row.get("Year","")),
                str(row.get("Branch","")),
                str(row.get("Parent Name","")),
                str(row.get("Parent Contact No","")).replace(".0",""),
                str(row.get("Parent Email","")),
                str(row.get("State","")),
                str(row.get("Mentor Name","")),
                str(row.get("Mobile No","")).replace(".0",""),
                str(row.get("Mentor Email",""))

            ))

        cur.executemany("""
        INSERT INTO students VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
        """,data)

        conn.commit()
        cur.close()
        conn.close()

    return redirect("/")


if __name__=="__main__":

    port=int(os.environ.get("PORT",10000))
    app.run(host="0.0.0.0",port=port)