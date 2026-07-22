#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Application E-Learning Sénégal
"""

from flask import Flask, render_template, send_from_directory, jsonify, request
from flask_cors import CORS
import sqlite3
import os
import hashlib
import uuid
from datetime import datetime, timedelta

app = Flask(__name__, static_folder='static', template_folder='templates')
app.secret_key = os.urandom(24)
CORS(app)

# ====== BASE DE DONNÉES ======
def get_db():
    """Connexion à la base de données"""
    db_path = os.path.join(os.path.dirname(__file__), 'data', 'cours.db')
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    return conn

# ====== ROUTES FRONTEND ======
@app.route('/')
def index():
    return render_template('index.html')

@app.route('/static/<path:path>')
def serve_static(path):
    return send_from_directory('static', path)

# ====== API - COURS ======
@app.route('/api/courses')
def api_courses():
    """Liste des cours disponibles"""
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

@app.route('/api/courses/<int:course_id>')
def api_course(course_id):
    """Détail d'un cours"""
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

@app.route('/api/courses/categories')
def api_categories():
    """Liste des catégories"""
    conn = get_db()
    cats = conn.execute("""
        SELECT * FROM course_categories ORDER BY name
    """).fetchall()
    conn.close()
    return jsonify([dict(row) for row in cats])

# ====== API - INSCRIPTIONS ======
@app.route('/api/enrollments/register', methods=['POST'])
def api_register():
    """Inscription à un cours"""
    data = request.get_json()
    
    # Vérification des champs requis
    required = ['email', 'first_name', 'last_name', 'course_id']
    missing = [f for f in required if f not in data]
    if missing:
        return jsonify({
            'success': False,
            'error': f'Champs manquants: {", ".join(missing)}'
        }), 400
    
    conn = get_db()
    
    # Vérifier si l'utilisateur existe déjà
    user = conn.execute(
        "SELECT id FROM users WHERE email = ?", 
        (data['email'],)
    ).fetchone()
    
    if not user:
        # Créer l'utilisateur
        password_hash = hashlib.sha256(data.get('password', 'default').encode()).hexdigest()
        user_id = conn.execute("""
            INSERT INTO users (uuid, email, password_hash, first_name, last_name)
            VALUES (?, ?, ?, ?, ?)
        """, (
            str(uuid.uuid4()), data['email'], password_hash,
            data['first_name'], data['last_name']
        )).lastrowid
    else:
        user_id = user['id']
    
    # Vérifier si déjà inscrit
    existing = conn.execute("""
        SELECT id, status FROM enrollments 
        WHERE user_id = ? AND course_id = ?
    """, (user_id, data['course_id'])).fetchone()
    
    if existing and existing['status'] in ['active', 'pending']:
        conn.close()
        return jsonify({
            'success': False,
            'error': 'Vous êtes déjà inscrit à ce cours'
        })
    
    # Récupérer les infos du cours
    course = conn.execute(
        "SELECT id, is_free, price, currency FROM courses WHERE id = ?",
        (data['course_id'],)
    ).fetchone()
    
    if not course:
        conn.close()
        return jsonify({'success': False, 'error': 'Cours non trouvé'})
    
    # Générer le numéro d'inscription
    enrollment_number = f"INS-{datetime.now().strftime('%Y')}-{str(uuid.uuid4().int)[:8]}"
    
    # Créer l'inscription
    enrollment_id = conn.execute("""
        INSERT INTO enrollments (
            user_id, course_id, enrollment_number, status, payment_status,
            payment_amount, payment_currency, start_date
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
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

@app.route('/api/enrollments/<int:enrollment_id>/pay', methods=['POST'])
def api_pay(enrollment_id):
    """Traitement du paiement"""
    data = request.get_json()
    conn = get_db()
    
    # Vérifier l'inscription
    enrollment = conn.execute(
        "SELECT * FROM enrollments WHERE id = ?",
        (enrollment_id,)
    ).fetchone()
    
    if not enrollment:
        conn.close()
        return jsonify({'success': False, 'error': 'Inscription non trouvée'})
    
    if enrollment['payment_status'] == 'paid':
        conn.close()
        return jsonify({'success': False, 'error': 'Déjà payé'})
    
    # Enregistrer le paiement
    transaction_id = str(uuid.uuid4())
    payment_id = conn.execute("""
        INSERT INTO payments (
            enrollment_id, transaction_id, amount, currency,
            payment_method, payment_reference, status
        ) VALUES (?, ?, ?, ?, ?, ?, ?)
    """, (
        enrollment_id, transaction_id, data['payment']['amount'],
        data['payment']['currency'], data['payment']['method'],
        data['payment'].get('reference'), 'completed'
    )).lastrowid
    
    # Activer l'inscription
    conn.execute("""
        UPDATE enrollments 
        SET status = 'active', payment_status = 'paid', updated_at = ?
        WHERE id = ?
    """, (datetime.now().isoformat(), enrollment_id))
    
    conn.commit()
    conn.close()
    
    return jsonify({
        'success': True,
        'payment_id': payment_id,
        'enrollment_id': enrollment_id,
        'enrollment_number': enrollment['enrollment_number']
    })

@app.route('/api/enrollments/user/<int:user_id>')
def api_user_enrollments(user_id):
    """Récupère les inscriptions d'un utilisateur"""
    conn = get_db()
    enrollments = conn.execute("""
        SELECT 
            e.*,
            c.title as course_title,
            c.thumbnail_url,
            cat.name as category_name
        FROM enrollments e
        JOIN courses c ON e.course_id = c.id
        JOIN course_categories cat ON c.category_id = cat.id
        WHERE e.user_id = ?
        ORDER BY e.created_at DESC
    """, (user_id,)).fetchall()
    conn.close()
    return jsonify([dict(row) for row in enrollments])

# ====== API - CERTIFICATS ======
@app.route('/api/certificates/verify/<string:number>')
def api_verify_certificate(number):
    """Vérification d'un certificat"""
    conn = get_db()
    cert = conn.execute("""
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
    """, (number,)).fetchone()
    conn.close()
    
    if cert:
        return jsonify({
            'valid': True,
            'certificate': dict(cert)
        })
    return jsonify({'valid': False, 'error': 'Certificat non trouvé'}), 404

# ====== API - STATISTIQUES ======
@app.route('/api/stats/overview')
def api_stats():
    """Statistiques globales"""
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

# ====== API - AUTHENTIFICATION ======
@app.route('/api/auth/login', methods=['POST'])
def api_login():
    """Connexion utilisateur"""
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

@app.route('/api/auth/register', methods=['POST'])
def api_register_user():
    """Création de compte utilisateur"""
    data = request.get_json()
    
    conn = get_db()
    
    # Vérifier si l'email existe déjà
    existing = conn.execute(
        "SELECT id FROM users WHERE email = ?", 
        (data['email'],)
    ).fetchone()
    
    if existing:
        conn.close()
        return jsonify({'success': False, 'error': 'Email déjà utilisé'}), 400
    
    # Créer l'utilisateur
    password_hash = hashlib.sha256(data['password'].encode()).hexdigest()
    user_id = conn.execute("""
        INSERT INTO users (
            uuid, email, password_hash, first_name, last_name, phone, date_of_birth
        ) VALUES (?, ?, ?, ?, ?, ?, ?)
    """, (
        str(uuid.uuid4()), data['email'], password_hash,
        data['first_name'], data['last_name'],
        data.get('phone'), data.get('date_of_birth')
    )).lastrowid
    
    conn.commit()
    conn.close()
    
    return jsonify({
        'success': True,
        'user_id': user_id,
        'message': 'Utilisateur créé avec succès'
    })

@app.route('/api/auth/logout', methods=['POST'])
def api_logout():
    """Déconnexion"""
    return jsonify({'success': True})

# ====== LANCEMENT ======
if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=False)
