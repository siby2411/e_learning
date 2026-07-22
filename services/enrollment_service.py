#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Service d'inscription - Version sans QR Code
"""

import hashlib
import uuid
import json
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, List
from models.database import db

class EnrollmentService:
    """Service principal de gestion des inscriptions"""

    @classmethod
    def register_for_course(cls, user_data: Dict[str, Any], course_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Inscription à un cours (version simplifiée)
        """
        # Vérifier l'utilisateur
        user_id = cls._get_or_create_user(user_data)
        
        # Vérifier si déjà inscrit
        existing = db.fetch_one("""
            SELECT id, status FROM enrollments 
            WHERE user_id = ? AND course_id = ?
        """, (user_id, course_data['course_id']))
        
        if existing and existing['status'] in ['active', 'pending']:
            return {'success': False, 'error': 'Vous êtes déjà inscrit à ce cours'}

        # Récupérer le cours
        course = cls._get_course(course_data['course_id'])
        if not course:
            return {'success': False, 'error': 'Cours non trouvé'}

        # Générer le numéro d'inscription
        enrollment_number = f"INS-{datetime.now().strftime('%Y')}-{str(uuid.uuid4().int)[:8]}"

        # Créer l'inscription
        enrollment_id = db.execute("""
            INSERT INTO enrollments (
                user_id, course_id, enrollment_number, status, payment_status,
                payment_amount, payment_currency, start_date
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            user_id, course_data['course_id'], enrollment_number,
            'active' if course['is_free'] else 'pending',
            'paid' if course['is_free'] else 'pending',
            course['price'], course['currency'], datetime.now().isoformat()
        ))

        # Si cours gratuit, activer immédiatement
        if course['is_free']:
            cls._activate_enrollment(enrollment_id)
            return {
                'success': True,
                'enrollment_id': enrollment_id,
                'enrollment_number': enrollment_number,
                'is_free': True,
                'message': 'Inscription confirmée !'
            }

        return {
            'success': True,
            'enrollment_id': enrollment_id,
            'enrollment_number': enrollment_number,
            'amount': course['price'],
            'currency': course['currency'],
            'is_free': False,
            'payment_required': True
        }

    @classmethod
    def process_payment(cls, enrollment_id: int, payment_data: Dict[str, Any]) -> Dict[str, Any]:
        """Traite un paiement"""
        enrollment = db.fetch_one("""
            SELECT e.*, c.title, c.price 
            FROM enrollments e
            JOIN courses c ON e.course_id = c.id
            WHERE e.id = ?
        """, (enrollment_id,))
        
        if not enrollment:
            return {'success': False, 'error': 'Inscription non trouvée'}
        
        if enrollment['payment_status'] == 'paid':
            return {'success': False, 'error': 'Déjà payé'}
        
        transaction_id = str(uuid.uuid4())
        payment_id = db.execute("""
            INSERT INTO payments (
                enrollment_id, transaction_id, amount, currency,
                payment_method, payment_reference, status
            ) VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (
            enrollment_id, transaction_id, payment_data['amount'],
            payment_data['currency'], payment_data['method'],
            payment_data.get('reference'), 'completed'
        ))
        
        cls._activate_enrollment(enrollment_id)
        
        return {
            'success': True,
            'payment_id': payment_id,
            'enrollment_id': enrollment_id,
            'enrollment_number': enrollment['enrollment_number']
        }

    @classmethod
    def _activate_enrollment(cls, enrollment_id: int):
        db.execute("""
            UPDATE enrollments 
            SET status = 'active', payment_status = 'paid', updated_at = ?
            WHERE id = ?
        """, (datetime.now().isoformat(), enrollment_id))

    @classmethod
    def _get_or_create_user(cls, data: Dict[str, Any]) -> int:
        existing = db.fetch_one("SELECT id FROM users WHERE email = ?", (data['email'],))
        if existing:
            return existing['id']
        
        password_hash = hashlib.sha256(data['password'].encode()).hexdigest()
        return db.execute("""
            INSERT INTO users (
                uuid, email, password_hash, first_name, last_name, phone, date_of_birth
            ) VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (
            str(uuid.uuid4()), data['email'], password_hash,
            data['first_name'], data['last_name'],
            data.get('phone'), data.get('date_of_birth')
        ))

    @classmethod
    def _get_course(cls, course_id: int) -> Optional[Dict[str, Any]]:
        result = db.fetch_one("""
            SELECT c.*, cat.is_free as category_free 
            FROM courses c
            LEFT JOIN course_categories cat ON c.category_id = cat.id
            WHERE c.id = ?
        """, (course_id,))
        return dict(result) if result else None

    @classmethod
    def get_enrollment(cls, enrollment_id: int) -> Optional[Dict[str, Any]]:
        result = db.fetch_one("""
            SELECT 
                e.*,
                u.first_name, u.last_name, u.email,
                c.title as course_title, c.slug as course_slug
            FROM enrollments e
            JOIN users u ON e.user_id = u.id
            JOIN courses c ON e.course_id = c.id
            WHERE e.id = ?
        """, (enrollment_id,))
        return dict(result) if result else None

    @classmethod
    def get_user_enrollments(cls, user_id: int) -> List[Dict[str, Any]]:
        results = db.fetch_all("""
            SELECT 
                e.*,
                c.title as course_title
            FROM enrollments e
            JOIN courses c ON e.course_id = c.id
            WHERE e.user_id = ?
            ORDER BY e.created_at DESC
        """, (user_id,))
        return [dict(row) for row in results]

    @classmethod
    def get_course_statistics(cls, course_id: int) -> Dict[str, Any]:
        stats = db.fetch_one("""
            SELECT 
                COUNT(*) as total_enrollments,
                SUM(CASE WHEN status = 'active' THEN 1 ELSE 0 END) as active_enrollments,
                SUM(CASE WHEN status = 'completed' THEN 1 ELSE 0 END) as completions
            FROM enrollments
            WHERE course_id = ?
        """, (course_id,))
        return dict(stats) if stats else {}
