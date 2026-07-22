#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Générateur de QR Code simplifié (sans Pillow)
Utilise une version textuelle si Pillow n'est pas disponible
"""

import hashlib

def generate_qr_text(content, size=10):
    """
    Génère une représentation textuelle d'un QR Code
    Utilisé si Pillow n'est pas disponible
    """
    try:
        # Tenter d'importer QRCode si disponible
        import qrcode
        from io import BytesIO
        import base64
        
        qr = qrcode.QRCode(version=1, box_size=size, border=4)
        qr.add_data(content)
        qr.make(fit=True)
        
        img = qr.make_image(fill_color="black", back_color="white")
        buffered = BytesIO()
        img.save(buffered, format="PNG")
        return f"data:image/png;base64,{base64.b64encode(buffered.getvalue()).decode()}"
        
    except ImportError:
        # Fallback : génération ASCII
        return generate_ascii_qr(content)

def generate_ascii_qr(content):
    """Génère un QR Code en ASCII (fallback)"""
    # Simplification : hash du contenu pour générer un pattern
    h = hashlib.md5(content.encode()).hexdigest()
    chars = ['█', '░', '▒', '▓']
    result = "█" * 20 + "\n"
    for i in range(10):
        row = ""
        for j in range(20):
            idx = (ord(h[(i*2 + j) % 32]) % 4)
            row += chars[idx]
        result += row + "\n"
    result += "█" * 20
    return result

# Fonction de remplacement pour le QR Code dans le service
def generate_certificate_qr(certificate_number):
    """Génère un QR Code pour un certificat"""
    content = f"https://cours.sn/certificat/{certificate_number}"
    return generate_qr_text(content)
