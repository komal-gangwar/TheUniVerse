from flask import Flask, render_template, request, redirect, url_for, flash, make_response, jsonify, send_from_directory
from flask_mail import Mail
from flask_wtf.csrf import CSRFProtect
from flask_migrate import Migrate
from models import db, User, TempUser, Bus, BusStop, Driver, AcademicResource, Event, Alumni, Faculty, Club, \
    ClubMembership, CommunityPost, PostLike, Admin, ChatHistory, PracticeQuestion, UserPreferences, PasswordResetToken, \
    BusManager, ClubTagRequest, AlumniContactRequest, EventParticipation, AlumniChat, Timetable
from config import Config
from utils.auth import generate_token, generate_session_token, get_expiry_time, is_token_expired
from utils.email_utils import send_verification_email, send_password_reset_email
from utils.decorators import login_required, admin_required, driver_required, bus_manager_required, faculty_required, alumni_required, club_leader_required
from utils.gemini_utils import chat_with_ai, generate_practice_questions, check_coding_answer
from utils.db_context import get_database_context, format_context_for_ai
from datetime import datetime
import os
import json

app = Flask(__name__)
app.config.from_object(Config)

db.init_app(app)
migrate = Migrate(app, db)

mail = Mail(app)
csrf = CSRFProtect(app)

os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

with app.app_context():
    db.create_all()

@app.route('/')
def index():
    user_id = request.cookies.get('user_id')
    if user_id:
        return redirect(url_for('dashboard'))
    return redirect(url_for('login'))

@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        name = request.form.get('name')
        email = request.form.get('email')
        password = request.form.get('password')
        
        if User.query.filter_by(email=email).first() or TempUser.query.filter_by(email=email).first():
            flash('Email already registered', 'error')
            return redirect(url_for('signup'))
        
        verification_token = generate_token()
        temp_user = TempUser(
            name=name,
            email=email,
            verification_token=verification_token,
            expires_at=get_expiry_time(15)
        )
        temp_user.set_password(password)
        
        db.session.add(temp_user)
        db.session.commit()
        
        send_verification_email(mail, email, verification_token, name)
        
        flash('Verification email sent! Please check your inbox.', 'success')
        return redirect(url_for('login'))
    
    return render_template('signup.html')

@app.route('/verify/<token>')
def verify_email(token):
    temp_user = TempUser.query.filter_by(verification_token=token).first()
    
    if not temp_user:
        flash('Invalid verification link', 'error')
        return redirect(url_for('login'))
    
    if is_token_expired(temp_user.expires_at):
        db.session.delete(temp_user)
        db.session.commit()
        flash('Verification link expired. Please register again.', 'error')
        return redirect(url_for('signup'))
    
    user = User(
        name=temp_user.name,
        email=temp_user.email,
        password_hash=temp_user.password_hash
    )
    
    db.session.add(user)
    db.session.delete(temp_user)
    db.session.commit()
    
    flash('Email verified successfully! Please login.', 'success')
    return redirect(url_for('login'))

@app.route('/login')
def login():
    return render_template('login-selector.html')

@app.route('/login-student', methods=['GET', 'POST'])
def login_student():
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        force_logout = request.form.get('force_logout', False)

        user_obj = User.query.filter_by(email=email).first()

        if not user_obj or not user_obj.check_password(password):
            flash('Invalid credentials', 'error')
            return redirect(url_for('login_student'))

        if user_obj.login_status and not force_logout:
            flash('Account is active on another device. Please confirm force logout.', 'warning')
            return render_template('login-student.html', email=email, ask_force=True)

        session_token = generate_session_token()
        user_obj.session_token = session_token
        user_obj.login_status = True
        user_obj.last_login_device = request.headers.get('User-Agent', 'Unknown')
        db.session.commit()

        response = make_response(redirect(url_for('dashboard')))
        response.set_cookie('user_id', str(user_obj.id), max_age=30*24*60*60, httponly=True, samesite='Lax')
        response.set_cookie('user_token', session_token, max_age=30*24*60*60, httponly=True, samesite='Lax')

        flash('Login successful!', 'success')
        return response

    return render_template('login-student.html')

@app.route('/login-authority', methods=['GET', 'POST'])
def login_authority():
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        role = request.form.get('role')
        force_logout = request.form.get('force_logout', False)

        user_obj = None
        redirect_to = None
        cookie_prefix = None

        if role == 'faculty':
            user_obj = Faculty.query.filter_by(email=email).first()
            redirect_to = 'faculty_dashboard'
            cookie_prefix = 'faculty'
        elif role == 'alumni':
            user_obj = Alumni.query.filter_by(email=email).first()
            redirect_to = 'alumni_dashboard'
            cookie_prefix = 'alumni'
        elif role == 'driver':
            user_obj = Driver.query.filter_by(email=email).first()
            redirect_to = 'driver_panel'
            cookie_prefix = 'driver'
        elif role == 'bus_manager':
            user_obj = BusManager.query.filter_by(email=email).first()
            redirect_to = 'bus_manager_dashboard'
            cookie_prefix = 'bus_manager'
        elif role == 'club_leader':
            user_obj = User.query.filter_by(email=email).first()
            if user_obj and user_obj.led_clubs:
                redirect_to = 'club_leader_dashboard'
                cookie_prefix = 'user'
            else:
                user_obj = None

        if not user_obj or not user_obj.check_password(password):
            flash('Invalid credentials', 'error')
            return redirect(url_for('login_authority'))

        if hasattr(user_obj, 'login_status') and user_obj.login_status and not force_logout:
            flash('Account is active on another device. Please confirm force logout.', 'warning')
            return render_template('login-authority.html', role=role, email=email, ask_force=True)

        session_token = generate_session_token()
        user_obj.session_token = session_token
        if hasattr(user_obj, 'login_status'):
            user_obj.login_status = True
        if hasattr(user_obj, 'last_login_device'):
            user_obj.last_login_device = request.headers.get('User-Agent', 'Unknown')
        db.session.commit()

        response = make_response(redirect(url_for(redirect_to)))
        response.set_cookie(f'{cookie_prefix}_id', str(user_obj.id), max_age=30*24*60*60, httponly=True, samesite='Lax')
        response.set_cookie(f'{cookie_prefix}_token', session_token, max_age=30*24*60*60, httponly=True, samesite='Lax')

        flash('Login successful!', 'success')
        return response

    return render_template('login-authority.html')

