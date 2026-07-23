#!/usr/bin/env python3
import uuid
from datetime import datetime
from models.database import db

class PaymentService:
    @staticmethod
    def process_payment(method, data):
        if method == 'simulation':
            return PaymentService._process_simulation(data)
        elif method == 'orange_money' or method == 'wave':
            # Pour l'instant, on simule aussi les paiements réels
            return PaymentService._process_simulation(data)
        else:
            return {'success': False, 'error': 'Méthode non supportée'}

    @staticmethod
    def _process_simulation(data):
        enrollment_id = data.get('enrollment_id')
        amount = data.get('amount')
        currency = data.get('currency', 'XOF')
        transaction_id = str(uuid.uuid4())

        payment_id = db.execute("""
            INSERT INTO payments (
                enrollment_id, transaction_id, amount, currency,
                payment_method, payment_reference, status, processed_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            enrollment_id, transaction_id, amount, currency,
            'simulation', transaction_id, 'completed', datetime.now().isoformat()
        ))

        db.execute("""
            UPDATE enrollments
            SET payment_status = 'paid', status = 'active'
            WHERE id = ?
        """, (enrollment_id,))

        return {
            'success': True,
            'payment_id': payment_id,
            'transaction_id': transaction_id,
            'method': 'simulation'
        }
