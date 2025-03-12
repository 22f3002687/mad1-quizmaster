from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from models import db, User, Admin
from .forms import UserRegistrationForm, UserLoginForm, AdminLoginForm
from flask import Blueprint, render_template, redirect, url_for, flash, request



login_manager = LoginManager()

@login_manager.user_loader
def load_user(user_identifier):
    if user_identifier.startswith("admin-"):
        admin_id = int(user_identifier.split("-")[1])
        return Admin.query.get(admin_id)
    elif user_identifier.startswith("user-"):
        user_id = int(user_identifier.split("-")[1])
        return User.query.get(user_id)
    return None


auth_bp = Blueprint('auth', __name__)

@auth_bp.route('/', methods=['GET'])
@auth_bp.route('/home', methods=['GET'])
def home():
    if current_user.is_authenticated:
        user_identifier = current_user.get_id()  
        if user_identifier.startswith("admin-"):
            return redirect(url_for('admin.dashboard'))
        else:
            return redirect(url_for('user.dashboard'))
    return render_template('home.html')


@auth_bp.route('/admin/login', methods=['GET', 'POST'])
def admin_login():
    if current_user.is_authenticated:
        user_identifier = current_user.get_id()  
        if user_identifier.startswith("admin-"):
            return redirect(url_for('admin.dashboard'))
        else:
            return redirect(url_for('user.dashboard'))
    
    form = AdminLoginForm()

    if form.validate_on_submit():
        admin = Admin.query.filter_by(email=form.email.data).first()
        if admin and admin.check_password(form.password.data):
            login_user(admin)
            flash('Login successful!','success')
            return redirect(url_for('admin.dashboard'))

        else:
            flash('Invalid email or password! Try again', 'danger')
            return redirect(url_for('auth.admin_login'))
    return render_template('admin_login.html', form=form)




@auth_bp.route('/login', methods=['GET', 'POST'])
def user_login():
    if current_user.is_authenticated:
        user_identifier = current_user.get_id()  
        if user_identifier.startswith("admin-"):
            return redirect(url_for('admin.dashboard'))
        else:
            return redirect(url_for('user.dashboard'))
    
    form = UserLoginForm()

    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()

        if user and user.check_password(form.password.data):
            login_user(user)
            flash('Login successful!','success')
            return redirect(url_for('user.dashboard'))

        else:
            flash('Invalid email or password! Try again', 'danger')
            return redirect(url_for('auth.user_login'))

    return render_template('login.html', form=form)


@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        user_identifier = current_user.get_id()  
        if user_identifier.startswith("admin-"):
            return redirect(url_for('admin.dashboard'))
        else:
            return redirect(url_for('user.dashboard'))

    form = UserRegistrationForm()
    
    if form.validate_on_submit():
        username = form.username.data
        email = form.email.data
        password = form.password.data
        full_name = form.full_name.data
        qualification = form.qualification.data
        dob = form.dob.data

        if User.query.filter_by(email=email).first():
            flash('Email already registered', 'danger')
            return redirect(url_for('auth.user_login'))
        
        if User.query.filter_by(username=username).first():
            flash('Username already taken', 'danger')
            return redirect(url_for('auth.register'))

        user = User(
            username=username,
            email=email,
            full_name=full_name,
            qualification=qualification,
            dob=dob
        )
        user.set_password(password) 

        db.session.add(user)
        db.session.commit()

        flash('Registration successful. Please log in.', 'success')
        return redirect(url_for('auth.user_login'))

    return render_template('register.html', form=form)

@auth_bp.route('/logout')
@login_required
def logout():
    logout_user()
    flash('You have been logged out', 'info')
    return redirect(url_for('auth.home'))