@app.route('/login-admin', methods=['GET', 'POST'])
def login_admin():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')

        admin_obj = Admin.query.filter_by(username=username).first()

        if not admin_obj or not admin_obj.check_password(password):
            flash('Invalid credentials', 'error')
            return redirect(url_for('login_admin'))

        session_token = generate_session_token()
        admin_obj.session_token = session_token
        db.session.commit()

        response = make_response(redirect(url_for('admin_dashboard')))
        response.set_cookie('admin_id', str(admin_obj.id), max_age=30*24*60*60, httponly=True, samesite='Lax')
        response.set_cookie('admin_token', session_token, max_age=30*24*60*60, httponly=True, samesite='Lax')

        flash('Login successful!', 'success')
        return response

    return render_template('login-admin.html')

@app.route('/logout')
@login_required
def logout():
    user_id = request.cookies.get('user_id')
    user = User.query.get(user_id)
    
    if user:
        user.login_status = False
        user.session_token = None
        db.session.commit()
    
    response = make_response(redirect(url_for('login')))
    response.delete_cookie('user_id')
    response.delete_cookie('session_token')
    
    flash('Logged out successfully', 'success')
    return response

@app.route('/forgot-password', methods=['GET', 'POST'])
def forgot_password():
    if request.method == 'POST':
        email = request.form.get('email')
        user = User.query.filter_by(email=email).first()
        
        if user:
            reset_token = generate_token()
            password_reset = PasswordResetToken(
                email=email,
                token=reset_token,
                expires_at=get_expiry_time(15)
            )
            db.session.add(password_reset)
            db.session.commit()
            
            send_password_reset_email(mail, email, reset_token, user.name)
            flash('Password reset link sent to your email', 'success')
        else:
            flash('If this email exists, a reset link has been sent', 'info')
        
        return redirect(url_for('login'))
    
    return render_template('forgot-password.html')

@app.route('/reset-password/<token>', methods=['GET', 'POST'])
def reset_password(token):
    reset_request = PasswordResetToken.query.filter_by(token=token).first()
    
    if not reset_request:
        flash('Invalid reset link', 'error')
        return redirect(url_for('login'))
    
    if is_token_expired(reset_request.expires_at):
        db.session.delete(reset_request)
        db.session.commit()
        flash('Reset link expired. Please request a new one', 'error')
        return redirect(url_for('forgot_password'))
    
    if request.method == 'POST':
        new_password = request.form.get('password')
        confirm_password = request.form.get('confirm_password')
        
        if new_password != confirm_password:
            flash('Passwords do not match', 'error')
            return render_template('reset-password.html', token=token)
        
        user = User.query.filter_by(email=reset_request.email).first()
        if user:
            user.set_password(new_password)
            db.session.delete(reset_request)
            db.session.commit()
            flash('Password reset successful! Please login', 'success')
            return redirect(url_for('login'))
    
    return render_template('reset-password.html', token=token)

@app.route('/dashboard')
@login_required
def dashboard():
    # Get current user from cookie
    user_id = request.cookies.get('user_id')
    user = User.query.get(user_id)

    # Count upcoming events (event_date in the future)
    upcoming_events_count = db.session.query(Event.id).filter(Event.event_date >= datetime.utcnow()).count()
    
    # Optional: Fetch highlighted event for banner/top section
    highlighted_event = Event.query.filter(Event.is_highlighted == True).first()
    
    # Optional: Fetch recent past events for highlight section
    past_events = (
        Event.query
        .filter(Event.event_date < datetime.utcnow())
        .order_by(Event.event_date.desc())
        .limit(5)
        .all()
    )

    # Optional: You can also categorize events by type for filtering
    event_types = db.session.query(Event.event_type).distinct().all()

    return render_template(
        'dashboard.html',
        user=user,
        upcoming_events_count=upcoming_events_count,
        highlighted_event=highlighted_event,
        past_events=past_events,
        event_types=[etype[0] for etype in event_types if etype[0]]  # flatten tuple list
    )

@app.route('/profile')
@login_required
def profile():
    user_id = request.cookies.get('user_id')
    user = User.query.get(user_id)
    buses = Bus.query.filter_by(is_active=True).all()
    
    bus_stops = {}
    for bus in buses:
        stops = BusStop.query.filter_by(bus_id=bus.id).order_by(BusStop.stop_order).all()
        bus_stops[bus.id] = [{'id': stop.id, 'name': stop.stop_name} for stop in stops]
    
    return render_template('profile.html', user=user, buses=buses, bus_stops=bus_stops)

@app.route('/update-profile', methods=['POST'])
@login_required
def update_profile():
    user_id = request.cookies.get('user_id')
    user = User.query.get(user_id)
    
    user.course = request.form.get('course')
    user.branch = request.form.get('branch')
    user.batch = request.form.get('batch')
    user.year = request.form.get('year')
    
    selected_bus_id = request.form.get('selected_bus_id')
    selected_stop = request.form.get('selected_stop')
    
    user.selected_bus_id = int(selected_bus_id) if selected_bus_id else None
    user.selected_stop = selected_stop if selected_stop else None
    
    db.session.commit()
    flash('Profile updated successfully', 'success')
    return redirect(url_for('profile'))

@app.route('/bus-tracking')
@login_required
def bus_tracking():
    user_id = request.cookies.get('user_id')
    user = User.query.get(user_id)
    buses = Bus.query.filter_by(is_active=True).all()
    return render_template('bus-tracking.html', user=user, buses=buses)

