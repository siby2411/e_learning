#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from flask import Flask, render_template, send_from_directory, jsonify, request
from flask_cors import CORS
import sqlite3
import os
import hashlib
import uuid
from datetime import datetime

app = Flask(__name__, static_folder='static', template_folder='templates')
app.secret_key = os.urandom(24)
CORS(app)

from routes.api import api_bp
from routes.academic_api import academic_bp
from routes.course_content_api import course_content_bp

app.register_blueprint(api_bp)
app.register_blueprint(academic_bp)
app.register_blueprint(course_content_bp)

def get_db():
    conn = sqlite3.connect(os.path.join(os.path.dirname(__file__), 'data', 'cours.db'))
    conn.row_factory = sqlite3.Row
    return conn

def create_admin():
    conn = get_db()
    if conn.execute("SELECT COUNT(*) FROM users").fetchone()[0] == 0:
        pwd = hashlib.sha256("admin123".encode()).hexdigest()
        conn.execute("INSERT INTO users (uuid, email, password_hash, first_name, last_name, status) VALUES (?,?,?,?,?,?)",
                     (str(uuid.uuid4()), "admin@elearning.sn", pwd, "Admin", "E-Learning", "active"))
        conn.commit()
        print("✅ Admin créé: admin@elearning.sn / admin123")
    conn.close()
create_admin()

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/academic')
def academic():
    return render_template('academic.html')

@app.route('/course')
def course_detail():
    return render_template('course_detail.html')

@app.route('/static/<path:path>')
def static_files(path):
    return send_from_directory('static', path)

@app.route('/api/stats/overview')
def stats_overview():
    conn = get_db()
    stats = conn.execute("""
        SELECT (SELECT COUNT(*) FROM users) as total_users,
               (SELECT COUNT(*) FROM courses WHERE status='published') as total_courses,
               (SELECT COUNT(*) FROM enrollments WHERE status='active') as active_enrollments,
               (SELECT COUNT(*) FROM enrollments WHERE status='completed') as completions,
               (SELECT COALESCE(SUM(amount),0) FROM payments WHERE status='completed') as total_revenue
    """).fetchone()
    conn.close()
    return jsonify(dict(stats))

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5001, debug=False)
