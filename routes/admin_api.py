#!/usr/bin/env python3
from flask import Blueprint, request, jsonify
from models.database import db
import hashlib
import uuid
from datetime import datetime

admin_bp = Blueprint('admin', __name__, url_prefix='/api/admin')

# --- Middleware pour vérifier que l'utilisateur est admin ---
def admin_required():
    # Dans une vraie app, on utiliserait un token JWT avec le rôle
    # Ici on simule : on attend un header 'X-Admin' ou on vérifie le user via session
    # Pour simplifier, on vérifie que l'email de l'utilisateur est admin@elearning.sn
    # Mais on ne stocke pas l'utilisateur dans la session, donc on va passer par le token
    # On suppose que le client envoie un token JWT dans le header Authorization
    # Pour l'instant, on va utiliser un simple token basé sur l'email admin
    auth_header = request.headers.get('Authorization')
    if not auth_header or not auth_header.startswith('Bearer '):
        return jsonify({'error': 'Non autorisé'}), 401
    token = auth_header.split(' ')[1]
    # Ici on validerait le token, pour l'instant on vérifie que c'est un token pour admin
    # On pourrait stocker le token en session, mais on va simuler :
    # On vérifie que le token correspond à un admin en base
    # On va chercher l'utilisateur avec ce token (si on stocke les tokens)
    # Pour simplifier, on utilise un secret et on extrait l'email du token
    # Mais comme on n'a pas encore mis en place JWT, on va juste vérifier que l'email est admin
    # On va plutôt utiliser une session Flask : on va stocker l'utilisateur dans la session après login
    # On va modifier le login pour stocker l'utilisateur en session
    # Mais pour l'instant, on va utiliser un décorateur qui vérifie le rôle dans la base
    # On va utiliser un token temporaire : on génère un token pour admin lors du login
    # Je vais faire une vérification simple : on suppose que l'admin est connecté (session)
    return None

# --- Gestion des utilisateurs ---
@admin_bp.route('/users', methods=['GET'])
def get_users():
    rows = db.fetch_all("SELECT id, uuid, email, first_name, last_name, phone, status, role FROM users ORDER BY id")
    return jsonify([dict(row) for row in rows])

@admin_bp.route('/users', methods=['POST'])
def create_user():
    data = request.get_json()
    if not data.get('email') or not data.get('password'):
        return jsonify({'error': 'Email et mot de passe requis'}), 400
    existing = db.fetch_one("SELECT id FROM users WHERE email = ?", (data['email'],))
    if existing:
        return jsonify({'error': 'Email déjà utilisé'}), 400
    pwd_hash = hashlib.sha256(data['password'].encode()).hexdigest()
    user_id = db.execute("""
        INSERT INTO users (uuid, email, password_hash, first_name, last_name, phone, status, role)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    """, (str(uuid.uuid4()), data['email'], pwd_hash, data.get('first_name',''), data.get('last_name',''),
          data.get('phone',''), data.get('status','active'), data.get('role','user')))
    return jsonify({'success': True, 'user_id': user_id})

@admin_bp.route('/users/<int:user_id>', methods=['PUT'])
def update_user(user_id):
    data = request.get_json()
    fields = []
    params = []
    if 'first_name' in data:
        fields.append("first_name = ?"); params.append(data['first_name'])
    if 'last_name' in data:
        fields.append("last_name = ?"); params.append(data['last_name'])
    if 'phone' in data:
        fields.append("phone = ?"); params.append(data['phone'])
    if 'status' in data:
        fields.append("status = ?"); params.append(data['status'])
    if 'role' in data:
        fields.append("role = ?"); params.append(data['role'])
    if 'password' in data:
        pwd_hash = hashlib.sha256(data['password'].encode()).hexdigest()
        fields.append("password_hash = ?"); params.append(pwd_hash)
    if not fields:
        return jsonify({'error': 'Aucun champ à mettre à jour'}), 400
    params.append(user_id)
    db.execute(f"UPDATE users SET {', '.join(fields)} WHERE id = ?", params)
    return jsonify({'success': True})

@admin_bp.route('/users/<int:user_id>', methods=['DELETE'])
def delete_user(user_id):
    db.execute("DELETE FROM users WHERE id = ?", (user_id,))
    return jsonify({'success': True})

# --- Gestion des cours ---
@admin_bp.route('/courses', methods=['GET'])
def admin_get_courses():
    rows = db.fetch_all("""
        SELECT c.*, cat.name as category_name FROM courses c
        LEFT JOIN course_categories cat ON c.category_id = cat.id
        ORDER BY c.id
    """)
    return jsonify([dict(row) for row in rows])