@app.route('/select-bus', methods=['POST'])
@login_required
@csrf.exempt
def select_bus():
    user_id = request.cookies.get('user_id')
    user = User.query.get(user_id)
    data = request.get_json()
    
    user.selected_bus_id = data.get('bus_id')
    db.session.commit()
    
    return jsonify({'message': 'Bus selected successfully'})

@app.route('/bus/<int:bus_id>/data')
@login_required
def bus_data(bus_id):
    bus = Bus.query.get_or_404(bus_id)
    stops = BusStop.query.filter_by(bus_id=bus_id).order_by(BusStop.stop_order).all()
    
    return jsonify({
        'bus_number': bus.bus_number,
        'current_lat': bus.current_lat,
        'current_lng': bus.current_lng,
        'stops': [{
            'stop_name': stop.stop_name,
            'lat': stop.lat,
            'lng': stop.lng,
            'is_crossed': stop.is_crossed
        } for stop in stops]
    })

@app.route('/bus/<int:bus_id>/location')
@login_required
def bus_location(bus_id):
    bus = Bus.query.get_or_404(bus_id)
    return jsonify({
        'lat': bus.current_lat,
        'lng': bus.current_lng,
        'last_updated': bus.last_updated.isoformat() if bus.last_updated else None
    })

@app.route('/driver/login', methods=['GET', 'POST'])
def driver_login():
    if request.method == 'POST':
        name = request.form.get('name')
        password = request.form.get('password')
        
        driver = Driver.query.filter(Driver.name.ilike(name)).first()
        
        if not driver or not driver.check_password(password):
            flash('Invalid credentials', 'error')
            return redirect(url_for('driver_login'))
        
        response = make_response(redirect(url_for('driver_panel')))
        response.set_cookie('driver_id', str(driver.id), max_age=24*60*60)
        response.set_cookie('driver_token', generate_session_token(), max_age=24*60*60)
        
        return response
    
    return render_template('driver.html')

@app.route('/driver/panel')
@driver_required
def driver_panel():
    driver_id = request.cookies.get('driver_id')
    driver = Driver.query.get(driver_id)
    return render_template('driver.html', driver=driver)

@app.route('/driver/toggle-location', methods=['POST'])
@driver_required
@csrf.exempt
def toggle_location():
    driver_id = request.cookies.get('driver_id')
    driver = Driver.query.get(driver_id)
    driver.is_sharing_location = not driver.is_sharing_location
    db.session.commit()
    return jsonify({'status': driver.is_sharing_location})

@app.route('/driver/update-location', methods=['POST'])
@driver_required
@csrf.exempt
def update_location():
    driver_id = request.cookies.get('driver_id')
    driver = Driver.query.get(driver_id)
    data = request.get_json()
    
    if driver.bus:
        driver.bus.current_lat = data.get('lat')
        driver.bus.current_lng = data.get('lng')
        driver.bus.last_updated = datetime.utcnow()
        db.session.commit()
    
    return jsonify({'success': True})

@app.route('/driver/logout')
def driver_logout():
    response = make_response(redirect(url_for('driver_login')))
    response.delete_cookie('driver_id')
    response.delete_cookie('driver_token')
    return response


@app.route('/academic-resources')
@login_required
def academic_resources():
    user_id = request.cookies.get('user_id')
    user = User.query.get(user_id)
    # Query the database for a list of unique subjects
    # The 'subject' field is what we want to display on the cards
    # Use SQLAlchemy's distinct() method to get unique values
    subjects = [s[0] for s in db.session.query(AcademicResource.subject).distinct()]
    print(subjects)
    # Render the template and pass the list of unique subjects
    return render_template('academic-resources.html', subjects=subjects, user=user)


@app.route('/academic-resources/<string:subject_name>')
@login_required
def subject_resources(subject_name):
    user_id = request.cookies.get('user_id')
    user = User.query.get(user_id)
    # This is the new route for the sub-page
    # Query all resources that match the given subject name
    resources = AcademicResource.query.filter_by(subject=subject_name).all()
    print(resources)

    # You'll need to create a new template for this page, e.g., 'subject-resources.html'
    return render_template('subject-resources.html', resources=resources, subject_name=subject_name, user=user)

@app.route('/download-resource/<int:resource_id>')
@login_required
def download_resource(resource_id):
    resource = AcademicResource.query.get_or_404(resource_id)
    resource.views += 1
    db.session.commit()
    
    try:
        directory = os.path.dirname(resource.file_path)
        filename = os.path.basename(resource.file_path)
        return send_from_directory(directory, filename, as_attachment=True)
    except Exception as e:
        flash(f'Error downloading resource: {str(e)}', 'error')
        return redirect(url_for('academic_resources'))


@app.route('/events')
@login_required
def events():
    user_id = request.cookies.get('user_id')
    user = User.query.get(user_id)
    now = datetime.utcnow()

    # 1. Query for the single highlighted upcoming event
    highlighted_event = Event.query.filter(
        Event.is_highlighted == True,
        Event.event_date >= now
    ).order_by(Event.event_date).first()

    # 2. Query for all other upcoming events, excluding the highlighted one
    upcoming_events = Event.query.filter(
        Event.event_date >= now,
        Event.id != highlighted_event.id if highlighted_event else None
    ).order_by(Event.event_date).all()

    # 3. Query for past events, ordered by most recent
    past_events = Event.query.filter(Event.event_date < now).order_by(Event.event_date.desc()).all()

    # user = User.query.get(request.cookies.get('user_id'))
    # The user object can be passed if needed, but the template doesn't use it directly from the old code.

    return render_template(
        'events.html',
        highlighted_event=highlighted_event,
        upcoming_events=upcoming_events,
        past_events=past_events,
        user=user
    )
@app.route('/alumni')
@login_required
def alumni():
    user_id = request.cookies.get('user_id')
    user = User.query.get(user_id)
    alumni_list = Alumni.query.all()
    return render_template('alumni.html', alumni=alumni_list, user=user)

@app.route('/faculty')
@login_required
def faculty():
    user_id = request.cookies.get('user_id')
    user = User.query.get(user_id)
    faculty_list = Faculty.query.all()
    return render_template('faculty.html', faculty=faculty_list, user=user)


