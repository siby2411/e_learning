#!/usr/bin/env python3
from flask import Blueprint, request, jsonify
from models.database import db

academic_bp = Blueprint('academic', __name__, url_prefix='/api/academic')

@academic_bp.route('/financial', methods=['GET'])
def get_financial():
    revenue = db.fetch_one("SELECT COALESCE(SUM(amount),0) as total_revenue, COUNT(*) as total_transactions, AVG(amount) as average_payment FROM payments WHERE status='completed'")
    by_course = db.fetch_all("SELECT c.title as course_title, COUNT(DISTINCT e.id) as enrollments, COALESCE(SUM(p.amount),0) as revenue FROM courses c LEFT JOIN enrollments e ON e.course_id=c.id LEFT JOIN payments p ON p.enrollment_id=e.id AND p.status='completed' WHERE e.status IN ('active','completed') GROUP BY c.id ORDER BY revenue DESC")
    outstanding = db.fetch_all("SELECT u.first_name, u.last_name, c.title as course_title, c.price as total_fees, COALESCE(SUM(p.amount),0) as paid, c.price - COALESCE(SUM(p.amount),0) as balance FROM enrollments e JOIN users u ON e.user_id=u.id JOIN courses c ON e.course_id=c.id LEFT JOIN payments p ON p.enrollment_id=e.id AND p.status='completed' WHERE e.status IN ('active','pending') GROUP BY e.id HAVING balance>0 ORDER BY balance DESC")
    return jsonify({'revenue': dict(revenue) if revenue else {}, 'by_course': [dict(r) for r in by_course], 'outstanding': [dict(r) for r in outstanding]})

@academic_bp.route('/enrollments', methods=['GET'])
def get_enrollments():
    status = request.args.get('status')
    course_id = request.args.get('course_id', type=int)
    search = request.args.get('search')
    query = "SELECT e.id as enrollment_id, u.id as user_id, u.first_name, u.last_name, u.email, c.id as course_id, c.title as course_title, e.status, e.payment_status, e.progress_percentage, COALESCE((SELECT ROUND(AVG(g.score * ex.coefficient) / AVG(ex.coefficient), 2) FROM grades g JOIN exams ex ON g.exam_id=ex.id WHERE g.enrollment_id=e.id),0) as average_score, e.start_date, e.completion_date FROM enrollments e JOIN users u ON e.user_id=u.id JOIN courses c ON e.course_id=c.id WHERE 1=1"
    params=[]
    if status:
        query += " AND e.status = ?"; params.append(status)
    if course_id:
        query += " AND e.course_id = ?"; params.append(course_id)
    if search:
        query += " AND (u.first_name LIKE ? OR u.last_name LIKE ? OR u.email LIKE ?)"
        s = f"%{search}%"; params.extend([s,s,s])
    query += " ORDER BY e.created_at DESC"
    rows = db.fetch_all(query, params)
    return jsonify([dict(row) for row in rows])

@academic_bp.route('/results', methods=['GET'])
def get_results():
    course_id = request.args.get('course_id', type=int)
    query = "SELECT u.first_name, u.last_name, c.title as course_title, e.total_score as final_grade, CASE WHEN e.total_score >= 10 THEN 'validé' WHEN e.total_score IS NOT NULL AND e.total_score < 10 THEN 'échec' ELSE 'en cours' END as final_result, e.payment_status FROM enrollments e JOIN users u ON e.user_id=u.id JOIN courses c ON e.course_id=c.id WHERE e.status IN ('active','completed')"
    params=[]
    if course_id:
        query += " AND e.course_id = ?"; params.append(course_id)
    rows = db.fetch_all(query, params)
    return jsonify([dict(row) for row in rows])

@academic_bp.route('/exams/course/<int:course_id>', methods=['GET'])
def get_exams(course_id):
    rows = db.fetch_all("SELECT * FROM exams WHERE course_id = ?", (course_id,))
    return jsonify([dict(row) for row in rows])

@academic_bp.route('/transcript/<int:enrollment_id>', methods=['GET'])
def get_transcript(enrollment_id):
    student = db.fetch_one("SELECT u.first_name, u.last_name, u.email, c.title as course_title, c.code as course_code, e.enrollment_number, e.start_date, e.status FROM enrollments e JOIN users u ON e.user_id=u.id JOIN courses c ON e.course_id=c.id WHERE e.id=?", (enrollment_id,))
    if not student: return jsonify({'error':'Inscription non trouvée'}), 404
    grades = db.fetch_all("SELECT ex.title as exam_title, ex.coefficient, ex.max_score, g.score, g.is_passed, g.graded_at, g.comments FROM grades g JOIN exams ex ON g.exam_id=ex.id WHERE g.enrollment_id=? ORDER BY ex.scheduled_date", (enrollment_id,))
    stats = db.fetch_one("SELECT COUNT(*) as total_exams, SUM(CASE WHEN is_passed=1 THEN 1 ELSE 0 END) as passed, ROUND(AVG(score),2) as average, MAX(score) as best_score, MIN(score) as worst_score FROM grades WHERE enrollment_id=?", (enrollment_id,))
    return jsonify({'student': dict(student), 'grades': [dict(g) for g in grades], 'statistics': dict(stats) if stats else {}})