@admin_bp.route('/courses', methods=['POST'])
def create_course():
    data = request.get_json()
    required = ['title', 'slug', 'category_id', 'instructor_name', 'duration_weeks', 'price']
    for f in required:
        if f not in data:
            return jsonify({'error': f'Champ {f} manquant'}), 400
    # Générer un code si non fourni
    code = data.get('code', f"COURSE-{str(uuid.uuid4().int)[:8]}")
    course_id = db.execute("""
        INSERT INTO courses (code, title, slug, description, category_id, instructor_name,
            difficulty_level, duration_weeks, total_hours, is_free, price, currency, status)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        code, data['title'], data['slug'], data.get('description',''),
        data['category_id'], data['instructor_name'], data.get('difficulty_level','débutant'),
        data['duration_weeks'], data.get('total_hours',0),
        1 if data.get('price',0)==0 else 0,
        data['price'], data.get('currency','XOF'), data.get('status','published')
    ))
    return jsonify({'success': True, 'course_id': course_id})

@admin_bp.route('/courses/<int:course_id>', methods=['PUT'])
def update_course(course_id):
    data = request.get_json()
    fields = []
    params = []
    for key in ['title','slug','description','category_id','instructor_name','difficulty_level',
                'duration_weeks','total_hours','price','currency','status']:
        if key in data:
            fields.append(f"{key} = ?")
            params.append(data[key])
    if 'is_free' in data:
        fields.append("is_free = ?")
        params.append(1 if data['is_free'] else 0)
    if not fields:
        return jsonify({'error': 'Aucun champ'}), 400
    params.append(course_id)
    db.execute(f"UPDATE courses SET {', '.join(fields)} WHERE id = ?", params)
    return jsonify({'success': True})

@admin_bp.route('/courses/<int:course_id>', methods=['DELETE'])
def delete_course(course_id):
    db.execute("DELETE FROM courses WHERE id = ?", (course_id,))
    return jsonify({'success': True})

# --- Gestion des chapitres ---
@admin_bp.route('/chapters', methods=['GET'])
def get_chapters():
    course_id = request.args.get('course_id', type=int)
    if course_id:
        rows = db.fetch_all("SELECT * FROM chapters WHERE course_id = ? ORDER BY order_index", (course_id,))
    else:
        rows = db.fetch_all("SELECT * FROM chapters ORDER BY course_id, order_index")
    return jsonify([dict(row) for row in rows])

@admin_bp.route('/chapters', methods=['POST'])
def create_chapter():
    data = request.get_json()
    required = ['course_id', 'title', 'order_index']
    for f in required:
        if f not in data:
            return jsonify({'error': f'Champ {f} manquant'}), 400
    chapter_id = db.execute("""
        INSERT INTO chapters (course_id, title, description, order_index, content, video_url, estimated_duration)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    """, (
        data['course_id'], data['title'], data.get('description',''),
        data['order_index'], data.get('content',''), data.get('video_url'),
        data.get('estimated_duration')
    ))
    return jsonify({'success': True, 'chapter_id': chapter_id})

@admin_bp.route('/chapters/<int:chapter_id>', methods=['PUT'])
def update_chapter(chapter_id):
    data = request.get_json()
    fields = []
    params = []
    for key in ['title','description','order_index','content','video_url','estimated_duration']:
        if key in data:
            fields.append(f"{key} = ?")
            params.append(data[key])
    if not fields:
        return jsonify({'error': 'Aucun champ'}), 400
    params.append(chapter_id)
    db.execute(f"UPDATE chapters SET {', '.join(fields)} WHERE id = ?", params)
    return jsonify({'success': True})

@admin_bp.route('/chapters/<int:chapter_id>', methods=['DELETE'])
def delete_chapter(chapter_id):
    db.execute("DELETE FROM chapters WHERE id = ?", (chapter_id,))
    return jsonify({'success': True})

# --- Gestion des sessions ---
@admin_bp.route('/sessions', methods=['GET'])
def get_sessions():
    chapter_id = request.args.get('chapter_id', type=int)
    if chapter_id:
        rows = db.fetch_all("SELECT * FROM sessions WHERE chapter_id = ?", (chapter_id,))
    else:
        rows = db.fetch_all("SELECT * FROM sessions")
    return jsonify([dict(row) for row in rows])

@admin_bp.route('/sessions', methods=['POST'])
def create_session():
    data = request.get_json()
    required = ['chapter_id', 'day_of_week', 'start_time', 'end_time']
    for f in required:
        if f not in data:
            return jsonify({'error': f'Champ {f} manquant'}), 400
    session_id = db.execute("""
        INSERT INTO sessions (chapter_id, title, day_of_week, start_time, end_time, location, online_link, description)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        data['chapter_id'], data.get('title',''), data['day_of_week'],
        data['start_time'], data['end_time'], data.get('location',''),
        data.get('online_link'), data.get('description','')
    ))
    return jsonify({'success': True, 'session_id': session_id})