@app.route('/faculty/<int:faculty_id>')
@login_required
def faculty_profile(faculty_id):
    # Query the database for a single faculty member by ID
    faculty_member = Faculty.query.get_or_404(faculty_id)

    # You'll need to pass the timetable data as well.
    # Assuming you have a Timetable model linked to Faculty.
    # Example: timetable = Timetable.query.filter_by(faculty_id=faculty_id).all()
    # If not, you'll need to add a Timetable model to your database.

    # Render the new profile template
    return render_template('faculty-profile.html', faculty=faculty_member)

@app.route('/community')
@login_required
def community():
    user_id = request.cookies.get('user_id')
    user = User.query.get(user_id)
    posts = CommunityPost.query.order_by(CommunityPost.created_at.desc()).all()
    
    user_liked_posts = set()
    if user_id:
        user_likes = PostLike.query.filter_by(user_id=user_id).all()
        user_liked_posts = {like.post_id for like in user_likes}
    
    return render_template('community.html', posts=posts, user=user, user_liked_posts=user_liked_posts)

@app.route('/create-post', methods=['POST'])
@login_required
def create_post():
    user_id = request.cookies.get('user_id')
    content = request.form.get('content')
    post_type = request.form.get('post_type')
    
    banned_words = ['spam', 'abuse', 'offensive']
    for word in banned_words:
        if word.lower() in content.lower():
            flash('Your post contains inappropriate content', 'error')
            return redirect(url_for('community'))
    
    post = CommunityPost(
        user_id=user_id,
        content=content,
        post_type=post_type
    )
    
    db.session.add(post)
    db.session.commit()
    
    flash('Post created successfully', 'success')
    return redirect(url_for('community'))

@app.route('/post/<int:post_id>/like', methods=['POST'])
@login_required
def like_post(post_id):
    user_id = request.cookies.get('user_id')
    post = CommunityPost.query.get_or_404(post_id)
    
    existing_like = PostLike.query.filter_by(user_id=user_id, post_id=post_id).first()
    
    if existing_like:
        db.session.delete(existing_like)
        post.likes = max(0, post.likes - 1)
        liked = False
    else:
        new_like = PostLike(user_id=user_id, post_id=post_id)
        db.session.add(new_like)
        post.likes += 1
        liked = True
    
    db.session.commit()
    return jsonify({'likes': post.likes, 'liked': liked})


@app.route('/clubs')
@login_required
def clubs():
    user_id = request.cookies.get('user_id')
    user = User.query.get(user_id)

    clubs_list = Club.query.options(
        db.joinedload(Club.memberships),
        db.joinedload(Club.secretary)
    ).all()

    user_club_ids = {m.club_id for m in user.club_memberships} if user and user.club_memberships else set()
    print(user_club_ids, clubs_list,user)
    return render_template(
        'clubs.html',
        clubs=clubs_list,
        current_user_id=user.id if user else None,
        user_club_ids=user_club_ids,
        user=user
    )
@app.route('/club/<int:club_id>')
@login_required
def club_detail(club_id):
    user_id = request.cookies.get('user_id')
    user = User.query.get(user_id)
    
    club = Club.query.options(
        db.joinedload(Club.memberships).joinedload(ClubMembership.user),
        db.joinedload(Club.secretary)
    ).get_or_404(club_id)
    
    is_member = ClubMembership.query.filter_by(user_id=user_id, club_id=club_id).first() is not None
    is_secretary = club.secretary_id == int(user_id) if user_id else False
    print(is_member, is_secretary, user_id, club.secretary_id)
    return render_template(
        'club-detail.html',
        club=club,
        is_member=is_member,
        is_secretary=is_secretary,
        user=user
    )

@app.route('/club/<int:club_id>/join', methods=['POST'])
@login_required
@csrf.exempt
def join_club(club_id):
    user_id = request.cookies.get('user_id')
    
    existing = ClubMembership.query.filter_by(user_id=user_id, club_id=club_id).first()
    if existing:
        return jsonify({'message': 'Already a member'})
    
    membership = ClubMembership(user_id=user_id, club_id=club_id)
    db.session.add(membership)
    db.session.commit()
    
    return jsonify({'message': 'Membership request sent'})

@app.route('/club/<int:club_id>/leave', methods=['POST'])
@login_required
@csrf.exempt
def leave_club(club_id):
    user_id = request.cookies.get('user_id')
    
    membership = ClubMembership.query.filter_by(user_id=user_id, club_id=club_id).first()
    if not membership:
        return jsonify({'message': 'Not a member'}), 400
    
    db.session.delete(membership)
    db.session.commit()
    
    return jsonify({'message': 'Successfully left the club'})

@app.route('/admin/login', methods=['GET', 'POST'])
def admin_login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        admin = Admin.query.filter_by(username=username).first()
        
        if not admin or not admin.check_password(password):
            flash('Invalid credentials', 'error')
            return redirect(url_for('admin_login'))
        
        response = make_response(redirect(url_for('admin_dashboard')))
        response.set_cookie('admin_id', str(admin.id), max_age=24*60*60)
        response.set_cookie('admin_token', generate_session_token(), max_age=24*60*60)
        
        return response
    
    return render_template('admin/admin-login.html')

@app.route('/admin/dashboard')
@admin_required
def admin_dashboard():
    stats = {
        'total_users': User.query.count(),
        'total_buses': Bus.query.count(),
        'total_events': Event.query.count(),
        'total_clubs': Club.query.count()
    }
    return render_template('admin/admin-dashboard.html', stats=stats)

@app.route('/admin/logout')
def admin_logout():
    response = make_response(redirect(url_for('admin_login')))
    response.delete_cookie('admin_id')
    response.delete_cookie('admin_token')
    return response

@app.route('/faculty/dashboard')
def faculty_dashboard():
    faculty_id = request.cookies.get('faculty_id')
    if not faculty_id:
        return redirect(url_for('login'))
    faculty_member = Faculty.query.get(faculty_id)
    return render_template('faculty/dashboard.html', faculty=faculty_member)

