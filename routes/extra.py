import os
from flask import Blueprint, render_template, redirect, url_for, flash, request, send_from_directory, abort
from flask_login import login_required, current_user
from models import db, Annonce, Evenement, Document, GaleriePhoto, Message, Note, User, Student, Bureau
from utils import save_photo, log_action, get_annee_courante
from datetime import datetime

extra_bp = Blueprint('extra', __name__)


def bureau_or_admin_required(f):
    from functools import wraps
    @wraps(f)
    def decorated(*args, **kwargs):
        if not current_user.is_authenticated:
            return redirect(url_for('auth.login'))
        # Admin always ok
        if current_user.is_admin():
            return f(*args, **kwargs)
        # Check if student is in bureau
        if current_user.student:
            annee = get_annee_courante()
            membre = Bureau.query.filter_by(
                student_id=current_user.student.id,
                annee_academique=annee,
                actif=True
            ).first()
            if membre:
                return f(*args, **kwargs)
        flash('Accès réservé aux membres du bureau.', 'danger')
        return redirect(url_for('main.accueil'))
    return decorated


def is_bureau_member():
    if not current_user.is_authenticated:
        return False
    if current_user.is_admin():
        return True
    if current_user.student:
        annee = get_annee_courante()
        return Bureau.query.filter_by(
            student_id=current_user.student.id,
            annee_academique=annee,
            actif=True
        ).first() is not None
    return False


# ─── ACCUEIL PUBLIC ───────────────────────────────────────────────────────────

@extra_bp.route('/accueil')
def accueil():
    annee = get_annee_courante()
    bureau = Bureau.query.filter_by(annee_academique=annee, actif=True).order_by(Bureau.ordre).limit(6).all()
    annonces = Annonce.query.filter_by(active=True).order_by(Annonce.importante.desc(), Annonce.date_publication.desc()).limit(5).all()
    evenements = Evenement.query.filter(Evenement.date_debut >= datetime.utcnow()).order_by(Evenement.date_debut).limit(4).all()
    photos = GaleriePhoto.query.order_by(GaleriePhoto.created_at.desc()).limit(8).all()
    total_etudiants = Student.query.count()
    total_promos = db.session.query(Student.annee_inscription).distinct().count()
    total_projets = db.session.execute(db.text("SELECT COUNT(*) FROM students WHERE projets != '[]' AND projets IS NOT NULL")).scalar()
    return render_template('main/accueil.html',
                           bureau=bureau, annonces=annonces,
                           evenements=evenements, photos=photos,
                           total_etudiants=total_etudiants,
                           total_promos=total_promos,
                           total_projets=total_projets,
                           annee=annee,
                           is_bureau=is_bureau_member())


# ─── ANNONCES ─────────────────────────────────────────────────────────────────

@extra_bp.route('/annonces')
def annonces():
    toutes = Annonce.query.filter_by(active=True).order_by(Annonce.importante.desc(), Annonce.date_publication.desc()).all()
    return render_template('extra/annonces.html', annonces=toutes, is_bureau=is_bureau_member())


@extra_bp.route('/annonces/ajouter', methods=['POST'])
@login_required
@bureau_or_admin_required
def ajouter_annonce():
    titre = request.form.get('titre', '').strip()
    contenu = request.form.get('contenu', '').strip()
    importante = bool(request.form.get('importante'))
    if not titre or not contenu:
        flash('Titre et contenu requis.', 'danger')
        return redirect(url_for('extra.annonces'))
    annonce = Annonce(titre=titre, contenu=contenu, importante=importante, auteur_id=current_user.id)
    db.session.add(annonce)
    db.session.commit()
    log_action('ADD_ANNONCE', f"Annonce: {titre}")
    flash('Annonce publiée.', 'success')
    return redirect(url_for('extra.annonces'))


@extra_bp.route('/annonces/<int:id>/supprimer', methods=['POST'])
@login_required
@bureau_or_admin_required
def supprimer_annonce(id):
    annonce = Annonce.query.get_or_404(id)
    db.session.delete(annonce)
    db.session.commit()
    flash('Annonce supprimée.', 'success')
    return redirect(url_for('extra.annonces'))