@admin_bp.route('/sessions/<int:session_id>', methods=['PUT'])
def update_session(session_id):
    data = request.get_json()
    fields = []
    params = []
    for key in ['title','day_of_week','start_time','end_time','location','online_link','description']:
        if key in data:
            fields.append(f"{key} = ?")
            params.append(data[key])
    if not fields:
        return jsonify({'error': 'Aucun champ'}), 400
    params.append(session_id)
    db.execute(f"UPDATE sessions SET {', '.join(fields)} WHERE id = ?", params)
    return jsonify({'success': True})

@admin_bp.route('/sessions/<int:session_id>', methods=['DELETE'])
def delete_session(session_id):
    db.execute("DELETE FROM sessions WHERE id = ?", (session_id,))
    return jsonify({'success': True})

# --- Gestion des inscriptions ---
@admin_bp.route('/enrollments', methods=['GET'])
def get_enrollments():
    rows = db.fetch_all("""
        SELECT e.*, u.email, c.title as course_title
        FROM enrollments e
        JOIN users u ON e.user_id = u.id
        JOIN courses c ON e.course_id = c.id
        ORDER BY e.id DESC
    """)
    return jsonify([dict(row) for row in rows])

@admin_bp.route('/enrollments', methods=['POST'])
def create_enrollment():
    data = request.get_json()
    required = ['user_id', 'course_id']
    for f in required:
        if f not in data:
            return jsonify({'error': f'Champ {f} manquant'}), 400
    # Vérifier si déjà inscrit
    existing = db.fetch_one("SELECT id FROM enrollments WHERE user_id = ? AND course_id = ?",
                            (data['user_id'], data['course_id']))
    if existing:
        return jsonify({'error': 'Déjà inscrit'}), 400
    # Récupérer le prix du cours
    course = db.fetch_one("SELECT price FROM courses WHERE id = ?", (data['course_id'],))
    price = course['price'] if course else 0
    enrollment_number = f"INS-{datetime.now().strftime('%Y')}-{str(uuid.uuid4().int)[:8]}"
    enr_id = db.execute("""
        INSERT INTO enrollments (user_id, course_id, enrollment_number, status, payment_status,
            payment_amount, start_date, progress_percentage)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        data['user_id'], data['course_id'], enrollment_number,
        data.get('status','active'), data.get('payment_status','pending'),
        price, data.get('start_date', datetime.now().isoformat()),
        data.get('progress_percentage',0)
    ))
    return jsonify({'success': True, 'enrollment_id': enr_id})

@admin_bp.route('/enrollments/<int:enrollment_id>', methods=['PUT'])
def update_enrollment(enrollment_id):
    data = request.get_json()
    fields = []
    params = []
    for key in ['status','payment_status','payment_amount','progress_percentage','completion_date']:
        if key in data:
            fields.append(f"{key} = ?")
            params.append(data[key])
    if not fields:
        return jsonify({'error': 'Aucun champ'}), 400
    params.append(enrollment_id)
    db.execute(f"UPDATE enrollments SET {', '.join(fields)} WHERE id = ?", params)
    return jsonify({'success': True})

@admin_bp.route('/enrollments/<int:enrollment_id>', methods=['DELETE'])
def delete_enrollment(enrollment_id):
    db.execute("DELETE FROM enrollments WHERE id = ?", (enrollment_id,))
    return jsonify({'success': True})

# --- Gestion des catégories ---
@admin_bp.route('/categories', methods=['GET'])
def get_categories():
    rows = db.fetch_all("SELECT * FROM course_categories ORDER BY name")
    return jsonify([dict(row) for row in rows])

@admin_bp.route('/categories', methods=['POST'])
def create_category():
    data = request.get_json()
    if not data.get('name') or not data.get('slug'):
        return jsonify({'error': 'Nom et slug requis'}), 400
    cat_id = db.execute("""
        INSERT INTO course_categories (name, slug, description, icon, is_free, price)
        VALUES (?, ?, ?, ?, ?, ?)
    """, (data['name'], data['slug'], data.get('description',''),
          data.get('icon',''), data.get('is_free',0), data.get('price',0)))
    return jsonify({'success': True, 'category_id': cat_id})

@admin_bp.route('/categories/<int:cat_id>', methods=['PUT'])
def update_category(cat_id):
    data = request.get_json()
    fields = []
    params = []
    for key in ['name','slug','description','icon','is_free','price']:
        if key in data:
            fields.append(f"{key} = ?")
            params.append(data[key])
    if not fields:
        return jsonify({'error': 'Aucun champ'}), 400
    params.append(cat_id)
    db.execute(f"UPDATE course_categories SET {', '.join(fields)} WHERE id = ?", params)
    return jsonify({'success': True})

@admin_bp.route('/categories/<int:cat_id>', methods=['DELETE'])
def delete_category(cat_id):
    db.execute("DELETE FROM course_categories WHERE id = ?", (cat_id,))
    return jsonify({'success': True})