@app.route('/alumni/dashboard')
def alumni_dashboard():
    alumni_id = request.cookies.get('alumni_id')
    if not alumni_id:
        return redirect(url_for('login'))
    alumni_member = Alumni.query.get(alumni_id)
    return render_template('alumni/dashboard.html', alumni=alumni_member)

@app.route('/admin/manage/faculty', methods=['GET', 'POST'])
@admin_required
def manage_faculty():
    if request.method == 'POST':
        name = request.form.get('name')
        email = request.form.get('email')
        password = request.form.get('password')
        designation = request.form.get('designation')
        department = request.form.get('department')
        
        faculty = Faculty(
            name=name,
            email=email,
            designation=designation,
            department=department
        )
        faculty.set_password(password)
        
        db.session.add(faculty)
        db.session.commit()
        
        flash('Faculty member added successfully', 'success')
        return redirect(url_for('manage_faculty'))
    
    faculty_list = Faculty.query.all()
    return render_template('admin/manage-faculty.html', faculty_list=faculty_list)

@app.route('/admin/manage/alumni', methods=['GET', 'POST'])
@admin_required
def manage_alumni():
    if request.method == 'POST':
        name = request.form.get('name')
        email = request.form.get('email')
        password = request.form.get('password')
        batch = request.form.get('batch')
        company = request.form.get('company')
        designation = request.form.get('designation')
        
        alumni = Alumni(
            name=name,
            email=email,
            batch=batch,
            company=company,
            current_designation=designation
        )
        alumni.set_password(password)
        
        db.session.add(alumni)
        db.session.commit()
        
        flash('Alumni added successfully', 'success')
        return redirect(url_for('manage_alumni'))
    
    alumni_list = Alumni.query.all()
    return render_template('admin/manage-alumni.html', alumni_list=alumni_list)

@app.route('/admin/manage/clubs', methods=['GET', 'POST'])
@admin_required
def manage_clubs():
    if request.method == 'POST':
        action = request.form.get('action')
        
        if action == 'create':
            name = request.form.get('name')
            description = request.form.get('description')
            club_type = request.form.get('club_type')
            
            club = Club(
                name=name,
                description=description,
                club_type=club_type
            )
            db.session.add(club)
            db.session.commit()
            flash('Club created successfully', 'success')
        
        elif action == 'appoint_leader':
            club_id = request.form.get('club_id')
            student_email = request.form.get('student_email')
            
            student = User.query.filter_by(email=student_email).first()
            if student:
                club = Club.query.get(club_id)
                club.secretary_id = student.id
                db.session.commit()
                flash('Club leader appointed successfully', 'success')
            else:
                flash('Student not found', 'error')
        
        return redirect(url_for('manage_clubs'))
    
    clubs_list = Club.query.all()
    students = User.query.all()
    return render_template('admin/manage-clubs.html', clubs=clubs_list, students=students)

@app.route('/ai-teacher')
@login_required
def ai_teacher():
    user_id = request.cookies.get('user_id')
    user = User.query.get(user_id)
    return render_template('ai-teacher.html', user=user)

@app.route('/api/chat', methods=['POST'])
@login_required
@csrf.exempt
def api_chat():
    try:
        data = request.get_json()
        message = data.get('message')
        mode = data.get('mode', 'normal')
        user_id = request.cookies.get('user_id')
        
        user = User.query.get(user_id)
        user_context = {
            'name': user.name,
            'course': user.course,
            'year': user.year,
            'branch': user.branch
        }
        
        db_context = get_database_context(message, user)
        db_context_text = format_context_for_ai(db_context)
        
        enhanced_message = message
        if db_context_text:
            enhanced_message = f"{message}\n{db_context_text}"
        
        ai_response = chat_with_ai(enhanced_message, mode, user_context)
        
        chat_entry = ChatHistory(
            user_id=user_id,
            mode=mode,
            question=message,
            answer=ai_response
        )
        db.session.add(chat_entry)
        
        prefs = UserPreferences.query.filter_by(user_id=user_id).first()
        if not prefs:
            prefs = UserPreferences(user_id=user_id, last_mode=mode)
            db.session.add(prefs)
        else:
            prefs.last_mode = mode
            prefs.updated_at = datetime.now()
        
        db.session.commit()
        
        return jsonify({
            'success': True,
            'response': ai_response,
            'mode': mode
        })
    
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/get_questions', methods=['POST'])
@login_required
@csrf.exempt
def api_get_questions():
    try:
        data = request.get_json()
        subject = data.get('subject', 'Programming')
        question_type = data.get('type', 'coding')
        difficulty = data.get('difficulty', 'medium')
        
        question_data = generate_practice_questions(subject, question_type, difficulty)
        
        return jsonify({
            'success': True,
            'question': question_data
        })
    
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/check_answer', methods=['POST'])
@login_required
@csrf.exempt
def api_check_answer():
    try:
        data = request.get_json()
        question = data.get('question')
        user_answer = data.get('answer')
        test_cases = data.get('test_cases', [])
        
        result = check_coding_answer(question, user_answer, test_cases)
        
        return jsonify({
            'success': True,
            'result': result
        })
    
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/chat_history', methods=['GET'])
@login_required
def api_chat_history():
    try:
        user_id = request.cookies.get('user_id')
        history = ChatHistory.query.filter_by(user_id=user_id).order_by(ChatHistory.timestamp.desc()).limit(50).all()
        
        history_data = [{
            'mode': h.mode,
            'question': h.question,
            'answer': h.answer,
            'timestamp': h.timestamp.isoformat()
        } for h in history]
        
        return jsonify({
            'success': True,
            'history': history_data
        })
    
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


# BUS MANAGER ROUTES
@app.route('/bus-manager/dashboard')
@bus_manager_required
def bus_manager_dashboard():
    bus_manager_id = request.cookies.get('bus_manager_id')
    bus_manager = BusManager.query.get(bus_manager_id)
    buses = Bus.query.all()
    drivers = Driver.query.all()
    return render_template('bus-manager-dashboard.html', bus_manager=bus_manager, buses=buses, drivers=drivers)

