#!/usr/bin/env python3
from flask import Blueprint, request, jsonify, send_file
from services.certificate_service import CertificateService
from services.payment_service import PaymentService
from services.export_service import ExportService
from models.database import db

advanced_bp = Blueprint('advanced', __name__, url_prefix='/api/advanced')

@advanced_bp.route('/test')
def test():
    return jsonify({'status': 'ok'})

@advanced_bp.route('/certificate/generate/<int:enrollment_id>', methods=['POST'])
def generate_certificate(enrollment_id):
    enrollment = db.fetch_one("""
        SELECT e.*, u.first_name, u.last_name, c.title as course_title
        FROM enrollments e
        JOIN users u ON e.user_id = u.id
        JOIN courses c ON e.course_id = c.id
        WHERE e.id = ?
    """, (enrollment_id,))
    if not enrollment:
        return jsonify({'error': 'Inscription non trouvée'}), 404
    student_name = f"{enrollment['first_name']} {enrollment['last_name']}"
    result = CertificateService.generate_certificate(
        enrollment_id, student_name, enrollment['course_title']
    )
    return jsonify(result)

@advanced_bp.route('/certificate/download/<int:enrollment_id>', methods=['GET'])
def download_certificate(enrollment_id):
    cert = CertificateService.get_certificate_by_enrollment(enrollment_id)
    if not cert or not cert.get('file_path'):
        return jsonify({'error': 'Certificat non trouvé'}), 404
    return send_file(cert['file_path'], as_attachment=True)

@advanced_bp.route('/pay', methods=['POST'])
def process_payment():
    data = request.get_json()
    method = data.get('method')
    if not method:
        return jsonify({'error': 'Méthode de paiement requise'}), 400
    result = PaymentService.process_payment(method, data)
    return jsonify(result)

@advanced_bp.route('/export/enrollments', methods=['GET'])
def export_enrollments():
    format = request.args.get('format', 'csv')
    filepath = ExportService.export_enrollments(format)
    return send_file(filepath, as_attachment=True)

@advanced_bp.route('/export/grades', methods=['GET'])
def export_grades():
    format = request.args.get('format', 'csv')
    filepath = ExportService.export_grades(format)
    return send_file(filepath, as_attachment=True)

@advanced_bp.route('/chart-data', methods=['GET'])
def get_chart_data():
    course_data = db.fetch_all("""
        SELECT c.title, COUNT(e.id) as count
        FROM courses c
        LEFT JOIN enrollments e ON e.course_id = c.id
        WHERE e.status IN ('active', 'completed')
        GROUP BY c.id
        ORDER BY count DESC
        LIMIT 10
    """)
    course_labels = [row['title'] for row in course_data]
    course_counts = [row['count'] for row in course_data]
    
    revenue_data = db.fetch_all("""
        SELECT strftime('%Y-%m', created_at) as month, SUM(amount) as total
        FROM payments
        WHERE status = 'completed'
        GROUP BY month
        ORDER BY month DESC
        LIMIT 6
    """)
    revenue_data.reverse()
    revenue_labels = [row['month'] for row in revenue_data]
    revenue_values = [float(row['total']) for row in revenue_data]
    
    progress_data = db.fetch_all("""
        SELECT 
            SUM(CASE WHEN progress_percentage < 25 THEN 1 ELSE 0 END) as g1,
            SUM(CASE WHEN progress_percentage BETWEEN 25 AND 50 THEN 1 ELSE 0 END) as g2,
            SUM(CASE WHEN progress_percentage BETWEEN 51 AND 75 THEN 1 ELSE 0 END) as g3,
            SUM(CASE WHEN progress_percentage > 75 THEN 1 ELSE 0 END) as g4
        FROM enrollments
        WHERE status = 'active'
    """)
    progress_groups = [progress_data[0]['g1'], progress_data[0]['g2'], progress_data[0]['g3'], progress_data[0]['g4']]
    
    category_data = db.fetch_all("""
        SELECT cat.name, COUNT(e.id) as count
        FROM course_categories cat
        LEFT JOIN courses c ON c.category_id = cat.id
        LEFT JOIN enrollments e ON e.course_id = c.id
        WHERE e.status IN ('active', 'completed')
        GROUP BY cat.id
        ORDER BY count DESC
    """)
    category_labels = [row['name'] for row in category_data]
    category_counts = [row['count'] for row in category_data]
    
    return jsonify({
        'course_labels': course_labels,
        'course_counts': course_counts,
        'revenue_labels': revenue_labels,
        'revenue_values': revenue_values,
        'progress_groups': progress_groups,
        'category_labels': category_labels,
        'category_counts': category_counts
    })
