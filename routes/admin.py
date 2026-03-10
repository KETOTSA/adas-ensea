import csv
import io
import json
from functools import wraps
from flask import Blueprint, render_template, redirect, url_for, flash, request, Response
from flask_login import login_required, current_user
from models import db, Student, User, Bureau, ActionLog
from utils import save_photo, log_action, generate_student_code, generate_username, get_annee_courante

admin_bp = Blueprint('admin', __name__)


def admin_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if not current_user.is_authenticated or not current_user.is_admin():
            flash('Accès réservé aux administrateurs.', 'danger')
            return redirect(url_for('auth.login'))
        return f(*args, **kwargs)
    return decorated


# ─── Dashboard ───────────────────────────────────────────────────────────────

@admin_bp.route('/')
@login_required
@admin_required
def dashboard():
    total_etudiants = Student.query.count()
    annee = get_annee_courante()
    bureau_actuel = Bureau.query.filter_by(annee_academique=annee).count()
    recent_logs = ActionLog.query.order_by(ActionLog.timestamp.desc()).limit(10).all()
    annees = db.session.query(Student.annee_inscription).distinct().order_by(Student.annee_inscription.desc()).all()
    return render_template('admin/dashboard.html', 
                           total_etudiants=total_etudiants,
                           bureau_actuel=bureau_actuel,
                           recent_logs=recent_logs,
                           annees=[a[0] for a in annees],
                           annee_courante=annee)


# ─── Students ─────────────────────────────────────────────────────────────────

@admin_bp.route('/etudiants')
@login_required
@admin_required
def liste_etudiants():
    search = request.args.get('q', '')
    annee = request.args.get('annee', '')
    query = Student.query
    if search:
        query = query.filter(
            (Student.nom.ilike(f'%{search}%')) |
            (Student.prenom.ilike(f'%{search}%')) |
            (Student.email.ilike(f'%{search}%')) |
            (Student.student_code.ilike(f'%{search}%'))
        )
    if annee:
        query = query.filter_by(annee_inscription=annee)
    etudiants = query.order_by(Student.nom).all()
    annees = db.session.query(Student.annee_inscription).distinct().order_by(Student.annee_inscription.desc()).all()
    return render_template('admin/etudiants.html', etudiants=etudiants, 
                           annees=[a[0] for a in annees], search=search, annee=annee)


@admin_bp.route('/etudiants/ajouter', methods=['GET', 'POST'])
@login_required
@admin_required
def ajouter_etudiant():
    if request.method == 'POST':
        annee = request.form.get('annee_inscription', get_annee_courante())
        
        student = Student(
            student_code=generate_student_code(annee),
            nom=request.form.get('nom', '').strip().upper(),
            prenom=request.form.get('prenom', '').strip().title(),
            nationalite=request.form.get('nationalite', '').strip(),
            email=request.form.get('email', '').strip().lower(),
            telephone=request.form.get('telephone', '').strip(),
            annee_inscription=annee,
            bio=request.form.get('bio', '').strip()
        )
        
        # Date de naissance
        dob = request.form.get('date_naissance')
        if dob:
            from datetime import date
            try:
                student.date_naissance = date.fromisoformat(dob)
            except:
                pass
        
        # Photo
        if 'photo' in request.files and request.files['photo'].filename:
            student.photo = save_photo(request.files['photo'], subfolder='students')
        
        db.session.add(student)
        db.session.flush()  # get id
        
        # Create user account
        username = generate_username(student.prenom, student.nom, annee)
        # Ensure unique
        base_username = username
        counter = 1
        while User.query.filter_by(username=username).first():
            username = f"{base_username}{counter}"
            counter += 1
        
        password = request.form.get('password') or f"StatDiv@{annee.split('-')[0]}!"
        user = User(username=username, role='student', student_id=student.id)
        user.set_password(password)
        db.session.add(user)
        db.session.commit()
        
        log_action('ADD_STUDENT', f"Étudiant ajouté: {student.nom_complet} ({student.student_code})")
        flash(f'Étudiant ajouté. Login: {username} / MDP: {password}', 'success')
        return redirect(url_for('admin.modifier_etudiant', student_id=student.id))
    
    return render_template('admin/form_etudiant.html', student=None, annee_courante=get_annee_courante())


@admin_bp.route('/etudiants/<int:student_id>/modifier', methods=['GET', 'POST'])
@login_required
@admin_required
def modifier_etudiant(student_id):
    student = Student.query.get_or_404(student_id)
    
    if request.method == 'POST':
        student.nom = request.form.get('nom', '').strip().upper()
        student.prenom = request.form.get('prenom', '').strip().title()
        student.nationalite = request.form.get('nationalite', '').strip()
        student.email = request.form.get('email', '').strip().lower()
        student.telephone = request.form.get('telephone', '').strip()
        student.annee_inscription = request.form.get('annee_inscription', student.annee_inscription)
        student.bio = request.form.get('bio', '').strip()
        
        dob = request.form.get('date_naissance')
        if dob:
            from datetime import date
            try:
                student.date_naissance = date.fromisoformat(dob)
            except:
                pass
        
        if 'photo' in request.files and request.files['photo'].filename:
            student.photo = save_photo(request.files['photo'], subfolder='students')
        
        # Update user credentials if provided
        user = student.user
        if user:
            new_username = request.form.get('username', '').strip()
            new_password = request.form.get('password', '').strip()
            if new_username and new_username != user.username:
                if not User.query.filter_by(username=new_username).first():
                    user.username = new_username
            if new_password and len(new_password) >= 6:
                user.set_password(new_password)
        
        db.session.commit()
        log_action('EDIT_STUDENT', f"Étudiant modifié: {student.nom_complet}")
        flash('Étudiant mis à jour.', 'success')
        return redirect(url_for('admin.modifier_etudiant', student_id=student.id))
    
    return render_template('admin/form_etudiant.html', student=student, annee_courante=get_annee_courante())