# CLUB LEADER ROUTES
@app.route('/club-leader/dashboard')
def club_leader_dashboard():
    user_id = request.cookies.get('user_id')
    if not user_id:
        return redirect(url_for('login'))
    user = User.query.get(user_id)
    if not user or not user.led_clubs:
        flash('You are not a club leader', 'error')
        return redirect(url_for('dashboard'))
    return render_template('club-leader-dashboard.html', user=user)

@app.route('/bus-manager/manage-bus', methods=['POST'])
@bus_manager_required
@csrf.exempt
def manage_bus():
    data = request.get_json()
    action = data.get('action')
    
    if action == 'create':
        bus = Bus(bus_number=data.get('bus_number'), route_description=data.get('route_description'), is_active=True)
        db.session.add(bus)
        db.session.commit()
        return jsonify({'success': True, 'bus_id': bus.id})
    elif action == 'update':
        bus = Bus.query.get(data.get('bus_id'))
        if bus:
            bus.is_active = data.get('is_active', bus.is_active)
            bus.driver_id = data.get('driver_id', bus.driver_id)
            db.session.commit()
            return jsonify({'success': True})
    elif action == 'delete':
        bus = Bus.query.get(data.get('bus_id'))
        if bus:
            db.session.delete(bus)
            db.session.commit()
            return jsonify({'success': True})
    
    return jsonify({'success': False, 'error': 'Invalid action'})

@app.route('/bus-manager/manage-driver', methods=['POST'])
@bus_manager_required
@csrf.exempt
def manage_driver():
    data = request.get_json()
    action = data.get('action')
    
    if action == 'create':
        driver = Driver(name=data.get('name'))
        driver.set_password(data.get('password'))
        db.session.add(driver)
        db.session.commit()
        return jsonify({'success': True, 'driver_id': driver.id})
    elif action == 'delete':
        driver = Driver.query.get(data.get('driver_id'))
        if driver:
            db.session.delete(driver)
            db.session.commit()
            return jsonify({'success': True})
    elif action == 'assign_bus':
        driver = Driver.query.get(data.get('driver_id'))
        if driver:
            driver.assigned_bus_id = data.get('bus_id')
            bus = Bus.query.get(data.get('bus_id'))
            if bus:
                bus.driver_id = driver.id
            db.session.commit()
            return jsonify({'success': True})
    
    return jsonify({'success': False, 'error': 'Invalid action'})

@app.route('/bus-manager/manage-route', methods=['POST'])
@bus_manager_required
@csrf.exempt
def manage_route():
    data = request.get_json()
    action = data.get('action')
    
    if action == 'add_stop':
        stop = BusStop(
            bus_id=data.get('bus_id'),
            stop_name=data.get('stop_name'),
            stop_order=data.get('stop_order'),
            lat=data.get('lat'),
            lng=data.get('lng')
        )
        db.session.add(stop)
        db.session.commit()
        return jsonify({'success': True, 'stop_id': stop.id})
    elif action == 'remove_stop':
        stop = BusStop.query.get(data.get('stop_id'))
        if stop:
            db.session.delete(stop)
            db.session.commit()
            return jsonify({'success': True})
    elif action == 'update_time':
        bus = Bus.query.get(data.get('bus_id'))
        if bus:
            bus.route_description = data.get('route_description', bus.route_description)
            db.session.commit()
            return jsonify({'success': True})
    
    return jsonify({'success': False, 'error': 'Invalid action'})

# CLUB TAG REQUEST ROUTES
@app.route('/student/request-club-tag', methods=['POST'])
@login_required
@csrf.exempt
def request_club_tag():
    user_id = request.cookies.get('user_id')
    data = request.get_json()
    
    club_id = data.get('club_id')
    existing_request = ClubTagRequest.query.filter_by(user_id=user_id, club_id=club_id, status='pending').first()
    
    if existing_request:
        return jsonify({'success': False, 'error': 'Request already pending'})
    
    tag_request = ClubTagRequest(user_id=user_id, club_id=club_id)
    db.session.add(tag_request)
    db.session.commit()
    
    return jsonify({'success': True, 'request_id': tag_request.id})

@app.route('/club-leader/tag-requests')
@club_leader_required
def view_tag_requests():
    user_id = request.cookies.get('user_id')
    clubs = Club.query.filter_by(secretary_id=user_id).all()
    
    requests = []
    for club in clubs:
        for req in club.tag_requests:
            if req.status == 'pending':
                requests.append({
                    'id': req.id,
                    'student_name': req.user.name,
                    'student_email': req.user.email,
                    'club_name': club.name,
                    'requested_at': req.requested_at.isoformat()
                })
    
    return jsonify({'success': True, 'requests': requests})

@app.route('/club-leader/review-tag-request', methods=['POST'])
@club_leader_required
@csrf.exempt
def review_tag_request():
    user_id = request.cookies.get('user_id')
    data = request.get_json()
    
    tag_request = ClubTagRequest.query.get(data.get('request_id'))
    if not tag_request or tag_request.club.secretary_id != int(user_id):
        return jsonify({'success': False, 'error': 'Unauthorized'})
    
    tag_request.status = data.get('status')
    tag_request.reviewed_by = user_id
    tag_request.reviewed_at = datetime.utcnow()
    
    if data.get('status') == 'approved':
        membership = ClubMembership(user_id=tag_request.user_id, club_id=tag_request.club_id, is_verified=True, verified_by=user_id)
        db.session.add(membership)
    
    db.session.commit()
    return jsonify({'success': True})

# ALUMNI CONTACT REQUEST ROUTES
@app.route('/student/request-alumni-contact', methods=['POST'])
@login_required
@csrf.exempt
def request_alumni_contact():
    user_id = request.cookies.get('user_id')
    data = request.get_json()
    
    alumni_id = data.get('alumni_id')
    message = data.get('message', '')
    
    existing_request = AlumniContactRequest.query.filter_by(student_id=user_id, alumni_id=alumni_id, status='pending').first()
    if existing_request:
        return jsonify({'success': False, 'error': 'Request already pending'})
    
    contact_request = AlumniContactRequest(student_id=user_id, alumni_id=alumni_id, message=message)
    db.session.add(contact_request)
    db.session.commit()
    
    return jsonify({'success': True, 'request_id': contact_request.id})

