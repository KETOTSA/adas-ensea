import os
from flask import Flask
from flask_login import LoginManager
from models import db, User
from datetime import datetime

def create_app():
    app = Flask(__name__)

    app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'statdiv-secret-key-change-in-production')
    app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get(
        'DATABASE_URL',
        f"sqlite:////tmp/statdiv.db"
    )
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    app.config['MAX_CONTENT_LENGTH'] = 32 * 1024 * 1024
    app.config['UPLOAD_FOLDER'] = os.path.join(os.path.dirname(__file__), 'static', 'uploads')
    app.config['ALLOWED_EXTENSIONS'] = {'png', 'jpg', 'jpeg', 'gif', 'webp'}

    db.init_app(app)

    login_manager = LoginManager()
    login_manager.init_app(app)
    login_manager.login_view = 'auth.login'
    login_manager.login_message = 'Veuillez vous connecter pour accéder à cette page.'
    login_manager.login_message_category = 'warning'

    @login_manager.user_loader
    def load_user(user_id):
        return User.query.get(int(user_id))

    @app.context_processor
    def inject_globals():
        from models import Message
        now = datetime.utcnow()
        annee_courante = f"{now.year}-{now.year+1}" if now.month >= 9 else f"{now.year-1}-{now.year}"
        non_lus = 0
        try:
            from flask_login import current_user
            if current_user.is_authenticated:
                non_lus = Message.query.filter_by(destinataire_id=current_user.id, lu=False).count()
        except:
            pass
        return dict(annee_courante=annee_courante, now=now, messages_non_lus=non_lus)

    from routes.auth import auth_bp
    from routes.student import student_bp
    from routes.admin import admin_bp
    from routes.bureau import bureau_bp
    from routes.main import main_bp
    from routes.extra import extra_bp
    from routes.carnet import carnet_bp

    app.register_blueprint(main_bp)
    app.register_blueprint(auth_bp, url_prefix='/auth')
    app.register_blueprint(student_bp, url_prefix='/etudiant')
    app.register_blueprint(admin_bp, url_prefix='/admin')
    app.register_blueprint(bureau_bp, url_prefix='/bureau')
    app.register_blueprint(extra_bp, url_prefix='/adas')
    app.register_blueprint(carnet_bp, url_prefix='/carnet')

    with app.app_context():
        db.create_all()
        _seed_admin()

    return app


def _seed_admin():
    from models import User
    if not User.query.filter_by(role='admin').first():
        admin = User(username='admin', role='admin')
        admin.set_password('Admin@StatDiv2024!')
        db.session.add(admin)
        db.session.commit()
        print(" Admin créé — username: admin / password: Admin@StatDiv2024!")


app = create_app()

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
