#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
API de la plateforme de cours en ligne
"""

from flask import Blueprint, request, jsonify
from ..services.enrollment_service import EnrollmentService
from ..models.database import db
import hashlib
import uuid
from datetime import datetime, timedelta

api_bp = Blueprint('api', __name__, url_prefix='/api')

# ===== COURS =====
@api_bp.route('/courses', methods=['GET'])
def list_courses():
    """Liste tous les cours disponibles"""
    category = request.args.get('category')
    is_free = request.args.get('is_free')
    difficulty = request.args.get('difficulty')
    
    query = """
        SELECT c.*, cat.name as category_name 
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
    
    results = db.fetch_all(query, params)
    return jsonify([dict(row) for row in results])

@api_bp.route('/courses/<int:course_id>', methods=['GET'])
def get_course(course_id):
    """Détails d'un cours avec ses modules"""
    course = db.fetch_one("""
        SELECT c.*, cat.name as category_name 
        FROM courses c
        JOIN course_categories cat ON c.category_id = cat.id
        WHERE c.id = ?
    """, (course_id,))
    
    if not course:
        return jsonify({'error': 'Cours non trouvé'}), 404
    
    modules = db.fetch_all("""
        SELECT * FROM course_modules 
        WHERE course_id = ? 
        ORDER BY module_number
    """, (course_id,))
    
    return jsonify({
        'course': dict(course),
        'modules': [dict(m) for m in modules]
    })

@api_bp.route('/courses/categories', methods=['GET'])
def get_categories():
    """Liste des catégories de cours"""
    results = db.fetch_all("""
        SELECT * FROM course_categories 
        ORDER BY name
    """)
    return jsonify([dict(row) for row in results])

# ===== INSCRIPTIONS =====
@api_bp.route('/enrollments/register', methods=['POST'])
def register():
    """Inscription à un cours"""
    data = request.get_json()
    
    required = ['email', 'password', 'first_name', 'last_name', 'course_id']
    missing = [f for f in required if f not in data]
    if missing:
        return jsonify({
            'success': False,
            'error': f'Champs manquants: {", ".join(missing)}'
        }), 400
    
    result = EnrollmentService.register_for_course(data, data)
    return jsonify(result), 200 if result['success'] else 400

@api_bp.route('/enrollments/<int:enrollment_id>/pay', methods=['POST'])
def pay_enrollment(enrollment_id):
    """Paiement d'une inscription"""
    data = request.get_json()
    result = EnrollmentService.process_payment(enrollment_id, data.get('payment', {}))
    return jsonify(result), 200 if result['success'] else 400

@api_bp.route('/enrollments/<int:enrollment_id>/progress', methods=['POST'])
def update_progress(enrollment_id):
    """Mise à jour de la progression"""
    data = request.get_json()
    module_id = data.get('module_id')
    
    if not module_id:
        return jsonify({'success': False, 'error': 'Module ID requis'}), 400
    
    result = EnrollmentService.complete_module(enrollment_id, module_id)
    return jsonify(result), 200 if result['success'] else 400

@api_bp.route('/enrollments/user/<int:user_id>', methods=['GET'])
def get_user_enrollments(user_id):
    """Récupère les inscriptions d'un utilisateur"""
    enrollments = EnrollmentService.get_user_enrollments(user_id)
    return jsonify(enrollments)

@api_bp.route('/enrollments/<int:enrollment_id>', methods=['GET'])
def get_enrollment(enrollment_id):
    """Détails d'une inscription"""
    enrollment = EnrollmentService.get_enrollment(enrollment_id)
    if enrollment:
        return jsonify(enrollment)
    return jsonify({'error': 'Inscription non trouvée'}), 404

