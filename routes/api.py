#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
API Routes - E-Learning
"""

from flask import Blueprint, request, jsonify
import sqlite3
import hashlib
import uuid
from datetime import datetime
import os

# Import absolu depuis la racine du projet
from services.enrollment_service import EnrollmentService
from models.database import db

api_bp = Blueprint('api', __name__, url_prefix='/api')

# ====== COURS ======
@api_bp.route('/courses')
def list_courses():
    category = request.args.get('category')
    is_free = request.args.get('is_free')
    difficulty = request.args.get('difficulty')
    
    conn = get_db()
    query = """
        SELECT c.*, cat.name as category_name, cat.icon
        FROM courses c
        JOIN course_categories cat ON c.category_id = cat.id
        WHERE c.status = 'published'
    """
    params = []
    
    if category:
        query += " AND cat.slug = ?"
        params.append(category)
    if is_free is not None:
        query += " AND c.is_free = ?"
        params.append(1 if is_free == 'true' else 0)
    if difficulty:
        query += " AND c.difficulty_level = ?"
        params.append(difficulty)
    
    query += " ORDER BY c.created_at DESC"
    
    courses = conn.execute(query, params).fetchall()
    conn.close()
    return jsonify([dict(row) for row in courses])

@api_bp.route('/courses/<int:course_id>')
def get_course(course_id):
    conn = get_db()
    course = conn.execute("""
        SELECT c.*, cat.name as category_name, cat.icon
        FROM courses c
        JOIN course_categories cat ON c.category_id = cat.id
        WHERE c.id = ?
    """, (course_id,)).fetchone()
    conn.close()
    if course:
        return jsonify({'course': dict(course)})
    return jsonify({'error': 'Cours non trouvé'}), 404

@api_bp.route('/courses/categories')
def get_categories():
    conn = get_db()
    cats = conn.execute("SELECT * FROM course_categories ORDER BY name").fetchall()
    conn.close()
    return jsonify([dict(row) for row in cats])

# ====== AUTH ======
@api_bp.route('/auth/login', methods=['POST'])
def login():
    data = request.get_json()
    email = data.get('email')
    password = data.get('password')
    
    if not email or not password:
        return jsonify({'success': False, 'error': 'Email et mot de passe requis'}), 400
    
    conn = get_db()
    password_hash = hashlib.sha256(password.encode()).hexdigest()
    user = conn.execute("""
        SELECT id, uuid, first_name, last_name, email, status
        FROM users
        WHERE email = ? AND password_hash = ?
    """, (email, password_hash)).fetchone()
    conn.close()
    
    if not user:
        return jsonify({'success': False, 'error': 'Identifiants invalides'}), 401
    
    token = str(uuid.uuid4())
    return jsonify({
        'success': True,
        'token': token,
        'user': dict(user)
    })

@api_bp.route('/auth/register', methods=['POST'])
def register_user():
    data = request.get_json()
    conn = get_db()
    
    existing = conn.execute("SELECT id FROM users WHERE email = ?", (data['email'],)).fetchone()
    if existing:
        conn.close()
        return jsonify({'success': False, 'error': 'Email déjà utilisé'}), 400
    
    password_hash = hashlib.sha256(data['password'].encode()).hexdigest()
    user_id = conn.execute("""
        INSERT INTO users (uuid, email, password_hash, first_name, last_name, phone, date_of_birth)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    """, (
        str(uuid.uuid4()), data['email'], password_hash,
        data['first_name'], data['last_name'],
        data.get('phone'), data.get('date_of_birth')
    )).lastrowid
    
    conn.commit()
    conn.close()
    
    return jsonify({'success': True, 'user_id': user_id, 'message': 'Utilisateur créé'})

@api_bp.route('/auth/logout', methods=['POST'])
def logout():
    return jsonify({'success': True})

# ====== INSCRIPTIONS ======
@api_bp.route('/enrollments/register', methods=['POST'])
def register_enrollment():
    data = request.get_json()
    
    required = ['email', 'first_name', 'last_name', 'course_id']
    missing = [f for f in required if f not in data]
    if missing:
        return jsonify({'success': False, 'error': f'Champs manquants: {", ".join(missing)}'}), 400
    
    conn = get_db()
    
    user = conn.execute("SELECT id FROM users WHERE email = ?", (data['email'],)).fetchone()
    if not user:
        password_hash = hashlib.sha256(data.get('password', 'default').encode()).hexdigest()
        user_id = conn.execute("""
            INSERT INTO users (uuid, email, password_hash, first_name, last_name)
            VALUES (?, ?, ?, ?, ?)
        """, (str(uuid.uuid4()), data['email'], password_hash, data['first_name'], data['last_name'])).lastrowid
    else:
        user_id = user['id']
    
    existing = conn.execute("SELECT id FROM enrollments WHERE user_id = ? AND course_id = ?", 
                           (user_id, data['course_id'])).fetchone()
    if existing:
        conn.close()
        return jsonify({'success': False, 'error': 'Déjà inscrit'})
    
    course = conn.execute("SELECT is_free, price, currency FROM courses WHERE id = ?", (data['course_id'],)).fetchone()
    if not course:
        conn.close()
        return jsonify({'success': False, 'error': 'Cours non trouvé'})
    
    enrollment_number = f"INS-{datetime.now().strftime('%Y')}-{str(uuid.uuid4().int)[:8]}"
    enrollment_id = conn.execute("""
        INSERT INTO enrollments (user_id, course_id, enrollment_number, status, payment_status, payment_amount, payment_currency, start_date)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        user_id, data['course_id'], enrollment_number,
        'active' if course['is_free'] else 'pending',
        'paid' if course['is_free'] else 'pending',
        course['price'], course['currency'], datetime.now().isoformat()
    )).lastrowid
    
    conn.commit()
    conn.close()
    
    return jsonify({
        'success': True,
        'enrollment_id': enrollment_id,
        'enrollment_number': enrollment_number,
        'is_free': bool(course['is_free']),
        'amount': course['price'],
        'currency': course['currency'],
        'payment_required': not bool(course['is_free'])
    })