@app.route('/alumni/contact-requests')
@alumni_required
def view_contact_requests():
    alumni_id = request.cookies.get('alumni_id')
    requests = AlumniContactRequest.query.filter_by(alumni_id=alumni_id, status='pending').all()
    
    return jsonify({
        'success': True,
        'requests': [{
            'id': req.id,
            'student_name': req.student.name,
            'student_email': req.student.email,
            'message': req.message,
            'requested_at': req.requested_at.isoformat()
        } for req in requests]
    })

@app.route('/alumni/review-contact-request', methods=['POST'])
@alumni_required
@csrf.exempt
def review_contact_request():
    alumni_id = request.cookies.get('alumni_id')
    data = request.get_json()
    
    contact_request = AlumniContactRequest.query.get(data.get('request_id'))
    if not contact_request or contact_request.alumni_id != int(alumni_id):
        return jsonify({'success': False, 'error': 'Unauthorized'})
    
    contact_request.status = data.get('status')
    contact_request.responded_at = datetime.utcnow()
    db.session.commit()
    
    return jsonify({'success': True})

# ALUMNI CHAT ROUTES
@app.route('/alumni/send-message', methods=['POST'])
@alumni_required
@csrf.exempt
def alumni_send_message():
    alumni_id = request.cookies.get('alumni_id')
    data = request.get_json()
    
    student_id = data.get('student_id')
    accepted_request = AlumniContactRequest.query.filter_by(student_id=student_id, alumni_id=alumni_id, status='accepted').first()
    
    if not accepted_request:
        return jsonify({'success': False, 'error': 'Contact not accepted'})
    
    chat_message = AlumniChat(alumni_id=alumni_id, student_id=student_id, sender_type='alumni', message=data.get('message'))
    db.session.add(chat_message)
    db.session.commit()
    
    return jsonify({'success': True, 'message_id': chat_message.id})

@app.route('/student/send-alumni-message', methods=['POST'])
@login_required
@csrf.exempt
def student_send_alumni_message():
    user_id = request.cookies.get('user_id')
    data = request.get_json()
    
    alumni_id = data.get('alumni_id')
    accepted_request = AlumniContactRequest.query.filter_by(student_id=user_id, alumni_id=alumni_id, status='accepted').first()
    
    if not accepted_request:
        return jsonify({'success': False, 'error': 'Contact not accepted'})
    
    chat_message = AlumniChat(alumni_id=alumni_id, student_id=user_id, sender_type='student', message=data.get('message'))
    db.session.add(chat_message)
    db.session.commit()
    
    return jsonify({'success': True, 'message_id': chat_message.id})

@app.route('/alumni/chat/<int:student_id>')
@alumni_required
def get_alumni_chat(student_id):
    alumni_id = request.cookies.get('alumni_id')
    messages = AlumniChat.query.filter_by(alumni_id=alumni_id, student_id=student_id).order_by(AlumniChat.timestamp).all()
    
    return jsonify({
        'success': True,
        'messages': [{
            'id': msg.id,
            'sender_type': msg.sender_type,
            'message': msg.message,
            'timestamp': msg.timestamp.isoformat(),
            'is_read': msg.is_read
        } for msg in messages]
    })

@app.route('/student/chat/<int:alumni_id>')
@login_required
def get_student_chat(alumni_id):
    user_id = request.cookies.get('user_id')
    messages = AlumniChat.query.filter_by(alumni_id=alumni_id, student_id=user_id).order_by(AlumniChat.timestamp).all()
    
    return jsonify({
        'success': True,
        'messages': [{
            'id': msg.id,
            'sender_type': msg.sender_type,
            'message': msg.message,
            'timestamp': msg.timestamp.isoformat(),
            'is_read': msg.is_read
        } for msg in messages]
    })

# EVENT PARTICIPATION ROUTES
@app.route('/club-leader/create-event', methods=['POST'])
@club_leader_required
@csrf.exempt
def create_club_event():
    user_id = request.cookies.get('user_id')
    data = request.get_json()
    
    club = Club.query.filter_by(secretary_id=user_id).first()
    if not club:
        return jsonify({'success': False, 'error': 'Not a club leader'})
    
    event = Event(
        title=data.get('title'),
        description=data.get('description'),
        event_date=datetime.fromisoformat(data.get('event_date')),
        venue=data.get('venue'),
        event_type=data.get('event_type', 'club'),
        club_id=club.id,
        created_by=user_id,
        participation_form_required=data.get('participation_form_required', False),
        is_selective=data.get('is_selective', False),
        form_fields=json.dumps(data.get('form_fields', []))
    )
    db.session.add(event)
    db.session.commit()
    
    return jsonify({'success': True, 'event_id': event.id})

@app.route('/student/enroll-event', methods=['POST'])
@login_required
@csrf.exempt
def enroll_event():
    user_id = request.cookies.get('user_id')
    data = request.get_json()
    
    event_id = data.get('event_id')
    existing_enrollment = EventParticipation.query.filter_by(event_id=event_id, user_id=user_id).first()
    
    if existing_enrollment:
        return jsonify({'success': False, 'error': 'Already enrolled'})
    
    participation = EventParticipation(
        event_id=event_id,
        user_id=user_id,
        form_data=json.dumps(data.get('form_data', {})),
        status='pending' if Event.query.get(event_id).is_selective else 'approved'
    )
    db.session.add(participation)
    db.session.commit()
    
    return jsonify({'success': True, 'participation_id': participation.id})