# ===== CERTIFICATS =====
@api_bp.route('/certificates/verify/<string:number>', methods=['GET'])
def verify_certificate(number):
    """Vérification d'un certificat"""
    cert = db.fetch_one("""
        SELECT 
            c.*,
            u.first_name, u.last_name,
            cr.title as course_title,
            e.completion_date
        FROM certificates c
        JOIN enrollments e ON c.enrollment_id = e.id
        JOIN users u ON e.user_id = u.id
        JOIN courses cr ON e.course_id = cr.id
        WHERE c.certificate_number = ?
    """, (number,))
    
    if cert:
        # Incrémenter le compteur de vérification
        db.execute("""
            UPDATE certificates 
            SET verification_count = verification_count + 1,
                last_verified_at = ?
            WHERE id = ?
        """, (datetime.now().isoformat(), cert['id']))
        
        return jsonify({
            'valid': True,
            'certificate': dict(cert)
        })
    
    return jsonify({'valid': False, 'error': 'Certificat non trouvé'}), 404

# ===== STATISTIQUES =====
@api_bp.route('/stats/overview', methods=['GET'])
def get_overview_stats():
    """Statistiques globales"""
    stats = db.fetch_one("""
        SELECT 
            (SELECT COUNT(*) FROM users) as total_users,
            (SELECT COUNT(*) FROM courses WHERE status = 'published') as total_courses,
            (SELECT COUNT(*) FROM enrollments WHERE status = 'active') as active_enrollments,
            (SELECT COUNT(*) FROM enrollments WHERE status = 'completed') as completions,
            (SELECT COALESCE(SUM(amount), 0) FROM payments WHERE status = 'completed') as total_revenue
    """)
    
    return jsonify(dict(stats))

@api_bp.route('/stats/course/<int:course_id>', methods=['GET'])
def get_course_stats(course_id):
    """Statistiques d'un cours"""
    return jsonify(EnrollmentService.get_course_statistics(course_id))

# ===== AUTHENTIFICATION =====
@api_bp.route('/auth/login', methods=['POST'])
def login():
    data = request.get_json()
    email = data.get('email')
    password = data.get('password')
    
    if not email or not password:
        return jsonify({'success': False, 'error': 'Email et mot de passe requis'}), 400
    
    password_hash = hashlib.sha256(password.encode()).hexdigest()
    user = db.fetch_one("""
        SELECT id, uuid, first_name, last_name, email, status
        FROM users
        WHERE email = ? AND password_hash = ?
    """, (email, password_hash))
    
    if not user:
        return jsonify({'success': False, 'error': 'Identifiants invalides'}), 401
    
    token = str(uuid.uuid4())
    expires_at = datetime.now() + timedelta(days=7)
    
    db.execute("""
        INSERT INTO sessions (user_id, session_token, expires_at)
        VALUES (?, ?, ?)
    """, (user['id'], token, expires_at.isoformat()))
    
    return jsonify({
        'success': True,
        'user': dict(user),
        'token': token
    })

@api_bp.route('/auth/register', methods=['POST'])
def register_user():
    """Inscription d'un nouvel utilisateur"""
    data = request.get_json()
    
    # Vérifier si l'email existe déjà
    existing = db.fetch_one("SELECT id FROM users WHERE email = ?", (data['email'],))
    if existing:
        return jsonify({'success': False, 'error': 'Email déjà utilisé'}), 400
    
    password_hash = hashlib.sha256(data['password'].encode()).hexdigest()
    
    user_id = db.execute("""
        INSERT INTO users (
            uuid, email, password_hash, first_name, last_name, phone, date_of_birth
        ) VALUES (?, ?, ?, ?, ?, ?, ?)
    """, (
        str(uuid.uuid4()), data['email'], password_hash,
        data['first_name'], data['last_name'],
        data.get('phone'), data.get('date_of_birth')
    ))
    
    return jsonify({
        'success': True,
        'user_id': user_id,
        'message': 'Utilisateur créé avec succès'
    })

@api_bp.route('/auth/logout', methods=['POST'])
def logout():
    token = request.headers.get('Authorization', '').replace('Bearer ', '')
    if token:
        db.execute("DELETE FROM sessions WHERE session_token = ?", (token,))
    return jsonify({'success': True})
