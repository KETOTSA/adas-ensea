from flask import Blueprint, render_template, redirect, url_for, flash, request, jsonify
from flask_login import login_required, current_user
from models import db, CarnetNote
from datetime import datetime

carnet_bp = Blueprint('carnet', __name__)

COULEURS = [
    '#003580', '#1a5fa8', '#c9973a', '#166534',
    '#991b1b', '#6b21a8', '#0f766e', '#b45309'
]


def get_student():
    if not current_user.is_authenticated or not current_user.student:
        return None
    return current_user.student


@carnet_bp.route('/')
@login_required
def index():
    student = get_student()
    if not student:
        flash('Profil étudiant requis.', 'warning')
        return redirect(url_for('extra.accueil'))

    q = request.args.get('q', '').strip()
    categorie = request.args.get('categorie', '')

    query = CarnetNote.query.filter_by(student_id=student.id)
    if q:
        query = query.filter(
            CarnetNote.titre.ilike(f'%{q}%') |
            CarnetNote.contenu.ilike(f'%{q}%')
        )
    if categorie:
        query = query.filter_by(categorie=categorie)

    # Épinglées d'abord, puis par date
    notes = query.order_by(CarnetNote.epingle.desc(), CarnetNote.updated_at.desc()).all()

    # Catégories disponibles
    cats_raw = db.session.query(CarnetNote.categorie).filter_by(student_id=student.id).distinct().all()
    categories = [c[0] for c in cats_raw if c[0]]

    return render_template('carnet/index.html',
                           notes=notes, categories=categories,
                           q=q, categorie=categorie,
                           couleurs=COULEURS)


@carnet_bp.route('/ajouter', methods=['POST'])
@login_required
def ajouter():
    student = get_student()
    if not student:
        flash('Profil introuvable.', 'danger')
        return redirect(url_for('carnet.index'))

    titre = request.form.get('titre', '').strip()
    contenu = request.form.get('contenu', '').strip()
    categorie = request.form.get('categorie', 'Général').strip() or 'Général'
    couleur = request.form.get('couleur', '#003580')

    if not titre or not contenu:
        flash('Titre et contenu requis.', 'danger')
        return redirect(url_for('carnet.index'))

    note = CarnetNote(
        student_id=student.id,
        titre=titre,
        contenu=contenu,
        categorie=categorie,
        couleur=couleur
    )
    db.session.add(note)
    db.session.commit()
    flash('Note ajoutée au carnet.', 'success')
    return redirect(url_for('carnet.index'))


@carnet_bp.route('/<int:note_id>/modifier', methods=['GET', 'POST'])
@login_required
def modifier(note_id):
    student = get_student()
    note = CarnetNote.query.get_or_404(note_id)

    if not student or note.student_id != student.id:
        flash('Accès non autorisé.', 'danger')
        return redirect(url_for('carnet.index'))

    if request.method == 'POST':
        note.titre = request.form.get('titre', '').strip()
        note.contenu = request.form.get('contenu', '').strip()
        note.categorie = request.form.get('categorie', 'Général').strip() or 'Général'
        note.couleur = request.form.get('couleur', note.couleur)
        note.updated_at = datetime.utcnow()
        db.session.commit()
        flash('Note mise à jour.', 'success')
        return redirect(url_for('carnet.index'))

    return render_template('carnet/modifier.html', note=note, couleurs=COULEURS)


@carnet_bp.route('/<int:note_id>/epingler', methods=['POST'])
@login_required
def epingler(note_id):
    student = get_student()
    note = CarnetNote.query.get_or_404(note_id)
    if student and note.student_id == student.id:
        note.epingle = not note.epingle
        db.session.commit()
    return redirect(url_for('carnet.index'))


@carnet_bp.route('/<int:note_id>/supprimer', methods=['POST'])
@login_required
def supprimer(note_id):
    student = get_student()
    note = CarnetNote.query.get_or_404(note_id)
    if student and note.student_id == student.id:
        db.session.delete(note)
        db.session.commit()
        flash('Note supprimée.', 'success')
    return redirect(url_for('carnet.index'))
