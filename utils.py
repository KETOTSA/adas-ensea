import os
import uuid
from PIL import Image
from flask import current_app, request
from models import db, ActionLog
from flask_login import current_user


ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'webp'}


def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


def save_photo(file, subfolder='students', max_size=(800, 800)):
    """Save and resize an uploaded photo. Returns relative path."""
    if not file or not allowed_file(file.filename):
        return None
    
    ext = file.filename.rsplit('.', 1)[1].lower()
    filename = f"{uuid.uuid4().hex}.{ext}"
    folder = os.path.join(current_app.config['UPLOAD_FOLDER'], subfolder)
    os.makedirs(folder, exist_ok=True)
    filepath = os.path.join(folder, filename)
    
    img = Image.open(file)
    img.thumbnail(max_size, Image.LANCZOS)
    
    if img.mode in ('RGBA', 'P'):
        img = img.convert('RGB')
    
    img.save(filepath, optimize=True, quality=85)
    return f"uploads/{subfolder}/{filename}"


def log_action(action, details=None):
    """Log an admin/user action."""
    try:
        log = ActionLog(
            user_id=current_user.id if current_user.is_authenticated else None,
            action=action,
            details=details,
            ip_address=request.remote_addr
        )
        db.session.add(log)
        db.session.commit()
    except Exception as e:
        print(f"Log error: {e}")


def generate_student_code(annee_inscription):
    """Generate unique student code like ADAS-2023-001"""
    from models import Student
    year = annee_inscription.split('-')[0] if '-' in annee_inscription else annee_inscription
    count = Student.query.filter(Student.annee_inscription == annee_inscription).count() + 1
    return f"ADAS-{year}-{count:03d}"


def generate_username(prenom, nom, annee_inscription):
    """Generate username like jdoe2023"""
    year = annee_inscription.split('-')[0] if '-' in annee_inscription else annee_inscription
    base = f"{prenom[0].lower()}{nom.lower().replace(' ', '')}{year}"
    # Remove accents
    import unicodedata
    base = ''.join(c for c in unicodedata.normalize('NFD', base) if unicodedata.category(c) != 'Mn')
    return base[:20]


def get_annee_courante():
    from datetime import datetime
    now = datetime.utcnow()
    if now.month >= 9:
        return f"{now.year}-{now.year+1}"
    return f"{now.year-1}-{now.year}"