# ─── CALENDRIER ───────────────────────────────────────────────────────────────

@extra_bp.route('/calendrier')
def calendrier():
    evenements = Evenement.query.order_by(Evenement.date_debut).all()
    a_venir = [e for e in evenements if e.date_debut >= datetime.utcnow()]
    passes = [e for e in evenements if e.date_debut < datetime.utcnow()]
    return render_template('extra/calendrier.html', a_venir=a_venir, passes=passes, is_bureau=is_bureau_member())


@extra_bp.route('/calendrier/ajouter', methods=['POST'])
@login_required
@bureau_or_admin_required
def ajouter_evenement():
    titre = request.form.get('titre', '').strip()
    description = request.form.get('description', '').strip()
    date_debut_str = request.form.get('date_debut', '')
    lieu = request.form.get('lieu', '').strip()
    type_event = request.form.get('type_event', 'general')
    if not titre or not date_debut_str:
        flash('Titre et date requis.', 'danger')
        return redirect(url_for('extra.calendrier'))
    try:
        date_debut = datetime.fromisoformat(date_debut_str)
    except:
        flash('Format de date invalide.', 'danger')
        return redirect(url_for('extra.calendrier'))
    ev = Evenement(titre=titre, description=description, date_debut=date_debut,
                   lieu=lieu, type_event=type_event, auteur_id=current_user.id)
    db.session.add(ev)
    db.session.commit()
    log_action('ADD_EVENT', f"Événement: {titre}")
    flash('Événement ajouté.', 'success')
    return redirect(url_for('extra.calendrier'))


@extra_bp.route('/calendrier/<int:id>/supprimer', methods=['POST'])
@login_required
@bureau_or_admin_required
def supprimer_evenement(id):
    ev = Evenement.query.get_or_404(id)
    db.session.delete(ev)
    db.session.commit()
    flash('Événement supprimé.', 'success')
    return redirect(url_for('extra.calendrier'))


# ─── DOCUMENTS ────────────────────────────────────────────────────────────────

ALLOWED_DOCS = {'pdf', 'doc', 'docx', 'xls', 'xlsx', 'ppt', 'pptx', 'txt', 'zip', 'png', 'jpg'}

@extra_bp.route('/documents')
def documents():
    categorie = request.args.get('categorie', '')
    query = Document.query.filter_by(public=True)
    if categorie:
        query = query.filter_by(categorie=categorie)
    docs = query.order_by(Document.created_at.desc()).all()
    categories = db.session.query(Document.categorie).distinct().all()
    return render_template('extra/documents.html', documents=docs,
                           categories=[c[0] for c in categories],
                           categorie_active=categorie,
                           is_bureau=is_bureau_member())


@extra_bp.route('/documents/ajouter', methods=['POST'])
@login_required
@bureau_or_admin_required
def ajouter_document():
    titre = request.form.get('titre', '').strip()
    description = request.form.get('description', '').strip()
    categorie = request.form.get('categorie', 'general').strip()
    public = bool(request.form.get('public', True))
    fichier = request.files.get('fichier')
    if not titre or not fichier or not fichier.filename:
        flash('Titre et fichier requis.', 'danger')
        return redirect(url_for('extra.documents'))
    ext = fichier.filename.rsplit('.', 1)[-1].lower() if '.' in fichier.filename else ''
    if ext not in ALLOWED_DOCS:
        flash('Type de fichier non autorisé.', 'danger')
        return redirect(url_for('extra.documents'))
    import uuid
    from flask import current_app
    filename = f"{uuid.uuid4().hex}.{ext}"
    folder = os.path.join(current_app.config['UPLOAD_FOLDER'], 'documents')
    os.makedirs(folder, exist_ok=True)
    fichier.save(os.path.join(folder, filename))
    doc = Document(titre=titre, description=description, categorie=categorie,
                   fichier=f"uploads/documents/{filename}", public=public,
                   auteur_id=current_user.id)
    db.session.add(doc)
    db.session.commit()
    log_action('ADD_DOCUMENT', f"Document: {titre}")
    flash('Document ajouté.', 'success')
    return redirect(url_for('extra.documents'))