@admin_bp.route('/etudiants/<int:student_id>/supprimer', methods=['POST'])
@login_required
@admin_required
def supprimer_etudiant(student_id):
    student = Student.query.get_or_404(student_id)
    nom = student.nom_complet
    if student.user:
        db.session.delete(student.user)
    for b in student.bureau_roles:
        db.session.delete(b)
    db.session.delete(student)
    db.session.commit()
    log_action('DELETE_STUDENT', f"Étudiant supprimé: {nom}")
    flash(f'Étudiant {nom} supprimé.', 'success')
    return redirect(url_for('admin.liste_etudiants'))


# ─── Import CSV ───────────────────────────────────────────────────────────────

@admin_bp.route('/importer-csv', methods=['GET', 'POST'])
@login_required
@admin_required
def importer_csv():
    results = []
    if request.method == 'POST':
        file = request.files.get('fichier_csv')
        annee = request.form.get('annee_inscription', get_annee_courante())
        
        if not file or not file.filename.endswith('.csv'):
            flash('Veuillez uploader un fichier CSV.', 'danger')
            return redirect(url_for('admin.importer_csv'))
        
        content = file.read().decode('utf-8-sig')
        reader = csv.DictReader(io.StringIO(content))
        
        for row in reader:
            try:
                nom = row.get('nom', '').strip().upper()
                prenom = row.get('prenom', '').strip().title()
                email = row.get('email', '').strip().lower()
                
                if not nom or not prenom:
                    results.append({'status': 'error', 'msg': f"Ligne ignorée: nom/prénom manquant"})
                    continue
                
                if email and Student.query.filter_by(email=email).first():
                    results.append({'status': 'warning', 'msg': f"{prenom} {nom}: email déjà existant"})
                    continue
                
                annee_row = row.get('annee_inscription', annee).strip() or annee
                student = Student(
                    student_code=generate_student_code(annee_row),
                    nom=nom, prenom=prenom,
                    email=email or None,
                    nationalite=row.get('nationalite', '').strip(),
                    telephone=row.get('telephone', '').strip(),
                    annee_inscription=annee_row
                )
                db.session.add(student)
                db.session.flush()
                
                username = generate_username(prenom, nom, annee_row)
                base = username
                c = 1
                while User.query.filter_by(username=username).first():
                    username = f"{base}{c}"; c += 1
                
                password = row.get('password') or f"StatDiv@{annee_row.split('-')[0]}!"
                user = User(username=username, role='student', student_id=student.id)
                user.set_password(password)
                db.session.add(user)
                results.append({'status': 'success', 'msg': f"{prenom} {nom} — {username} / {password}"})
            except Exception as e:
                results.append({'status': 'error', 'msg': f"Erreur: {str(e)}"})
        
        db.session.commit()
        log_action('IMPORT_CSV', f"{len(results)} lignes traitées")
        
    return render_template('admin/import_csv.html', results=results, annee_courante=get_annee_courante())


# ─── Bureau ───────────────────────────────────────────────────────────────────

@admin_bp.route('/bureau')
@login_required
@admin_required
def gerer_bureau():
    annee = request.args.get('annee', get_annee_courante())
    bureau = Bureau.query.filter_by(annee_academique=annee).order_by(Bureau.ordre).all()
    etudiants = Student.query.order_by(Student.nom).all()
    annees = db.session.query(Bureau.annee_academique).distinct().all()
    return render_template('admin/bureau.html', bureau=bureau, etudiants=etudiants,
                           annee=annee, annees=[a[0] for a in annees])


@admin_bp.route('/bureau/ajouter', methods=['POST'])
@login_required
@admin_required
def ajouter_bureau():
    annee = request.form.get('annee_academique', get_annee_courante())
    role = request.form.get('role', '').strip()
    student_id = request.form.get('student_id')
    ordre = request.form.get('ordre', 0)
    
    if not role or not student_id:
        flash('Rôle et étudiant requis.', 'danger')
        return redirect(url_for('admin.gerer_bureau', annee=annee))
    
    member = Bureau(annee_academique=annee, role=role, 
                    student_id=int(student_id), ordre=int(ordre))
    db.session.add(member)
    db.session.commit()
    log_action('ADD_BUREAU', f"Bureau {annee}: {role}")
    flash('Membre du bureau ajouté.', 'success')
    return redirect(url_for('admin.gerer_bureau', annee=annee))


@admin_bp.route('/bureau/<int:bureau_id>/supprimer', methods=['POST'])
@login_required
@admin_required
def supprimer_bureau(bureau_id):
    member = Bureau.query.get_or_404(bureau_id)
    annee = member.annee_academique
    db.session.delete(member)
    db.session.commit()
    log_action('DELETE_BUREAU', f"Membre bureau supprimé ID:{bureau_id}")
    flash('Membre supprimé du bureau.', 'success')
    return redirect(url_for('admin.gerer_bureau', annee=annee))


# ─── Logs ─────────────────────────────────────────────────────────────────────

@admin_bp.route('/logs')
@login_required
@admin_required
def logs():
    page = request.args.get('page', 1, type=int)
    logs_page = ActionLog.query.order_by(ActionLog.timestamp.desc()).paginate(page=page, per_page=50)
    return render_template('admin/logs.html', logs=logs_page)
