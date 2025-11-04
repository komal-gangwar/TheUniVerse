from functools import wraps
from flask import request, redirect, url_for, flash
from models import User, Admin, BusManager, Faculty, Alumni

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        user_id = request.cookies.get('user_id')
        session_token = request.cookies.get('user_token')

        
        if not user_id or not session_token:
            flash('Please login to access this page', 'warning')
            return redirect(url_for('login'))
        
        user = User.query.get(user_id)
        if not user or user.session_token != session_token:
            flash('Invalid session. Please login again', 'warning')
            return redirect(url_for('login'))
        
        return f(*args, **kwargs)
    return decorated_function

def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        admin_id = request.cookies.get('admin_id')
        admin_token = request.cookies.get('admin_token')
        
        if not admin_id or not admin_token:
            flash('Please login as admin', 'warning')
            return redirect(url_for('admin_login'))
        
        admin = Admin.query.get(admin_id)
        if not admin:
            flash('Invalid admin session', 'warning')
            return redirect(url_for('admin_login'))
        
        return f(*args, **kwargs)
    return decorated_function

def driver_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        driver_id = request.cookies.get('driver_id')
        driver_token = request.cookies.get('driver_token')
        
        if not driver_id or not driver_token:
            flash('Please login as driver', 'warning')
            return redirect(url_for('driver_login'))
        
        return f(*args, **kwargs)
    return decorated_function

def bus_manager_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        bus_manager_id = request.cookies.get('bus_manager_id')
        bus_manager_token = request.cookies.get('bus_manager_token')
        
        if not bus_manager_id or not bus_manager_token:
            flash('Please login as bus manager', 'warning')
            return redirect(url_for('login'))
        
        bus_manager = BusManager.query.get(bus_manager_id)
        if not bus_manager or bus_manager.session_token != bus_manager_token:
            flash('Invalid session', 'warning')
            return redirect(url_for('login'))
        
        return f(*args, **kwargs)
    return decorated_function

def faculty_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        faculty_id = request.cookies.get('faculty_id')
        faculty_token = request.cookies.get('faculty_token')
        
        if not faculty_id or not faculty_token:
            flash('Please login as faculty', 'warning')
            return redirect(url_for('login'))
        
        faculty = Faculty.query.get(faculty_id)
        if not faculty or faculty.session_token != faculty_token:
            flash('Invalid session', 'warning')
            return redirect(url_for('login'))
        
        return f(*args, **kwargs)
    return decorated_function

def alumni_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        alumni_id = request.cookies.get('alumni_id')
        alumni_token = request.cookies.get('alumni_token')
        
        if not alumni_id or not alumni_token:
            flash('Please login as alumni', 'warning')
            return redirect(url_for('login'))
        
        alumni = Alumni.query.get(alumni_id)
        if not alumni or alumni.session_token != alumni_token:
            flash('Invalid session', 'warning')
            return redirect(url_for('login'))
        
        return f(*args, **kwargs)
    return decorated_function

def club_leader_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        user_id = request.cookies.get('user_id')
        session_token = request.cookies.get('session_token')
        
        if not user_id or not session_token:
            flash('Please login to access this page', 'warning')
            return redirect(url_for('login'))
        
        user = User.query.get(user_id)
        if not user or user.session_token != session_token:
            flash('Invalid session', 'warning')
            return redirect(url_for('login'))
        
        from models import Club
        if not Club.query.filter_by(secretary_id=user.id).first():
            flash('Access denied. Club leader privileges required', 'error')
            return redirect(url_for('dashboard'))
        
        return f(*args, **kwargs)
    return decorated_function