@extra_bp.route('/documents/<int:id>/telecharger')
def telecharger_document(id):
    doc = Document.query.get_or_404(id)
    if not doc.public and not (current_user.is_authenticated):
        abort(403)
    doc.telechargements += 1
    db.session.commit()
    from flask import current_app
    folder = os.path.join(current_app.static_folder, os.path.dirname(doc.fichier.replace('uploads/', 'uploads/')))
    filename = os.path.basename(doc.fichier)
    return send_from_directory(os.path.join(current_app.static_folder, 'uploads', 'documents'), filename, as_attachment=True)


@extra_bp.route('/documents/<int:id>/supprimer', methods=['POST'])
@login_required
@bureau_or_admin_required
def supprimer_document(id):
    doc = Document.query.get_or_404(id)
    db.session.delete(doc)
    db.session.commit()
    flash('Document supprimé.', 'success')
    return redirect(url_for('extra.documents'))


# ─── GALERIE ──────────────────────────────────────────────────────────────────

@extra_bp.route('/galerie')
def galerie():
    annee = request.args.get('annee', '')
    query = GaleriePhoto.query
    if annee:
        query = query.filter_by(annee_academique=annee)
    photos = query.order_by(GaleriePhoto.created_at.desc()).all()
    annees = db.session.query(GaleriePhoto.annee_academique).distinct().all()
    return render_template('extra/galerie.html', photos=photos,
                           annees=[a[0] for a in annees if a[0]],
                           annee_active=annee,
                           is_bureau=is_bureau_member())


@extra_bp.route('/galerie/ajouter', methods=['POST'])
@login_required
@bureau_or_admin_required
def ajouter_photo():
    titre = request.form.get('titre', '').strip()
    description = request.form.get('description', '').strip()
    annee = request.form.get('annee_academique', get_annee_courante())
    fichier = request.files.get('photo')
    if not fichier or not fichier.filename:
        flash('Photo requise.', 'danger')
        return redirect(url_for('extra.galerie'))
    chemin = save_photo(fichier, subfolder='galerie', max_size=(1200, 1200))
    if not chemin:
        flash('Format non supporté.', 'danger')
        return redirect(url_for('extra.galerie'))
    photo = GaleriePhoto(titre=titre, description=description,
                         fichier=chemin, annee_academique=annee,
                         auteur_id=current_user.id)
    db.session.add(photo)
    db.session.commit()
    flash('Photo ajoutée à la galerie.', 'success')
    return redirect(url_for('extra.galerie'))


@extra_bp.route('/galerie/<int:id>/supprimer', methods=['POST'])
@login_required
@bureau_or_admin_required
def supprimer_photo_galerie(id):
    photo = GaleriePhoto.query.get_or_404(id)
    db.session.delete(photo)
    db.session.commit()
    flash('Photo supprimée.', 'success')
    return redirect(url_for('extra.galerie'))


# ─── MESSAGERIE ───────────────────────────────────────────────────────────────

@extra_bp.route('/messages')
@login_required
def messages():
    # Messages publics du bureau
    publics = Message.query.filter_by(public=True).order_by(Message.created_at.desc()).limit(20).all()
    # Messages privés reçus
    prives = Message.query.filter_by(destinataire_id=current_user.id, public=False)\
                          .order_by(Message.created_at.desc()).all()
    # Envoyer à
    if current_user.is_admin():
        destinataires = User.query.filter_by(is_active=True).all()
    else:
        # Students can message bureau members and admin
        destinataires = User.query.filter(
            (User.role == 'admin') | 
            (User.student_id.in_(
                db.session.query(Bureau.student_id).filter_by(
                    annee_academique=get_annee_courante(), actif=True
                )
            ))
        ).all()
    non_lus = Message.query.filter_by(destinataire_id=current_user.id, lu=False).count()
    return render_template('extra/messages.html', publics=publics, prives=prives,
                           destinataires=destinataires, non_lus=non_lus,
                           is_bureau=is_bureau_member())


