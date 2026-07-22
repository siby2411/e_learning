#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Service d'inscription aux cours en ligne
"""

import hashlib
import uuid
import json
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, List
import qrcode
import os
from ..models.database import db

class EnrollmentService:
    """Service principal de gestion des inscriptions"""
    
    @classmethod
    def register_for_course(cls, user_data: Dict[str, Any], course_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Inscription à un cours
        """
        # Vérifier si l'utilisateur existe déjà
        user_id = cls._get_or_create_user(user_data)
        
        # Vérifier si déjà inscrit au cours
        existing = db.fetch_one("""
            SELECT id, status FROM enrollments 
            WHERE user_id = ? AND course_id = ?
        """, (user_id, course_data['course_id']))
        
        if existing and existing['status'] in ['active', 'pending']:
            return {'success': False, 'error': 'Vous êtes déjà inscrit à ce cours', 'enrollment_id': existing['id']}
        
        # Récupérer les informations du cours
        course = cls._get_course(course_data['course_id'])
        if not course:
            return {'success': False, 'error': 'Cours non trouvé'}
        
        # Générer le numéro d'inscription
        enrollment_number = cls._generate_enrollment_number()
        
        # Créer l'inscription
        enrollment_id = db.execute("""
            INSERT INTO enrollments (
                user_id, course_id, enrollment_number, status, payment_status,
                payment_amount, payment_currency, start_date
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            user_id, course_data['course_id'], enrollment_number,
            'pending' if not course['is_free'] else 'active',
            'pending' if not course['is_free'] else 'paid',
            course['price'], course['currency'], datetime.now().isoformat()
        ))
        
        # Si le cours est gratuit, activer immédiatement
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
        """
        Traite un paiement pour l'inscription
        """
        # Vérifier l'inscription
        enrollment = db.fetch_one("""
            SELECT e.*, c.title, c.price 
            FROM enrollments e
            JOIN courses c ON e.course_id = c.id
            WHERE e.id = ?
        """, (enrollment_id,))
        
        if not enrollment:
            return {'success': False, 'error': 'Inscription non trouvée'}
        
        if enrollment['payment_status'] == 'paid':
            return {'success': False, 'error': 'Paiement déjà effectué'}
        
        # Enregistrement du paiement
        transaction_id = str(uuid.uuid4())
        payment_id = db.execute("""
            INSERT INTO payments (
                enrollment_id, transaction_id, amount, currency,
                payment_method, payment_reference, status
            ) VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (
            enrollment_id, transaction_id, payment_data['amount'],
            payment_data['currency'], payment_data['method'],
            payment_data.get('reference'), 'pending'
        ))
        
        # Simulation de vérification
        if cls._verify_payment(payment_data):
            # Mise à jour du paiement
            db.execute("""
                UPDATE payments SET status = 'completed', processed_at = ? 
                WHERE id = ?
            """, (datetime.now().isoformat(), payment_id))
            
            # Activation de l'inscription
            cls._activate_enrollment(enrollment_id)
            
            return {
                'success': True,
                'payment_id': payment_id,
                'enrollment_id': enrollment_id,
                'enrollment_number': enrollment['enrollment_number']
            }
        
        return {'success': False, 'error': 'Échec du paiement'}
    
    @classmethod
    def _activate_enrollment(cls, enrollment_id: int):
        """Active une inscription"""
        db.execute("""
            UPDATE enrollments 
            SET status = 'active', payment_status = 'paid', updated_at = ?
            WHERE id = ?
        """, (datetime.now().isoformat(), enrollment_id))
        
        # Mise à jour des statistiques
        db.execute("""
            UPDATE course_stats 
            SET active_enrollments = active_enrollments + 1,
                total_revenue = total_revenue + (
                    SELECT payment_amount FROM enrollments WHERE id = ?
                )
            WHERE course_id = (SELECT course_id FROM enrollments WHERE id = ?)
        """, (enrollment_id, enrollment_id))
    
    @classmethod
    def complete_module(cls, enrollment_id: int, module_id: int) -> Dict[str, Any]:
        """
        Marque un module comme terminé
        """
        # Vérifier l'inscription
        enrollment = db.fetch_one("""
            SELECT id, user_id, course_id, status 
            FROM enrollments WHERE id = ?
        """, (enrollment_id,))
        
        if not enrollment or enrollment['status'] != 'active':
            return {'success': False, 'error': 'Inscription invalide ou inactive'}
        
        # Vérifier que le module appartient bien au cours
        module = db.fetch_one("""
            SELECT id FROM course_modules 
            WHERE id = ? AND course_id = ?
        """, (module_id, enrollment['course_id']))
        
        if not module:
            return {'success': False, 'error': 'Module non trouvé'}
        
        # Enregistrer la progression
        db.execute("""
            INSERT OR REPLACE INTO user_progress 
            (enrollment_id, module_id, is_completed, completed_at)
            VALUES (?, ?, ?, ?)
        """, (enrollment_id, module_id, 1, datetime.now().isoformat()))
        
        # Calculer la progression
        progress = cls._calculate_progress(enrollment_id)
        
        # Mettre à jour la progression
        db.execute("""
            UPDATE enrollments SET progress_percentage = ?, updated_at = ?
            WHERE id = ?
        """, (progress, datetime.now().isoformat(), enrollment_id))
        
        # Vérifier si tout est terminé
        if progress == 100:
            cls._complete_course(enrollment_id)
        
        return {'success': True, 'progress': progress}
    
    @classmethod
    def _complete_course(cls, enrollment_id: int):
        """Termine un cours et génère le certificat"""
        # Mettre à jour le statut
        db.execute("""
            UPDATE enrollments 
            SET status = 'completed', completion_date = ?, updated_at = ?
            WHERE id = ?
        """, (datetime.now().isoformat(), datetime.now().isoformat(), enrollment_id))
        
        # Générer le certificat
        certificate_number = cls._generate_certificate_number()
        
        # Créer le certificat
        certificate_id = db.execute("""
            INSERT INTO certificates (
                enrollment_id, certificate_number, issued_date
            ) VALUES (?, ?, ?)
        """, (enrollment_id, certificate_number, datetime.now().isoformat()))
        
        # Mettre à jour les statistiques
        db.execute("""
            UPDATE course_stats 
            SET completions = completions + 1
            WHERE course_id = (SELECT course_id FROM enrollments WHERE id = ?)
        """, (enrollment_id,))
        
        # Génération du QR Code (optionnel)
        cls._generate_qr_code(certificate_number)
    
    @classmethod
    def get_enrollment(cls, enrollment_id: int) -> Optional[Dict[str, Any]]:
        """Récupère les détails d'une inscription"""
        result = db.fetch_one("""
            SELECT 
                e.*,
                u.first_name, u.last_name, u.email,
                c.title as course_title, c.slug as course_slug,
                cat.name as category_name
            FROM enrollments e
            JOIN users u ON e.user_id = u.id
            JOIN courses c ON e.course_id = c.id
            JOIN course_categories cat ON c.category_id = cat.id
            WHERE e.id = ?
        """, (enrollment_id,))
        
        if result:
            return dict(result)
        return None
    
    @classmethod
    def get_user_enrollments(cls, user_id: int) -> List[Dict[str, Any]]:
        """Récupère toutes les inscriptions d'un utilisateur"""
        results = db.fetch_all("""
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
        """, (user_id,))
        
        return [dict(row) for row in results]
    
    @classmethod
    def get_course_statistics(cls, course_id: int) -> Dict[str, Any]:
        """Statistiques d'un cours"""
        stats = db.fetch_one("""
            SELECT * FROM course_stats WHERE course_id = ?
        """, (course_id,))
        
        if not stats:
            return {'total_enrollments': 0, 'active_enrollments': 0, 'completions': 0}
        return dict(stats)
    
    @staticmethod
    def _get_or_create_user(data: Dict[str, Any]) -> int:
        """Récupère ou crée un utilisateur"""
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
    
    @staticmethod
    def _get_course(course_id: int) -> Optional[Dict[str, Any]]:
        """Récupère les informations d'un cours"""
        result = db.fetch_one("""
            SELECT c.*, cat.is_free as category_free 
            FROM courses c
            LEFT JOIN course_categories cat ON c.category_id = cat.id
            WHERE c.id = ?
        """, (course_id,))
        return dict(result) if result else None
    
    @staticmethod
    def _generate_enrollment_number() -> str:
        """Génère un numéro d'inscription unique"""
        prefix = "INS"
        year = datetime.now().strftime("%Y")
        random_part = str(uuid.uuid4().int)[:8]
        return f"{prefix}-{year}-{random_part}"
    
    @staticmethod
    def _generate_certificate_number() -> str:
        """Génère un numéro de certificat unique"""
        prefix = "CERT"
        year = datetime.now().strftime("%Y")
        random_part = str(uuid.uuid4().int)[:8]
        return f"{prefix}-{year}-{random_part}"
    
    @staticmethod
    def _calculate_progress(enrollment_id: int) -> int:
        """Calcule le pourcentage de progression"""
        result = db.fetch_one("""
            SELECT 
                COUNT(DISTINCT m.id) as total_modules,
                COUNT(DISTINCT p.module_id) as completed_modules
            FROM course_modules m
            JOIN enrollments e ON e.course_id = m.course_id
            LEFT JOIN user_progress p ON p.module_id = m.id AND p.enrollment_id = e.id AND p.is_completed = 1
            WHERE e.id = ?
        """, (enrollment_id,))
        
        if result and result['total_modules'] > 0:
            return int((result['completed_modules'] / result['total_modules']) * 100)
        return 0
    
    @staticmethod
    def _verify_payment(payment_data: Dict[str, Any]) -> bool:
        """Simulation de vérification de paiement"""
        # À remplacer par intégration réelle (Orange Money, Wave, etc.)
        return True
    
    @staticmethod
    def _generate_qr_code(certificate_number: str):
        """Génère un QR Code pour le certificat"""
        try:
            qr = qrcode.QRCode(version=1, box_size=10, border=5)
            qr.add_data(f"https://cours.sn/certificat/{certificate_number}")
            qr.make(fit=True)
            
            img = qr.make_image(fill_color="black", back_color="white")
            os.makedirs("static/certificates", exist_ok=True)
            img.save(f"static/certificates/{certificate_number}.png")
        except Exception as e:
            print(f"Erreur génération QR Code: {e}")
