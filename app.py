

from flask import Flask, render_template, request, redirect, url_for, flash, session
from flask_talisman import Talisman
from flask_wtf.csrf import CSRFProtect
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime, timedelta
import time
import threading
from collections import deque
import os
import json

app = Flask(__name__)
Talisman(app)
csrf = CSRFProtect(app)

app.config.update(
    SESSION_COOKIE_HTTPONLY=True,
    SESSION_COOKIE_SECURE=True,
    SESSION_COOKIE_SAMESITE='Lax'
)
app.secret_key = 'college_notice_board_secret_2025'
app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(hours=2)

# Database configuration - JUST ADDED THIS
basedir = os.path.abspath(os.path.dirname(__file__))
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + os.path.join(basedir, 'notice_board.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)  # JUST ADDED THIS

# Database Models - JUST ADDED THIS
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password = db.Column(db.String(80), nullable=False)
    role = db.Column(db.String(20), nullable=False)
    name = db.Column(db.String(100), nullable=False)
    department = db.Column(db.String(50), nullable=False)
    year = db.Column(db.String(10), nullable=True)

class Notice(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    content = db.Column(db.Text, nullable=False)
    department = db.Column(db.String(50), nullable=False)
    type = db.Column(db.String(50), nullable=False)
    priority = db.Column(db.String(20), nullable=False)
    author = db.Column(db.String(80), nullable=False)
    author_name = db.Column(db.String(100), nullable=False)
    timestamp = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    expiry = db.Column(db.DateTime, nullable=False)

# In-memory storage (for backward compatibility) - YOUR EXISTING CODE
notices = deque(maxlen=100)
users = {
    # Admin Accounts
    'admin': {'password': 'admin123', 'role': 'admin', 'name': 'College Admin', 'department': 'ALL'},
    
    # HOD Accounts
    'hod_cse': {'password': 'hod123', 'role': 'admin', 'name': 'HOD CSE', 'department': 'CSE'},
    'hod_ece': {'password': 'hod123', 'role': 'admin', 'name': 'HOD ECE', 'department': 'ECE'},
    'hod_eee': {'password': 'hod123', 'role': 'admin', 'name': 'HOD EEE', 'department': 'EEE'},
    'hod_mech': {'password': 'hod123', 'role': 'admin', 'name': 'HOD MECH', 'department': 'MECH'},
    'hod_civil': {'password': 'hod123', 'role': 'admin', 'name': 'HOD CIVIL', 'department': 'CIVIL'},
    'hod_aids': {'password': 'hod123', 'role': 'admin', 'name': 'HOD AIDS', 'department': 'AIDS'},
    'hod_it': {'password': 'hod123', 'role': 'admin', 'name': 'HOD IT', 'department': 'IT'},
    
    # Student Accounts
    'student1': {'password': 'student123', 'role': 'student', 'name': 'Shivaani', 'department': 'CSE', 'year': 'III'},
    'student2': {'password': 'student123', 'role': 'student', 'name': 'Priya', 'department': 'ECE', 'year': 'II'},
    'student3': {'password': 'student123', 'role': 'student', 'name': 'Pooja', 'department': 'EEE', 'year': 'IV'},
    'student4': {'password': 'student123', 'role': 'student', 'name': 'Abi', 'department': 'MECH', 'year': 'III'},
    'student5': {'password': 'student123', 'role': 'student', 'name': 'Anjali Singh', 'department': 'CIVIL', 'year': 'II'},
    'student6': {'password': 'student123', 'role': 'student', 'name': 'Vikram Raj', 'department': 'AIDS', 'year': 'III'},
    'student7': {'password': 'student123', 'role': 'student', 'name': 'Divya', 'department': 'IT', 'year': 'II'}
}

# Departments with AIDS and IT
departments = ['ALL', 'CSE', 'ECE', 'EEE', 'MECH', 'CIVIL', 'AIDS', 'IT']
notice_types = ['General', 'Academic', 'Event', 'Emergency', 'Placement', 'Exam']

# Clear any existing notices
notices.clear()

def get_current_time():
    """Get current time as timezone-naive datetime"""
    return datetime.now().replace(microsecond=0)

def make_timezone_naive(dt):
    """Convert datetime to timezone-naive if it's timezone-aware"""
    if dt.tzinfo is not None:
        return dt.replace(tzinfo=None)
    return dt

def safe_datetime_compare(dt1, dt2):
    """Safely compare two datetimes, making them both timezone-naive"""
    dt1_naive = make_timezone_naive(dt1)
    dt2_naive = make_timezone_naive(dt2)
    return dt1_naive, dt2_naive

# Add sample notices with current dates
sample_notices = [
    {
        'id': 1,
        'title': 'SIH 2025 Internal Registration Started',
        'content': 'Smart India Hackathon 2025 internal registration portal is now open. Last date: 15th December 2024.',
        'department': 'ALL',
        'type': 'Event',
        'priority': 'High',
        'author': 'admin',
        'author_name': 'College Admin',
        'timestamp': get_current_time() - timedelta(days=1),
        'expiry': get_current_time() + timedelta(days=20)
    },
    {
        'id': 2,
        'title': 'End Semester Exams Schedule',
        'content': 'End semester examinations for odd semester 2024-25 will commence from December 10th, 2024.',
        'department': 'ALL',
        'type': 'Exam',
        'priority': 'High',
        'author': 'admin',
        'author_name': 'College Admin',
        'timestamp': get_current_time() - timedelta(days=2),
        'expiry': get_current_time() + timedelta(days=15)
    },
    {
        'id': 3,
        'title': 'CSE Department Lab Maintenance',
        'content': 'Computer Lab 1 will be closed for maintenance on 30th November 2024.',
        'department': 'CSE',
        'type': 'General',
        'priority': 'Medium',
        'author': 'hod_cse',
        'author_name': 'HOD CSE',
        'timestamp': get_current_time() - timedelta(hours=5),
        'expiry': get_current_time() + timedelta(days=5)
    },
    {
        'id': 4,
        'title': 'ECE Workshop on IoT',
        'content': 'Two-day workshop on Internet of Things for ECE students on 5th-6th December 2024.',
        'department': 'ECE',
        'type': 'Event',
        'priority': 'Medium',
        'author': 'hod_ece',
        'author_name': 'HOD ECE',
        'timestamp': get_current_time() - timedelta(days=1),
        'expiry': get_current_time() + timedelta(days=10)
    },
    {
        'id': 5,
        'title': 'AIDS AI/ML Workshop',
        'content': 'Hands-on workshop on Artificial Intelligence and Machine Learning for AIDS students.',
        'department': 'AIDS',
        'type': 'Academic',
        'priority': 'High',
        'author': 'hod_aids',
        'author_name': 'HOD AIDS',
        'timestamp': get_current_time() - timedelta(hours=3),
        'expiry': get_current_time() + timedelta(days=25)
    },
    {
        'id': 6,
        'title': 'IT Department Hackathon',
        'content': 'Annual coding hackathon for IT students on 15th December 2024.',
        'department': 'IT',
        'type': 'Event',
        'priority': 'Medium',
        'author': 'hod_it',
        'author_name': 'HOD IT',
        'timestamp': get_current_time() - timedelta(hours=8),
        'expiry': get_current_time() + timedelta(days=18)
    }
]

# Add sample notices to the deque
for notice in sample_notices:
    notices.append(notice)

notice_counter = 7

def can_delete_notice(notice, user_department):
    """Check if user can delete the notice"""
    if user_department == 'ALL':
        return True  # Main admin can delete any notice
    return notice['department'] == user_department  # HOD can only delete their department notices

def cleanup_expired_notices():
    """Background thread to remove expired notices"""
    while True:
        current_time = get_current_time()
        valid_notices = deque(maxlen=100)
        for notice in notices:
            # Ensure both are timezone-naive for comparison
            expiry_naive = make_timezone_naive(notice['expiry'])
            if expiry_naive > current_time:
                valid_notices.append(notice)
        
        notices.clear()
        notices.extend(valid_notices)
        time.sleep(3600)  # Check every hour

# Start cleanup thread
cleanup_thread = threading.Thread(target=cleanup_expired_notices, daemon=True)
cleanup_thread.start()

# Initialize database with sample data - JUST ADDED THIS
def sync_database():
    """Sync in-memory data with database"""
    with app.app_context():
        # Create tables if they don't exist
        db.create_all()
        
        # Sync users to database
        for username, user_data in users.items():
            existing_user = User.query.filter_by(username=username).first()
            if not existing_user:
                user = User(
                    username=username,
                    password=user_data['password'],
                    role=user_data['role'],
                    name=user_data['name'],
                    department=user_data['department'],
                    year=user_data.get('year')
                )
                db.session.add(user)
        
        # Sync notices to database
        for notice_data in notices:
            existing_notice = Notice.query.filter_by(id=notice_data['id']).first()
            if not existing_notice:
                notice = Notice(
                    id=notice_data['id'],
                    title=notice_data['title'],
                    content=notice_data['content'],
                    department=notice_data['department'],
                    type=notice_data['type'],
                    priority=notice_data['priority'],
                    author=notice_data['author'],
                    author_name=notice_data['author_name'],
                    timestamp=notice_data['timestamp'],
                    expiry=notice_data['expiry']
                )
                db.session.add(notice)
        
        db.session.commit()

# Load data from database on startup - JUST ADDED THIS
def load_from_database():
    """Load data from database into memory on startup"""
    with app.app_context():
        # Load notices from database
        db_notices = Notice.query.all()
        notices.clear()
        for db_notice in db_notices:
            notice = {
                'id': db_notice.id,
                'title': db_notice.title,
                'content': db_notice.content,
                'department': db_notice.department,
                'type': db_notice.type,
                'priority': db_notice.priority,
                'author': db_notice.author,
                'author_name': db_notice.author_name,
                'timestamp': db_notice.timestamp,
                'expiry': db_notice.expiry
            }
            notices.append(notice)
        
        # Update notice counter
        global notice_counter
        if notices:
            notice_counter = max(notice['id'] for notice in notices) + 1
        else:
            notice_counter = 1

# Initialize database sync - JUST ADDED THIS
sync_database()
load_from_database()

# ALL YOUR EXISTING ROUTES REMAIN EXACTLY THE SAME
@app.route('/')
def index():
    """Public notice board - shows recent notices from ALL departments"""
    # Show all recent notices (not just ALL department)
    recent_notices = list(notices)[-5:]  # Last 5 notices regardless of department
    return render_template('index.html', notices=recent_notices)

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        
        if username in users and users[username]['password'] == password:
            session.permanent = True
            session['user'] = username
            session['role'] = users[username]['role']
            session['name'] = users[username]['name']
            session['department'] = users[username]['department']
            flash('Login successful!', 'success')
            
            if users[username]['role'] == 'admin':
                return redirect(url_for('admin_dashboard'))
            else:
                return redirect(url_for('student_dashboard'))
        else:
            flash('Invalid username or password!', 'error')
    
    return render_template('login.html')

@app.route('/student/dashboard')
def student_dashboard():
    if 'user' not in session or session['role'] != 'student':
        return redirect(url_for('login'))
    
    # Get ALL notices for students (no department filtering)
    relevant_notices = list(notices)
    
    # Check for new notices since last visit
    last_visit = session.get('last_visit')
    if last_visit is None:
        last_visit = datetime.min.replace(tzinfo=None)  # Make it timezone-naive
    else:
        last_visit = make_timezone_naive(last_visit)
    
    # Ensure both datetimes are timezone-naive for comparison
    new_notices = []
    for notice in relevant_notices:
        notice_time = make_timezone_naive(notice['timestamp'])
        if notice_time > last_visit:
            new_notices.append(notice)
    
    # Update last visit time (timezone-naive)
    session['last_visit'] = get_current_time()
    
    return render_template('student_dashboard.html',
                         student=users[session['user']],
                         notices=relevant_notices[-10:],  # Last 10 notices from all departments
                         new_notices_count=len(new_notices),
                         current_time=get_current_time())

@app.route('/admin/dashboard')
def admin_dashboard():
    if 'user' not in session or session['role'] != 'admin':
        return redirect(url_for('login'))

    admin_dept = session['department']

    # Get ALL notices for admin (no department filtering)
    admin_notices = list(notices)

    # Statistics - ensure timezone-naive comparison
    current_time = get_current_time()
    total_notices = len(admin_notices)
    active_notices = len([n for n in admin_notices if make_timezone_naive(n['expiry']) > current_time])
    emergency_notices = len([n for n in admin_notices if n['type'] == 'Emergency'])

    # Notices by type
    notices_by_type = {}
    for notice_type in notice_types:
        notices_by_type[notice_type] = len([n for n in admin_notices if n['type'] == notice_type])

    return render_template('admin_dashboard.html',
                         admin=users[session['user']],
                         notices=admin_notices[-15:],  # Last 15 notices from all departments
                         total_notices=total_notices,
                         active_notices=active_notices,
                         emergency_notices=emergency_notices,
                         notices_by_type=notices_by_type,
                         departments=departments,
                         notice_types=notice_types,
                         current_time=current_time,
                         can_delete_notice=can_delete_notice)

@app.route('/admin/statistics')
def admin_statistics():
    if 'user' not in session or session['role'] != 'admin':
        return redirect(url_for('login'))

    # Get ALL notices for statistics
    admin_notices = list(notices)

    # Statistics - ensure timezone-naive comparison
    current_time = get_current_time()
    total_notices = len(admin_notices)
    active_notices = len([n for n in admin_notices if make_timezone_naive(n['expiry']) > current_time])
    emergency_notices = len([n for n in admin_notices if n['type'] == 'Emergency'])

    # Type distribution for pie chart
    type_distribution = {}
    for notice_type in notice_types:
        type_distribution[notice_type] = len([n for n in admin_notices if n['type'] == notice_type])

    # Department distribution for bar chart
    dept_distribution = {}
    for dept in departments:
        if dept != 'ALL':  # Skip ALL department for chart
            dept_distribution[dept] = len([n for n in admin_notices if n['department'] == dept])

    # Prepare data for charts
    type_data = [type_distribution.get(notice_type, 0) for notice_type in notice_types]
    dept_data = [dept_distribution.get(dept, 0) for dept in list(dept_distribution.keys())]

    return render_template('admin_statistics.html',
                         admin=users[session['user']],
                         total_notices=total_notices,
                         active_notices=active_notices,
                         emergency_notices=emergency_notices,
                         notice_types=json.dumps(notice_types),
                         type_data=json.dumps(type_data),
                         departments=json.dumps(list(dept_distribution.keys())),
                         dept_data=json.dumps(dept_data))

@app.route('/create_notice', methods=['GET', 'POST'])
def create_notice():
    if 'user' not in session or session['role'] != 'admin':
        return redirect(url_for('login'))
    
    if request.method == 'POST':
        global notice_counter
        
        title = request.form['title']
        content = request.form['content']
        
        # Determine department based on user role
        if session['department'] == 'ALL':
            # Main admin can choose department
            department = request.form['department']
        else:
            # HOD can only use their own department
            department = session['department']
            
        notice_type = request.form['type']
        priority = request.form['priority']
        expiry_days = int(request.form['expiry_days'])
        
        new_notice = {
            'id': notice_counter,
            'title': title,
            'content': content,
            'department': department,
            'type': notice_type,
            'priority': priority,
            'author': session['user'],
            'author_name': session['name'],
            'timestamp': get_current_time(),
            'expiry': get_current_time() + timedelta(days=expiry_days)
        }
        
        notices.append(new_notice)
        
        # Also save to database - JUST ADDED THIS
        db_notice = Notice(
            id=notice_counter,
            title=title,
            content=content,
            department=department,
            type=notice_type,
            priority=priority,
            author=session['user'],
            author_name=session['name'],
            timestamp=get_current_time(),
            expiry=get_current_time() + timedelta(days=expiry_days)
        )
        db.session.add(db_notice)
        db.session.commit()
        
        notice_counter += 1
        
        flash('Notice published successfully!', 'success')
        return redirect(url_for('admin_dashboard'))
    
    # Get available departments based on user role
    available_departments = []
    if session['department'] == 'ALL':
        # Main admin can see all departments
        available_departments = departments
    else:
        # HOD can only see their own department
        available_departments = [session['department']]
    
    return render_template('create_notice.html',
                         departments=available_departments,
                         notice_types=notice_types,
                         user_department=session['department'])

@app.route('/delete_notice/<int:notice_id>')
def delete_notice(notice_id):
    if 'user' not in session or session['role'] != 'admin':
        return redirect(url_for('login'))
    
    # Find and remove the notice from memory
    for notice in notices:
        if notice['id'] == notice_id:
            # Check if admin has permission to delete this notice
            if session['department'] == 'ALL' or notice['department'] == session['department']:
                notices.remove(notice)
                
                # Also delete from database - JUST ADDED THIS
                db_notice = Notice.query.get(notice_id)
                if db_notice:
                    db.session.delete(db_notice)
                    db.session.commit()
                
                flash('Notice deleted successfully!', 'success')
                break
            else:
                flash('You can only delete notices from your department!', 'error')
                break
    else:
        flash('Notice not found!', 'error')
    
    return redirect(url_for('admin_dashboard'))

@app.route('/search_notices', methods=['POST'])
def search_notices():
    if 'user' not in session:
        return redirect(url_for('login'))
    
    query = request.form['query'].lower()
    department_filter = request.form.get('department', 'ALL')
    type_filter = request.form.get('type', 'ALL')
    
    filtered_notices = []
    for notice in reversed(list(notices)):
        # Apply filters
        if department_filter != 'ALL' and notice['department'] != department_filter:
            continue
        if type_filter != 'ALL' and notice['type'] != type_filter:
            continue
        
        # Search in title and content
        if (query in notice['title'].lower() or 
            query in notice['content'].lower() or
            query in notice['type'].lower()):
            filtered_notices.append(notice)
    
    if session['role'] == 'admin':
        # For admin dashboard - show all notices
        admin_notices = list(notices)
        
        current_time = get_current_time()
        total_notices = len(admin_notices)
        active_notices = len([n for n in admin_notices if make_timezone_naive(n['expiry']) > current_time])
        emergency_notices = len([n for n in admin_notices if n['type'] == 'Emergency'])
        
        notices_by_type = {}
        for notice_type in notice_types:
            notices_by_type[notice_type] = len([n for n in admin_notices if n['type'] == notice_type])
        
        return render_template('admin_dashboard.html',
                             admin=users[session['user']],
                             notices=filtered_notices,
                             total_notices=total_notices,
                             active_notices=active_notices,
                             emergency_notices=emergency_notices,
                             notices_by_type=notices_by_type,
                             departments=departments,
                             notice_types=notice_types,
                             current_time=current_time,
                             search_query=query,
                             can_delete_notice=can_delete_notice)
    else:
        # For student dashboard - show all notices
        last_visit = session.get('last_visit')
        if last_visit is None:
            last_visit = datetime.min.replace(tzinfo=None)
        else:
            last_visit = make_timezone_naive(last_visit)
        
        # Ensure both datetimes are timezone-naive for comparison
        new_notices = []
        for notice in filtered_notices:
            notice_time = make_timezone_naive(notice['timestamp'])
            if notice_time > last_visit:
                new_notices.append(notice)
        
        return render_template('student_dashboard.html',
                             student=users[session['user']],
                             notices=filtered_notices,
                             new_notices_count=len(new_notices),
                             current_time=get_current_time(),
                             search_query=query)

@app.route('/logout')
def logout():
    session.clear()
    flash('You have been logged out successfully!', 'info')
    return redirect(url_for('index'))
import os

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)