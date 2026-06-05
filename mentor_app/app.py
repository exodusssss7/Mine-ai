from flask import Flask, render_template, request, redirect, url_for, session, flash, send_file
import os
import psycopg2
from psycopg2.extras import RealDictCursor
from werkzeug.security import generate_password_hash, check_password_hash
import io

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "fallback_secret_key_for_dev")

def get_db_connection():
    db_url = os.environ.get("DATABASE_URL")
    if db_url and "sslmode=require" not in db_url:
        if "?" in db_url:
            db_url += "&sslmode=require"
        else:
            db_url += "?sslmode=require"

    conn = psycopg2.connect(
        db_url or "postgresql://postgres:postgres@localhost/mentor_app",
        cursor_factory=RealDictCursor
    )
    return conn

def init_db():
    conn = get_db_connection()
    cur = conn.cursor()
    with open('schema.sql', 'r') as f:
        cur.execute(f.read())
    conn.commit()
    cur.close()
    conn.close()

@app.route("/")
def index():
    if 'user_id' in session:
        return redirect(url_for('dashboard'))
    return render_template("index.html")


@app.before_request
def setup_db():
    if not getattr(app, '_db_initialized', False):
        try:
            init_db()
            app._db_initialized = True
        except Exception as e:
            print(f"DB Init error (could be expected during dev): {e}")
            pass

@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")
        role = request.form.get("role")

        if not username or not password or role not in ['teacher', 'student']:
            flash("Please fill out all fields correctly.", "error")
            return redirect(url_for('register'))

        conn = get_db_connection()
        cur = conn.cursor()

        # Check if user exists
        cur.execute("SELECT id FROM users WHERE username = %s", (username,))
        if cur.fetchone():
            flash("Username already exists.", "error")
            conn.close()
            return redirect(url_for('register'))

        hashed_password = generate_password_hash(password)
        cur.execute(
            "INSERT INTO users (username, password_hash, role) VALUES (%s, %s, %s) RETURNING id",
            (username, hashed_password, role)
        )
        user_id = cur.fetchone()['id']
        conn.commit()
        cur.close()
        conn.close()

        session['user_id'] = user_id
        session['username'] = username
        session['role'] = role

        flash("Registration successful!", "success")
        return redirect(url_for('dashboard'))

    return render_template("register.html")

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")

        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute("SELECT * FROM users WHERE username = %s", (username,))
        user = cur.fetchone()
        conn.close()

        if user and check_password_hash(user['password_hash'], password):
            session['user_id'] = user['id']
            session['username'] = user['username']
            session['role'] = user['role']
            return redirect(url_for('dashboard'))
        else:
            flash("Invalid username or password.", "error")

    return render_template("login.html")

@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for('index'))

@app.route("/dashboard")
def dashboard():
    if 'user_id' not in session:
        return redirect(url_for('login'))

    conn = get_db_connection()
    cur = conn.cursor()

    if session['role'] == 'teacher':
        cur.execute("SELECT * FROM assignments WHERE teacher_id = %s ORDER BY created_at DESC", (session['user_id'],))
        assignments = cur.fetchall()

        # Get all submissions for these assignments
        cur.execute("""
            SELECT s.*, a.title, u.username as student_name
            FROM submissions s
            JOIN assignments a ON s.assignment_id = a.id
            JOIN users u ON s.student_id = u.id
            WHERE a.teacher_id = %s
            ORDER BY s.submitted_at DESC
        """, (session['user_id'],))
        submissions = cur.fetchall()
        conn.close()

        return render_template("teacher_dashboard.html", assignments=assignments, submissions=submissions)

    else: # student
        # Get all assignments
        cur.execute("""
            SELECT a.*, u.username as teacher_name
            FROM assignments a
            JOIN users u ON a.teacher_id = u.id
            ORDER BY a.created_at DESC
        """)
        assignments = cur.fetchall()

        # Get my submissions
        cur.execute("SELECT * FROM submissions WHERE student_id = %s", (session['user_id'],))
        my_submissions = {s['assignment_id']: s for s in cur.fetchall()}
        conn.close()

        return render_template("student_dashboard.html", assignments=assignments, my_submissions=my_submissions)

@app.route("/create_assignment", methods=["POST"])
def create_assignment():
    if 'user_id' not in session or session['role'] != 'teacher':
        return redirect(url_for('login'))

    title = request.form.get("title")
    description = request.form.get("description")

    if title:
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute(
            "INSERT INTO assignments (teacher_id, title, description) VALUES (%s, %s, %s)",
            (session['user_id'], title, description)
        )
        conn.commit()
        cur.close()
        conn.close()
        flash("Assignment created successfully!", "success")

    return redirect(url_for('dashboard'))

@app.route("/submit_work/<int:assignment_id>", methods=["POST"])
def submit_work(assignment_id):
    if 'user_id' not in session or session['role'] != 'student':
        return redirect(url_for('login'))

    if 'file' not in request.files:
        flash("No file uploaded.", "error")
        return redirect(url_for('dashboard'))

    file = request.files['file']
    if file.filename == '':
        flash("No file selected.", "error")
        return redirect(url_for('dashboard'))

    if file:
        file_data = file.read()
        conn = get_db_connection()
        cur = conn.cursor()

        try:
            cur.execute("""
                INSERT INTO submissions (assignment_id, student_id, file_data, file_name, mimetype)
                VALUES (%s, %s, %s, %s, %s)
                ON CONFLICT (assignment_id, student_id)
                DO UPDATE SET file_data = EXCLUDED.file_data, file_name = EXCLUDED.file_name, mimetype = EXCLUDED.mimetype, status = 'pending'
            """, (assignment_id, session['user_id'], psycopg2.Binary(file_data), file.filename, file.mimetype))
            conn.commit()
            flash("Work submitted successfully!", "success")
        except Exception as e:
            conn.rollback()
            flash(f"Error submitting work: {e}", "error")
        finally:
            cur.close()
            conn.close()

    return redirect(url_for('dashboard'))

@app.route("/download/<int:submission_id>")
def download(submission_id):
    if 'user_id' not in session:
        return redirect(url_for('login'))

    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("SELECT file_data, file_name, mimetype FROM submissions WHERE id = %s", (submission_id,))
    sub = cur.fetchone()
    cur.close()
    conn.close()

    if sub:
        return send_file(
            io.BytesIO(sub['file_data']),
            mimetype=sub['mimetype'],
            as_attachment=True,
            download_name=sub['file_name']
        )
    return "File not found", 404

@app.route("/review/<int:submission_id>", methods=["POST"])
def review(submission_id):
    if 'user_id' not in session or session['role'] != 'teacher':
        return redirect(url_for('login'))

    status = request.form.get("status")
    feedback = request.form.get("feedback")

    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute(
        "UPDATE submissions SET status = %s, feedback = %s WHERE id = %s",
        (status, feedback, submission_id)
    )
    conn.commit()
    cur.close()
    conn.close()

    flash("Review submitted.", "success")
    return redirect(url_for('dashboard'))

if __name__ == '__main__':
    app.run(debug=True, port=5000)
