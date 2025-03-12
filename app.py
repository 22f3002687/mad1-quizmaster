from flask import Flask
from models import *
from dotenv import load_dotenv
import os
from controllers import auth_bp, login_manager, admin_bp, user_bp

def create_app():
    app = Flask(__name__)

    load_dotenv()
    app.config['SECRET_KEY'] = os.environ.get('FLASK_SECRET_KEY')
    app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///quiz_master.db"

    db.init_app(app)
    with app.app_context():
        db.create_all()
        admin = Admin.query.filter_by(id=1).first()
        if not admin:
            admin = Admin(username="Adminstartor", email='admin@quizmaster.com')
            admin.set_password('admin@#2468')
            db.session.add(admin)
            db.session.commit()

    app.register_blueprint(auth_bp)
    login_manager.init_app(app)
    app.register_blueprint(admin_bp)
    app.register_blueprint(user_bp)

    
    
    return app

app = create_app()

if __name__ == '__main__':
    app.run(host='0.0.0.0', debug=True)

