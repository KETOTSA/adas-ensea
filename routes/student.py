import json
from flask import Blueprint, render_template, redirect, url_for, flash, request, current_app
from flask_login import login_required, current_user
from models import db, Student
from utils import save_photo, log_action

student_bp = Blueprint('student', __name__)


def student_required(f):
    from functools import wraps
    @wraps(f)
    def decorated(*args, **kwargs):
        if not current_user.is_authenticated:
            return redirect(url_for('auth.login'))
        if current_user.role not in ('student', 'admin'):
            flash('Accès non autorisé.', 'danger')
            return redirect(url_for('main.index'))
        return f(*args, **kwargs)
    return decorated


@student_bp.route('/profil')
@login_required
@student_required
def profil():
    if current_user.is_admin():
        return redirect(url_for('admin.dashboard'))
    student = current_user.student
    if not student:
        flash('Profil étudiant introuvable.', 'warning')
        return redirect(url_for('auth.login'))
    return render_template('student/profil.html', student=student,
                           parcours=student.get_parcours(),
                           projets=student.get_projets())


@student_bp.route('/ajouter-parcours', methods=['POST'])
@login_required
@student_required
def ajouter_parcours():
    student = current_user.student
    if not student:
        flash('Profil introuvable.', 'danger')
        return redirect(url_for('student.profil'))
    
    etape = request.form.get('etape', '').strip()
    description = request.form.get('description', '').strip()
    periode = request.form.get('periode', '').strip()
    
    if not etape:
        flash('Le titre de l\'étape est requis.', 'danger')
        return redirect(url_for('student.profil'))
    
    parcours = student.get_parcours()
    parcours.append({'etape': etape, 'description': description, 'periode': periode})
    student.set_parcours(parcours)
    db.session.commit()
    log_action('ADD_PARCOURS', f"Étape ajoutée: {etape}")
    flash('Étape du parcours ajoutée.', 'success')
    return redirect(url_for('student.profil'))


@student_bp.route('/supprimer-parcours/<int:index>', methods=['POST'])
@login_required
@student_required
def supprimer_parcours(index):
    student = current_user.student
    parcours = student.get_parcours()
    if 0 <= index < len(parcours):
        removed = parcours.pop(index)
        student.set_parcours(parcours)
        db.session.commit()
        log_action('DELETE_PARCOURS', f"Étape supprimée: {removed.get('etape')}")
        flash('Étape supprimée.', 'success')
    return redirect(url_for('student.profil'))


@student_bp.route('/ajouter-projet', methods=['POST'])
@login_required
@student_required
def ajouter_projet():
    student = current_user.student
    if not student:
        flash('Profil introuvable.', 'danger')
        return redirect(url_for('student.profil'))
    
    nom = request.form.get('nom_projet', '').strip()
    description = request.form.get('description_projet', '').strip()
    date = request.form.get('date_projet', '').strip()
    lien = request.form.get('lien_projet', '').strip()
    
    if not nom:
        flash('Le nom du projet est requis.', 'danger')
        return redirect(url_for('student.profil'))
    
    photo_path = None
    if 'photo_projet' in request.files:
        photo_path = save_photo(request.files['photo_projet'], subfolder='projets')
    
    projets = student.get_projets()
    projets.append({
        'nom': nom,
        'description': description,
        'date': date,
        'lien': lien,
        'photo': photo_path
    })
    student.set_projets(projets)
    db.session.commit()
    log_action('ADD_PROJET', f"Projet ajouté: {nom}")
    flash('Projet ajouté avec succès.', 'success')
    return redirect(url_for('student.profil'))


@student_bp.route('/supprimer-projet/<int:index>', methods=['POST'])
@login_required
@student_required
def supprimer_projet(index):
    student = current_user.student
    projets = student.get_projets()
    if 0 <= index < len(projets):
        removed = projets.pop(index)
        student.set_projets(projets)
        db.session.commit()
        log_action('DELETE_PROJET', f"Projet supprimé: {removed.get('nom')}")
        flash('Projet supprimé.', 'success')
    return redirect(url_for('student.profil'))


@student_bp.route('/update-photo', methods=['POST'])
@login_required
@student_required
def update_photo():
    student = current_user.student
    if 'photo' not in request.files:
        flash('Aucun fichier sélectionné.', 'danger')
        return redirect(url_for('student.profil'))
    
    photo_path = save_photo(request.files['photo'], subfolder='students')
    if photo_path:
        student.photo = photo_path
        db.session.commit()
        log_action('UPDATE_PHOTO', 'Photo de profil mise à jour')
        flash('Photo mise à jour.', 'success')
    else:
        flash('Format de fichier non supporté.', 'danger')
    return redirect(url_for('student.profil'))


@student_bp.route('/update-bio', methods=['POST'])
@login_required
@student_required
def update_bio():
    student = current_user.student
    bio = request.form.get('bio', '').strip()
    student.bio = bio[:1000]
    db.session.commit()
    log_action('UPDATE_BIO', 'Bio mise à jour')
    flash('Bio mise à jour.', 'success')
    return redirect(url_for('student.profil'))


@student_bp.route('/public/<int:student_id>')
def profil_public(student_id):
    student = Student.query.get_or_404(student_id)
    return render_template('student/profil_public.html', student=student,
                           parcours=student.get_parcours(),
                           projets=student.get_projets())
