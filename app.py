#!/usr/bin/env python3
from flask import Flask, render_template, jsonify
from flask_cors import CORS
from routes.api import api_bp
from routes.academic_api import academic_bp
from routes.course_content_api import course_content_bp
from routes.admin_api import admin_bp
from routes.advanced_api import advanced_bp

app = Flask(__name__, static_folder='static', template_folder='templates')
app.secret_key = 'secret'
CORS(app)

app.register_blueprint(api_bp)
app.register_blueprint(academic_bp)
app.register_blueprint(course_content_bp)
app.register_blueprint(admin_bp)
app.register_blueprint(advanced_bp)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/admin')
def admin():
    return render_template('admin.html')

@app.route('/dashboard')
def dashboard():
    return render_template('dashboard.html')

@app.route('/course')
def course():
    return render_template('course_detail.html')

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5001, debug=True)
