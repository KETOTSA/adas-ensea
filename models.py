from datetime import datetime
from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
import json

db = SQLAlchemy()


class Annonce(db.Model):
    __tablename__ = 'annonces'
    id = db.Column(db.Integer, primary_key=True)
    titre = db.Column(db.String(200), nullable=False)
    contenu = db.Column(db.Text, nullable=False)
    auteur_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    date_publication = db.Column(db.DateTime, default=datetime.utcnow)
    importante = db.Column(db.Boolean, default=False)
    active = db.Column(db.Boolean, default=True)
    auteur = db.relationship('User')


class Evenement(db.Model):
    __tablename__ = 'evenements'
    id = db.Column(db.Integer, primary_key=True)
    titre = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text)
    date_debut = db.Column(db.DateTime, nullable=False)
    date_fin = db.Column(db.DateTime)
    lieu = db.Column(db.String(200))
    type_event = db.Column(db.String(50), default='general')
    auteur_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    auteur = db.relationship('User')


class Document(db.Model):
    __tablename__ = 'documents'
    id = db.Column(db.Integer, primary_key=True)
    titre = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text)
    fichier = db.Column(db.String(500), nullable=False)
    categorie = db.Column(db.String(100), default='general')
    public = db.Column(db.Boolean, default=True)
    auteur_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    telechargements = db.Column(db.Integer, default=0)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    auteur = db.relationship('User')


class GaleriePhoto(db.Model):
    __tablename__ = 'galerie_photos'
    id = db.Column(db.Integer, primary_key=True)
    titre = db.Column(db.String(200))
    description = db.Column(db.Text)
    fichier = db.Column(db.String(500), nullable=False)
    annee_academique = db.Column(db.String(20))
    auteur_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    auteur = db.relationship('User')


class Message(db.Model):
    __tablename__ = 'messages'
    id = db.Column(db.Integer, primary_key=True)
    expediteur_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    destinataire_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    sujet = db.Column(db.String(200))
    contenu = db.Column(db.Text, nullable=False)
    public = db.Column(db.Boolean, default=False)
    lu = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    expediteur = db.relationship('User', foreign_keys=[expediteur_id])
    destinataire = db.relationship('User', foreign_keys=[destinataire_id])


class Note(db.Model):
    __tablename__ = 'notes'
    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey('students.id'), nullable=False)
    matiere = db.Column(db.String(200), nullable=False)
    note = db.Column(db.Float, nullable=False)
    note_max = db.Column(db.Float, default=20.0)
    semestre = db.Column(db.String(50))
    annee_academique = db.Column(db.String(20))
    commentaire = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    student = db.relationship('Student', back_populates='notes')


class User(UserMixin, db.Model):
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(100), unique=True, nullable=False)
    password_hash = db.Column(db.String(256), nullable=False)
    role = db.Column(db.String(20), default='student')  # 'student' or 'admin'
    student_id = db.Column(db.Integer, db.ForeignKey('students.id'), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    is_active = db.Column(db.Boolean, default=True)
    
    student = db.relationship('Student', back_populates='user', uselist=False)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def is_admin(self):
        return self.role == 'admin'


class Student(db.Model):
    __tablename__ = 'students'
    
    id = db.Column(db.Integer, primary_key=True)
    student_code = db.Column(db.String(50), unique=True, nullable=False)  # e.g. ADAS-2023-001
    nom = db.Column(db.String(100), nullable=False)
    prenom = db.Column(db.String(100), nullable=False)
    nationalite = db.Column(db.String(100))
    photo = db.Column(db.String(500))  # file path
    date_naissance = db.Column(db.Date)
    email = db.Column(db.String(200), unique=True)
    telephone = db.Column(db.String(30))
    annee_inscription = db.Column(db.String(20))  # e.g. "2023-2024"
    parcours = db.Column(db.Text)  # JSON array of parcours steps
    projets = db.Column(db.Text)  # JSON array of projects
    bio = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    user = db.relationship('User', back_populates='student', uselist=False)
    bureau_roles = db.relationship("Bureau", back_populates="student")
    notes = db.relationship("Note", back_populates="student")

    def get_parcours(self):
        try:
            return json.loads(self.parcours) if self.parcours else []
        except:
            return []

    def get_projets(self):
        try:
            return json.loads(self.projets) if self.projets else []
        except:
            return []

    def set_parcours(self, data):
        self.parcours = json.dumps(data, ensure_ascii=False)

    def set_projets(self, data):
        self.projets = json.dumps(data, ensure_ascii=False)

    @property
    def nom_complet(self):
        return f"{self.prenom} {self.nom}"


class Bureau(db.Model):
    __tablename__ = 'bureau'
    
    id = db.Column(db.Integer, primary_key=True)
    annee_academique = db.Column(db.String(20), nullable=False)  # e.g. "2023-2024"
    role = db.Column(db.String(100), nullable=False)  # Président, VP, etc.
    student_id = db.Column(db.Integer, db.ForeignKey('students.id'), nullable=False)
    ordre = db.Column(db.Integer, default=0)  # display order
    actif = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    student = db.relationship('Student', back_populates='bureau_roles')


class ActionLog(db.Model):
    __tablename__ = 'action_logs'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    action = db.Column(db.String(200), nullable=False)
    details = db.Column(db.Text)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    ip_address = db.Column(db.String(50))
    
    user = db.relationship('User')


class CarnetNote(db.Model):
    """Prise de notes personnelles d'un étudiant — carnet privé"""
    __tablename__ = 'carnet_notes'

    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey('students.id'), nullable=False)
    titre = db.Column(db.String(200), nullable=False)
    contenu = db.Column(db.Text, nullable=False)
    categorie = db.Column(db.String(100), default='Général')
    couleur = db.Column(db.String(20), default='#003580')  # couleur de la carte
    epingle = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    student = db.relationship('Student', backref='carnet_notes')
