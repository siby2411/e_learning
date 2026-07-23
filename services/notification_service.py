#!/usr/bin/env python3
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.application import MIMEApplication
import os
from models.database import db

class NotificationService:
    # Configuration SMTP (remplacer par vos identifiants)
    SMTP_CONFIG = {
        'host': 'smtp.gmail.com',          # ou smtp.office365.com, etc.
        'port': 587,
        'username': 'votre_email@gmail.com',
        'password': 'votre_mot_de_passe_app',
        'from_email': 'votre_email@gmail.com'
    }

    @staticmethod
    def send_email(to_email, subject, body, attachment_path=None):
        """Envoie un email avec pièce jointe optionnelle"""
        try:
            msg = MIMEMultipart()
            msg['From'] = NotificationService.SMTP_CONFIG['from_email']
            msg['To'] = to_email
            msg['Subject'] = subject
            msg.attach(MIMEText(body, 'plain'))

            if attachment_path and os.path.exists(attachment_path):
                with open(attachment_path, 'rb') as f:
                    part = MIMEApplication(f.read(), Name=os.path.basename(attachment_path))
                part['Content-Disposition'] = f'attachment; filename="{os.path.basename(attachment_path)}"'
                msg.attach(part)

            server = smtplib.SMTP(NotificationService.SMTP_CONFIG['host'],
                                  NotificationService.SMTP_CONFIG['port'])
            server.starttls()
            server.login(NotificationService.SMTP_CONFIG['username'],
                         NotificationService.SMTP_CONFIG['password'])
            server.send_message(msg)
            server.quit()
            return {'success': True}
        except Exception as e:
            return {'success': False, 'error': str(e)}

    @staticmethod
    def send_certificate_email(enrollment_id):
        """Envoie le certificat par email à l'étudiant"""
        enrollment = db.fetch_one("""
            SELECT u.email, u.first_name, u.last_name, c.title as course_title
            FROM enrollments e
            JOIN users u ON e.user_id = u.id
            JOIN courses c ON e.course_id = c.id
            WHERE e.id = ?
        """, (enrollment_id,))

        if not enrollment:
            return {'success': False, 'error': 'Inscription non trouvée'}

        cert = db.fetch_one("SELECT * FROM certificates WHERE enrollment_id = ?", (enrollment_id,))
        if not cert or not cert.get('file_path'):
            return {'success': False, 'error': 'Certificat non trouvé'}

        subject = f"Félicitations ! Votre certificat pour {enrollment['course_title']}"
        body = f"""
        Bonjour {enrollment['first_name']} {enrollment['last_name']},

        Félicitations pour avoir complété la formation "{enrollment['course_title']}" !

        Veuillez trouver en pièce jointe votre certificat de réussite.

        Cordialement,
        L'équipe E-Learning Sénégal
        """
        return NotificationService.send_email(
            enrollment['email'],
            subject,
            body,
            cert['file_path']
        )