@app.route('/club-leader/event-participants/<int:event_id>')
@club_leader_required
def view_event_participants(event_id):
    user_id = request.cookies.get('user_id')
    event = Event.query.get(event_id)
    
    if not event or event.created_by != int(user_id):
        return jsonify({'success': False, 'error': 'Unauthorized'})
    
    participants = EventParticipation.query.filter_by(event_id=event_id).all()
    
    return jsonify({
        'success': True,
        'participants': [{
            'id': p.id,
            'student_name': p.participant.name,
            'student_email': p.participant.email,
            'form_data': json.loads(p.form_data) if p.form_data else {},
            'status': p.status,
            'enrolled_at': p.enrolled_at.isoformat()
        } for p in participants]
    })

@app.route('/club-leader/review-participant', methods=['POST'])
@club_leader_required
@csrf.exempt
def review_participant():
    user_id = request.cookies.get('user_id')
    data = request.get_json()
    
    participation = EventParticipation.query.get(data.get('participation_id'))
    if not participation or participation.event.created_by != int(user_id):
        return jsonify({'success': False, 'error': 'Unauthorized'})
    
    participation.status = data.get('status')
    participation.reviewed_by = user_id
    db.session.commit()
    
    return jsonify({'success': True})

# FACULTY ROUTES
@app.route('/faculty/update-timetable', methods=['POST'])
@faculty_required
@csrf.exempt
def update_timetable():
    faculty_id = request.cookies.get('faculty_id')
    data = request.get_json()
    
    action = data.get('action')
    if action == 'add':
        timetable = Timetable(
            faculty_id=faculty_id,
            day=data.get('day'),
            time=data.get('time'),
            course=data.get('course'),
            location=data.get('location')
        )
        db.session.add(timetable)
        db.session.commit()
        return jsonify({'success': True, 'timetable_id': timetable.id})
    elif action == 'delete':
        timetable = Timetable.query.get(data.get('timetable_id'))
        if timetable and timetable.faculty_id == int(faculty_id):
            db.session.delete(timetable)
            db.session.commit()
            return jsonify({'success': True})
    
    return jsonify({'success': False})

@app.route('/faculty/upload-resource', methods=['POST'])
@faculty_required
def upload_faculty_resource():
    faculty_id = request.cookies.get('faculty_id')
    
    if 'file' not in request.files:
        return jsonify({'success': False, 'error': 'No file provided'})
    
    file = request.files['file']
    if file.filename == '':
        return jsonify({'success': False, 'error': 'No file selected'})
    
    filename = f"{datetime.utcnow().timestamp()}_{file.filename}"
    file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
    file.save(file_path)
    
    resource = AcademicResource(
        course=request.form.get('course'),
        branch=request.form.get('branch'),
        year=int(request.form.get('year')),
        subject=request.form.get('subject'),
        resource_type=request.form.get('resource_type'),
        title=request.form.get('title'),
        file_path=filename,
        uploaded_by=faculty_id
    )
    db.session.add(resource)
    db.session.commit()
    
    return jsonify({'success': True, 'resource_id': resource.id})

@app.route('/faculty/update-profile', methods=['POST'])
@faculty_required
@csrf.exempt
def update_faculty_profile():
    faculty_id = request.cookies.get('faculty_id')
    faculty = Faculty.query.get(faculty_id)
    data = request.get_json()
    
    faculty.bio = data.get('bio', faculty.bio)
    faculty.phone = data.get('phone', faculty.phone)
    faculty.office = data.get('office', faculty.office)
    faculty.linkedin = data.get('linkedin', faculty.linkedin)
    
    db.session.commit()
    return jsonify({'success': True})

# ALUMNI ROUTES
@app.route('/alumni/update-profile', methods=['POST'])
@alumni_required
@csrf.exempt
def update_alumni_profile():
    alumni_id = request.cookies.get('alumni_id')
    alumni = Alumni.query.get(alumni_id)
    data = request.get_json()
    
    alumni.current_designation = data.get('current_designation', alumni.current_designation)
    alumni.company = data.get('company', alumni.company)
    alumni.linkedin_profile = data.get('linkedin_profile', alumni.linkedin_profile)
    
    db.session.commit()
    return jsonify({'success': True})

@app.route('/alumni/notifications')
@alumni_required
def get_alumni_notifications():
    alumni_id = request.cookies.get('alumni_id')
    
    pending_requests = AlumniContactRequest.query.filter_by(alumni_id=alumni_id, status='pending').all()
    unread_chats = AlumniChat.query.filter_by(alumni_id=alumni_id, sender_type='student', is_read=False).count()
    
    return jsonify({
        'success': True,
        'contact_requests': len(pending_requests),
        'unread_messages': unread_chats
    })

# ADMIN AI MANAGER ROUTES
@app.route('/admin/ai-manager', methods=['POST'])
@admin_required
@csrf.exempt
def ai_manager_query():
    data = request.get_json()
    query = data.get('query')
    
    context = f"""
    Database Summary:
    - Total Students: {User.query.count()}
    - Total Faculty: {Faculty.query.count()}
    - Total Alumni: {Alumni.query.count()}
    - Total Buses: {Bus.query.count()}
    - Total Clubs: {Club.query.count()}
    - Total Events: {Event.query.count()}
    - Upcoming Events: {Event.query.filter(Event.event_date >= datetime.utcnow()).count()}
    
    Query: {query}
    """
    
    response = chat_with_ai(context, 'normal')
    return jsonify({'success': True, 'response': response})

@app.route('/admin/reports')
@admin_required
def get_admin_reports():
    return jsonify({
        'success': True,
        'reports': {
            'students': User.query.count(),
            'faculty': Faculty.query.count(),
            'alumni': Alumni.query.count(),
            'buses': Bus.query.count(),
            'active_buses': Bus.query.filter_by(is_active=True).count(),
            'clubs': Club.query.count(),
            'events': Event.query.count(),
            'upcoming_events': Event.query.filter(Event.event_date >= datetime.utcnow()).count(),
            'pending_club_requests': ClubTagRequest.query.filter_by(status='pending').count(),
            'pending_alumni_requests': AlumniContactRequest.query.filter_by(status='pending').count()
        }
    })

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
