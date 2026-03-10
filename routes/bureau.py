from flask import Blueprint, render_template, request
from models import Bureau, Student, db
from utils import get_annee_courante

bureau_bp = Blueprint('bureau', __name__)


@bureau_bp.route('/')
@bureau_bp.route('/<annee>')
def index(annee=None):
    annee_courante = get_annee_courante()
    if not annee:
        annee = annee_courante

    bureau = Bureau.query.filter_by(annee_academique=annee, actif=True)\
                         .order_by(Bureau.ordre).all()

    # Toutes les années disponibles, triées du plus récent au plus ancien
    annees_raw = db.session.query(Bureau.annee_academique).distinct()\
                            .order_by(Bureau.annee_academique.desc()).all()
    annees = [a[0] for a in annees_raw]

    # Si l'année en cours n'est pas encore dans la liste, l'ajouter en tête
    if annee_courante not in annees:
        annees.insert(0, annee_courante)

    return render_template('bureau/index.html',
                           bureau=bureau,
                           annee_selectionnee=annee,
                           annees=annees,
                           annee_courante=annee_courante)
