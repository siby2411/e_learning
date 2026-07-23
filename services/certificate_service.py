#!/usr/bin/env python3
from fpdf import FPDF
import os
from datetime import datetime
import uuid
from models.database import db

class CertificateService:
    @staticmethod
    def generate_certificate(enrollment_id, student_name, course_title, completion_date=None):
        cert = db.fetch_one("SELECT * FROM certificates WHERE enrollment_id = ?", (enrollment_id,))
        if cert:
            return {'exists': True, 'file_path': cert['file_path']}
        os.makedirs('static/certificates', exist_ok=True)
        cert_number = f"CERT-{datetime.now().strftime('%Y')}-{str(uuid.uuid4().int)[:8]}"
        file_name = f"cert_{enrollment_id}_{cert_number}.pdf"
        file_path = os.path.join('static/certificates', file_name)
        pdf = FPDF('L', 'mm', 'A4')
        pdf.add_page()
        pdf.set_draw_color(26,35,126)
        pdf.set_line_width(1.5)
        pdf.rect(10,10,277,190)
        pdf.set_draw_color(13,71,161)
        pdf.rect(15,15,267,180)
        pdf.set_font('Helvetica','B',28)
        pdf.set_text_color(26,35,126)
        pdf.cell(0,30,'CERTIFICAT DE RÉUSSITE',ln=True,align='C')
        pdf.set_font('Helvetica','',16)
        pdf.set_text_color(0,0,0)
        pdf.cell(0,20,'Ce certificat atteste que',ln=True,align='C')
        pdf.set_font('Helvetica','B',24)
        pdf.set_text_color(26,35,126)
        pdf.cell(0,30,student_name,ln=True,align='C')
        pdf.set_font('Helvetica','',16)
        pdf.set_text_color(0,0,0)
        pdf.cell(0,20,'a complété avec succès la formation',ln=True,align='C')
        pdf.set_font('Helvetica','B',20)
        pdf.set_text_color(26,35,126)
        pdf.cell(0,25,course_title,ln=True,align='C')
        completion_date = completion_date or datetime.now().strftime('%d/%m/%Y')
        pdf.set_font('Helvetica','',14)
        pdf.set_text_color(0,0,0)
        pdf.cell(0,20,f'Délivré le {completion_date}',ln=True,align='C')
        pdf.set_font('Helvetica','I',10)
        pdf.cell(0,20,f'Numéro : {cert_number}',ln=True,align='C')
        pdf.line(140,170,180,170)
        pdf.set_font('Helvetica','',10)
        pdf.cell(0,8,'Signature du responsable',ln=True,align='C')
        pdf.output(file_path)
        db.execute("INSERT INTO certificates (enrollment_id, certificate_number, file_path, issued_date) VALUES (?,?,?,?)",
                   (enrollment_id, cert_number, file_path, datetime.now().isoformat()))
        db.execute("UPDATE enrollments SET certificate_generated = 1 WHERE id = ?", (enrollment_id,))
        return {'success': True, 'file_path': file_path, 'certificate_number': cert_number}
    
    @staticmethod
    def get_certificate_by_enrollment(enrollment_id):
        cert = db.fetch_one("SELECT * FROM certificates WHERE enrollment_id = ?", (enrollment_id,))
        return dict(cert) if cert else None