@extra_bp.route('/messages/envoyer', methods=['POST'])
@login_required
def envoyer_message():
    sujet = request.form.get('sujet', '').strip()
    contenu = request.form.get('contenu', '').strip()
    public = bool(request.form.get('public'))
    destinataire_id = request.form.get('destinataire_id')
    if not contenu:
        flash('Le message ne peut pas être vide.', 'danger')
        return redirect(url_for('extra.messages'))
    # Only bureau/admin can post public messages
    if public and not is_bureau_member():
        public = False
    msg = Message(expediteur_id=current_user.id,
                  destinataire_id=int(destinataire_id) if destinataire_id and not public else None,
                  sujet=sujet, contenu=contenu, public=public)
    db.session.add(msg)
    db.session.commit()
    flash('Message envoyé.', 'success')
    return redirect(url_for('extra.messages'))


@extra_bp.route('/messages/<int:id>/lire', methods=['POST'])
@login_required
def marquer_lu(id):
    msg = Message.query.get_or_404(id)
    if msg.destinataire_id == current_user.id:
        msg.lu = True
        db.session.commit()
    return redirect(url_for('extra.messages'))


# ─── NOTES ────────────────────────────────────────────────────────────────────

@extra_bp.route('/notes')
@login_required
def mes_notes():
    if current_user.is_admin():
        return redirect(url_for('extra.notes_admin'))
    student = current_user.student
    if not student:
        flash('Profil introuvable.', 'danger')
        return redirect(url_for('main.accueil'))
    notes = Note.query.filter_by(student_id=student.id).order_by(Note.annee_academique, Note.semestre).all()
    # Group by année/semestre
    groupes = {}
    for n in notes:
        key = f"{n.annee_academique} — {n.semestre or 'Général'}"
        groupes.setdefault(key, []).append(n)
    moyennes = {}
    for key, ns in groupes.items():
        moyennes[key] = sum(n.note for n in ns) / len(ns)
    return render_template('extra/notes.html', notes=notes, groupes=groupes, moyennes=moyennes)


@extra_bp.route('/notes/admin')
@login_required
def notes_admin():
    if not current_user.is_admin():
        abort(403)
    etudiants = Student.query.order_by(Student.nom).all()
    return render_template('extra/notes_admin.html', etudiants=etudiants)


@extra_bp.route('/notes/ajouter', methods=['POST'])
@login_required
def ajouter_note():
    if not current_user.is_admin():
        abort(403)
    student_id = request.form.get('student_id')
    matiere = request.form.get('matiere', '').strip()
    note_val = request.form.get('note')
    note_max = request.form.get('note_max', 20)
    semestre = request.form.get('semestre', '').strip()
    annee = request.form.get('annee_academique', get_annee_courante())
    commentaire = request.form.get('commentaire', '').strip()
    if not student_id or not matiere or note_val is None:
        flash('Étudiant, matière et note requis.', 'danger')
        return redirect(url_for('extra.notes_admin'))
    try:
        note_val = float(note_val)
        note_max = float(note_max)
    except:
        flash('Note invalide.', 'danger')
        return redirect(url_for('extra.notes_admin'))
    note = Note(student_id=int(student_id), matiere=matiere, note=note_val,
                note_max=note_max, semestre=semestre, annee_academique=annee,
                commentaire=commentaire)
    db.session.add(note)
    db.session.commit()
    log_action('ADD_NOTE', f"Note ajoutée: {matiere} pour étudiant {student_id}")
    flash('Note ajoutée.', 'success')
    return redirect(url_for('extra.notes_admin'))


@extra_bp.route('/notes/<int:id>/supprimer', methods=['POST'])
@login_required
def supprimer_note(id):
    if not current_user.is_admin():
        abort(403)
    note = Note.query.get_or_404(id)
    db.session.delete(note)
    db.session.commit()
    flash('Note supprimée.', 'success')
    return redirect(url_for('extra.notes_admin'))
