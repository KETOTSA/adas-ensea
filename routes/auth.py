from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_user, logout_user, login_required, current_user
from models import User, db
from utils import log_action

auth_bp = Blueprint('auth', __name__)


@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('main.index'))
    
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '')
        remember = request.form.get('remember', False)
        
        user = User.query.filter_by(username=username).first()
        
        if user and user.check_password(password) and user.is_active:
            login_user(user, remember=bool(remember))
            log_action('LOGIN', f"Connexion réussie pour {username}")
            next_page = request.args.get('next')
            if user.is_admin():
                return redirect(next_page or url_for('admin.dashboard'))
            return redirect(next_page or url_for('student.profil'))
        else:
            flash('Identifiant ou mot de passe incorrect.', 'danger')
            log_action('LOGIN_FAIL', f"Tentative échouée pour {username}")
    
    return render_template('auth/login.html')


@auth_bp.route('/logout')
@login_required
def logout():
    log_action('LOGOUT', f"Déconnexion de {current_user.username}")
    logout_user()
    flash('Vous avez été déconnecté.', 'info')
    return redirect(url_for('auth.login'))


@auth_bp.route('/change-password', methods=['GET', 'POST'])
@login_required
def change_password():
    if request.method == 'POST':
        current_pw = request.form.get('current_password')
        new_pw = request.form.get('new_password')
        confirm_pw = request.form.get('confirm_password')
        
        if not current_user.check_password(current_pw):
            flash('Mot de passe actuel incorrect.', 'danger')
        elif new_pw != confirm_pw:
            flash('Les nouveaux mots de passe ne correspondent pas.', 'danger')
        elif len(new_pw) < 8:
            flash('Le mot de passe doit contenir au moins 8 caractères.', 'danger')
        else:
            current_user.set_password(new_pw)
            db.session.commit()
            log_action('CHANGE_PASSWORD', 'Mot de passe modifié')
            flash('Mot de passe modifié avec succès.', 'success')
            return redirect(url_for('student.profil'))
    
    return render_template('auth/change_password.html')