@api_bp.route('/enrollments/<int:enrollment_id>/pay', methods=['POST'])
def pay_enrollment(enrollment_id):
    data = request.get_json()
    conn = get_db()
    
    enrollment = conn.execute("SELECT * FROM enrollments WHERE id = ?", (enrollment_id,)).fetchone()
    if not enrollment:
        conn.close()
        return jsonify({'success': False, 'error': 'Inscription non trouvée'})
    
    if enrollment['payment_status'] == 'paid':
        conn.close()
        return jsonify({'success': False, 'error': 'Déjà payé'})
    
    transaction_id = str(uuid.uuid4())
    payment_id = conn.execute("""
        INSERT INTO payments (enrollment_id, transaction_id, amount, currency, payment_method, payment_reference, status)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    """, (
        enrollment_id, transaction_id, data['payment']['amount'],
        data['payment']['currency'], data['payment']['method'],
        data['payment'].get('reference'), 'completed'
    )).lastrowid
    
    conn.execute("UPDATE enrollments SET status = 'active', payment_status = 'paid' WHERE id = ?", (enrollment_id,))
    conn.commit()
    conn.close()
    
    return jsonify({'success': True, 'payment_id': payment_id, 'enrollment_id': enrollment_id})

@api_bp.route('/enrollments/user/<int:user_id>')
def user_enrollments(user_id):
    conn = get_db()
    enrollments = conn.execute("""
        SELECT e.*, c.title as course_title
        FROM enrollments e
        JOIN courses c ON e.course_id = c.id
        WHERE e.user_id = ?
        ORDER BY e.created_at DESC
    """, (user_id,)).fetchall()
    conn.close()
    return jsonify([dict(row) for row in enrollments])

# ====== STATS ======
@api_bp.route('/stats/overview')
def stats_overview():
    conn = get_db()
    stats = conn.execute("""
        SELECT 
            (SELECT COUNT(*) FROM users) as total_users,
            (SELECT COUNT(*) FROM courses WHERE status = 'published') as total_courses,
            (SELECT COUNT(*) FROM enrollments WHERE status = 'active') as active_enrollments,
            (SELECT COUNT(*) FROM enrollments WHERE status = 'completed') as completions,
            (SELECT COALESCE(SUM(amount), 0) FROM payments WHERE status = 'completed') as total_revenue
    """).fetchone()
    conn.close()
    return jsonify(dict(stats))

# ====== FONCTION D'ACCÈS DB ======
def get_db():
    db_path = os.path.join(os.path.dirname(__file__), '..', 'data', 'cours.db')
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    return conn
