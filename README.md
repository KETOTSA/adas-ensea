# ADAS — Division des Analystes Statisticiens
### Portail Web & Mobile (PWA) — Flask + SQLite

Application web progressive (PWA) de gestion de la division d'analystes statisticiens d'une école. Accessible sur ordinateur, iOS et Android via navigateur.

---

## 🚀 Installation rapide

### 1. Prérequis
- Python 3.9+
- pip

### 2. Cloner / dézipper le projet

```bash
cd statdiv
```

### 3. Créer un environnement virtuel (recommandé)

```bash
python -m venv venv

# Windows
venv\Scripts\activate

# macOS/Linux
source venv/bin/activate
```

### 4. Installer les dépendances

```bash
pip install -r requirements.txt
```

### 5. Configuration (optionnel)

```bash
cp .env.example .env
# Éditez .env pour personnaliser SECRET_KEY etc.
```

### 6. Initialiser (icônes + BDD)

```bash
python setup.py
```

### 7. Lancer l'application

```bash
python app.py
```

Ouvrez http://localhost:5000 dans votre navigateur.

---

## 🔐 Connexion initiale

| Rôle  | Username | Mot de passe         |
|-------|----------|----------------------|
| Admin | `admin`  | `Admin@StatDiv2024!` |

> **⚠️ Changez le mot de passe admin immédiatement après la première connexion !**

---

## 📁 Structure du projet

```
statdiv/
├── app.py                  # Point d'entrée Flask
├── models.py               # Modèles SQLAlchemy (User, Student, Bureau, ActionLog)
├── utils.py                # Fonctions utilitaires (upload, logs, génération codes)
├── setup.py                # Script d'initialisation
├── requirements.txt
├── exemple_import.csv      # Exemple pour import CSV
├── .env.example
│
├── routes/
│   ├── auth.py             # Authentification (login, logout, change password)
│   ├── main.py             # Page principale
│   ├── student.py          # Profil étudiant (parcours, projets, photo)
│   ├── admin.py            # Administration (CRUD étudiants, bureau, CSV, logs)
│   └── bureau.py           # Page publique du bureau
│
├── templates/
│   ├── base.html           # Template de base (navbar, flash, footer)
│   ├── auth/               # login.html, change_password.html
│   ├── student/            # profil.html, profil_public.html
│   ├── admin/              # dashboard, étudiants, bureau, CSV, logs
│   └── bureau/             # index.html
│
├── static/
│   ├── css/main.css        # CSS complet (responsive, mobile-first)
│   ├── js/app.js           # JavaScript (tabs, modals, PWA install)
│   ├── js/sw.js            # Service Worker (PWA offline)
│   ├── manifest.json       # Manifest PWA
│   ├── images/             # Icônes PWA (icon-192.png, icon-512.png)
│   └── uploads/            # Photos uploadées (auto-créé)
│
└── instance/
    └── statdiv.db          # Base SQLite (auto-créée)
```

---

## 🎓 Fonctionnalités

### Pour les étudiants
- **Connexion** avec identifiant et mot de passe personnels
- **Profil complet** : photo, infos, bio, nationalité, contact
- **Parcours académique** : timeline interactive, ajout/suppression d'étapes
- **Projets** : fiches projets avec photo, description, lien, date
- **Changement de mot de passe**

### Pour les administrateurs
- **Dashboard** avec statistiques et activité récente
- **CRUD complet** des étudiants (ajouter, modifier, supprimer)
- **Génération automatique** des codes étudiants (ADAS-2024-001) et usernames
- **Import CSV** en masse avec rapport d'erreurs
- **Gestion du bureau** par année académique (rôles, ordre d'affichage)
- **Logs d'activité** paginés

### Bureau
- Affichage public par année académique
- Sélecteur d'années
- Cartes membres avec photo, rôle, lien vers profil

### PWA (Progressive Web App)
- Installable sur iOS (Safari → Partager → Sur l'écran d'accueil)
- Installable sur Android (Chrome → Installer l'application)
- Service Worker pour cache offline
- Manifest avec icônes

---

## 📊 Base de données

### Tables

**users** : id, username, password_hash, role, student_id, created_at, is_active

**students** : id, student_code, nom, prenom, nationalite, photo, date_naissance, email, telephone, annee_inscription, parcours (JSON), projets (JSON), bio

**bureau** : id, annee_academique, role, student_id, ordre, actif

**action_logs** : id, user_id, action, details, timestamp, ip_address

---

## 🔒 Sécurité

- Mots de passe hashés avec **Werkzeug** (PBKDF2-SHA256)
- Protection **CSRF** via Flask sessions
- **SQLAlchemy ORM** → pas d'injection SQL possible
- Validation des types de fichiers uploadés
- Redimensionnement automatique des images (Pillow)
- Journalisation de toutes les actions admin
- Rôles : `admin` vs `student` avec décorateurs de protection

---

## 🌍 Déploiement en production

### Heroku
```bash
# Créer Procfile
echo "web: gunicorn app:app" > Procfile

heroku create adas-division
heroku config:set SECRET_KEY=$(python -c "import secrets; print(secrets.token_hex(32))")
git push heroku main
```

### VPS (Ubuntu + Nginx + Gunicorn)
```bash
# Gunicorn
gunicorn --workers 4 --bind 127.0.0.1:5000 app:app

# Nginx config (simplifiée)
# proxy_pass http://127.0.0.1:5000;
```

### Variables d'environnement en production
```
SECRET_KEY=cle-longue-et-aleatoire-xxxx
DATABASE_URL=sqlite:///instance/statdiv.db  # ou PostgreSQL
FLASK_ENV=production
FLASK_DEBUG=0
```

---

## 📱 Installer comme app mobile

### iOS (iPhone/iPad)
1. Ouvrez Safari → naviguez vers l'URL
2. Appuyez sur le bouton **Partager** ↑
3. Sélectionnez **Sur l'écran d'accueil**
4. Confirmez

### Android
1. Ouvrez Chrome → naviguez vers l'URL
2. Menu ⋮ → **Installer l'application**
3. Ou attendez la bannière automatique

---

## 📋 Import CSV — Format

```csv
nom,prenom,email,nationalite,telephone,annee_inscription,password
DUPONT,Jean,j.dupont@ecole.fr,Française,+33612345678,2024-2025,
KONÉ,Aminata,a.kone@ecole.fr,Ivoirienne,,2024-2025,
```

Colonnes obligatoires : `nom`, `prenom`  
Si `password` est vide : généré automatiquement  
Si `annee_inscription` est vide : année courante

---

## ⚙️ Personnalisation

Modifiez `static/css/main.css` pour changer :
- Couleurs via les variables CSS (`:root { --navy: ... }`)
- Polices (Google Fonts)
- Mise en page

Modifiez `app.py` → `_seed_admin()` pour changer les credentials admin par défaut.

---

## 🐛 Dépannage

**Erreur "No module named flask"** → `pip install -r requirements.txt`

**Photos ne s'affichent pas** → Vérifiez les permissions du dossier `static/uploads/`

**Service Worker ne se charge pas** → Nécessite HTTPS en production (fonctionne sur localhost)

**Import CSV avec accents** → Sauvegardez en UTF-8 sans BOM
