{% extends "base.html" %}

{% block content %}
<div class="dashboard-header">
    <h2>Admin Dashboard</h2>
    <p>Welcome, {{ admin.name }} | Department: {{ admin.department }}</p>
</div>

<div class="stats-container">
    <div class="stat-card">
        <h3>{{ total_notices }}</h3>
        <p>Total Notices</p>
    </div>
    <div class="stat-card">
        <h3>{{ active_notices }}</h3>
        <p>Active Notices</p>
    </div>
    <div class="stat-card">
        <h3>{{ emergency_notices }}</h3>
        <p>Emergency</p>
    </div>
</div>

<form method="POST" action="{{ url_for('search_notices') }}" class="search-form">
    <div class="form-row">
        <input type="text" name="query" placeholder="Search notices..." value="{{ search_query or '' }}">
        <select name="department">
            <option value="ALL">All Departments</option>
            {% for dept in departments %}
            <option value="{{ dept }}">{{ dept }}</option>
            {% endfor %}
        </select>
        <select name="type">
            <option value="ALL">All Types</option>
            {% for type in notice_types %}
            <option value="{{ type }}">{{ type }}</option>
            {% endfor %}
        </select>
        <button type="submit" class="btn btn-secondary">Search</button>
    </div>
</form>

<div class="notices-section">
    <h3>Recent Notices</h3>
    
    {% if notices %}
        {% for notice in notices %}
        <div class="notice-card {{ notice.priority|lower }}-priority admin-notice">
            <div class="notice-header">
                <h4>{{ notice.title }}</h4>
                <div>
                    <span class="notice-badge {{ notice.type|lower }}">{{ notice.type }}</span>
                    <a href="{{ url_for('delete_notice', notice_id=notice.id) }}" 
                       class="btn btn-danger btn-small" 
                       onclick="return confirm('Delete this notice?')">Delete</a>
                </div>
            </div>
            <p class="notice-content">{{ notice.content }}</p>
            <div class="notice-meta">
                <span><strong>Department:</strong> {{ notice.department }}</span>
                <span><strong>Priority:</strong> {{ notice.priority }}</span>
                <span><strong>Author:</strong> {{ notice.author_name }}</span>
                <span><strong>Published:</strong> {{ notice.timestamp.strftime('%d-%m-%Y %H:%M') }}</span>
                <span><strong>Expires:</strong> {{ notice.expiry.strftime('%d-%m-%Y %H:%M') }}</span>
            </div>
        </div>
        {% endfor %}
    {% else %}
        <p class="no-notices">No notices found.</p>
    {% endif %}
</div>
{% endblock %}





from flask import Flask, render_template, request, redirect, url_for, flash, session
from datetime import datetime, timedelta
import time
import threading
from collections import deque

app = Flask(__name__)
app.secret_key = 'college_notice_board_secret_2025'
app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(hours=2)

# In-memory storage
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
    
    # Find and remove the notice
    for notice in notices:
        if notice['id'] == notice_id:
            # Check if admin has permission to delete this notice
            if session['department'] == 'ALL' or notice['department'] == session['department']:
                notices.remove(notice)
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

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)




    * {
    margin: 0;
    padding: 0;
    box-sizing: border-box;
}

body {
    font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
    line-height: 1.6;
    color: #333;
    background-color: #f4f4f4;
}

.container {
    max-width: 1200px;
    margin: 0 auto;
    padding: 0 20px;
}

.header {
    background: linear-gradient(135deg, #2c3e50, #3498db);
    color: white;
    padding: 2rem 0;
    text-align: center;
    border-radius: 0 0 10px 10px;
}

.header h1 {
    margin-bottom: 0.5rem;
    font-size: 2.5rem;
}

.user-info {
    margin-top: 1rem;
    font-size: 1.1rem;
}

.navbar {
    background: #34495e;
    padding: 1rem 0;
    margin-bottom: 2rem;
}

.navbar a {
    color: white;
    text-decoration: none;
    margin: 0 1rem;
    padding: 0.5rem 1rem;
    border-radius: 5px;
    transition: background 0.3s;
}

.navbar a:hover {
    background: #3498db;
}

.flash-message {
    padding: 1rem;
    margin: 1rem 0;
    border-radius: 5px;
    border-left: 4px solid;
}

.flash-message.success {
    background: #d4edda;
    border-color: #28a745;
    color: #155724;
}

.flash-message.error {
    background: #f8d7da;
    border-color: #dc3545;
    color: #721c24;
}

.flash-message.info {
    background: #d1ecf1;
    border-color: #17a2b8;
    color: #0c5460;
}

.btn {
    display: inline-block;
    padding: 0.5rem 1rem;
    border: none;
    border-radius: 5px;
    text-decoration: none;
    cursor: pointer;
    font-size: 1rem;
    transition: all 0.3s;
}

.btn-primary {
    background: #3498db;
    color: white;
}

.btn-primary:hover {
    background: #2980b9;
}

.btn-secondary {
    background: #95a5a6;
    color: white;
}

.btn-secondary:hover {
    background: #7f8c8d;
}

.btn-danger {
    background: #e74c3c;
    color: white;
}

.btn-danger:hover {
    background: #c0392b;
}

.btn-small {
    padding: 0.25rem 0.5rem;
    font-size: 0.875rem;
}

.form-container {
    max-width: 600px;
    margin: 0 auto;
    background: white;
    padding: 2rem;
    border-radius: 10px;
    box-shadow: 0 2px 10px rgba(0,0,0,0.1);
}

.form-group {
    margin-bottom: 1rem;
}

.form-group label {
    display: block;
    margin-bottom: 0.5rem;
    font-weight: bold;
}

.form-group input,
.form-group select,
.form-group textarea {
    width: 100%;
    padding: 0.5rem;
    border: 1px solid #ddd;
    border-radius: 5px;
    font-size: 1rem;
}

.form-row {
    display: flex;
    gap: 1rem;
}

.form-row .form-group {
    flex: 1;
}

.form-actions {
    display: flex;
    gap: 1rem;
    justify-content: flex-end;
    margin-top: 1.5rem;
}

.search-form {
    background: white;
    padding: 1.5rem;
    border-radius: 10px;
    margin-bottom: 2rem;
    box-shadow: 0 2px 5px rgba(0,0,0,0.1);
}

.notice-card {
    background: white;
    padding: 1.5rem;
    margin-bottom: 1rem;
    border-radius: 8px;
    box-shadow: 0 2px 5px rgba(0,0,0,0.1);
    border-left: 4px solid #3498db;
}

.high-priority {
    border-left-color: #e74c3c;
    background: #ffeaea;
}

.medium-priority {
    border-left-color: #f39c12;
}

.emergency-type {
    border: 2px solid #e74c3c;
    background: #fff3cd;
}

.notice-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 1rem;
}

.notice-header h4 {
    color: #2c3e50;
    margin: 0;
}

.notice-badge {
    padding: 0.25rem 0.5rem;
    border-radius: 15px;
    font-size: 0.875rem;
    font-weight: bold;
}

.notice-badge.emergency {
    background: #e74c3c;
    color: white;
}

.notice-badge.event {
    background: #3498db;
    color: white;
}

.notice-badge.exam {
    background: #9b59b6;
    color: white;
}

.notice-content {
    margin-bottom: 1rem;
    line-height: 1.6;
}

.notice-meta {
    display: flex;
    flex-wrap: wrap;
    gap: 1rem;
    font-size: 0.875rem;
    color: #666;
}

.notice-meta span {
    background: #f8f9fa;
    padding: 0.25rem 0.5rem;
    border-radius: 3px;
}

.stats-container {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
    gap: 1rem;
    margin-bottom: 2rem;
}

.stat-card {
    background: white;
    padding: 1.5rem;
    border-radius: 8px;
    text-align: center;
    box-shadow: 0 2px 5px rgba(0,0,0,0.1);
}

.stat-card h3 {
    font-size: 2.5rem;
    color: #3498db;
    margin-bottom: 0.5rem;
}

.hero-section {
    text-align: center;
    padding: 3rem 0;
    background: white;
    border-radius: 10px;
    margin-bottom: 2rem;
}

.hero-section h2 {
    color: #2c3e50;
    margin-bottom: 1rem;
}

.login-prompt {
    text-align: center;
    padding: 2rem;
    background: white;
    border-radius: 10px;
}

.demo-accounts {
    margin-top: 2rem;
    padding: 1rem;
    background: #f8f9fa;
    border-radius: 5px;
    text-align: left;
}

.new-notices-alert {
    background: #d4edda;
    color: #155724;
    padding: 1rem;
    border-radius: 5px;
    margin: 1rem 0;
    text-align: center;
    font-weight: bold;
}

.refresh-info {
    text-align: center;
    margin-top: 2rem;
    color: #666;
}

.footer {
    text-align: center;
    padding: 2rem 0;
    margin-top: 3rem;
    color: #666;
    border-top: 1px solid #ddd;
}

@media (max-width: 768px) {
    .form-row {
        flex-direction: column;
    }
    
    .notice-header {
        flex-direction: column;
        align-items: flex-start;
        gap: 1rem;
    }
    
    .notice-meta {
        flex-direction: column;
        gap: 0.5rem;
    }
    
    .navbar a {
        display: block;
        margin: 0.5rem 0;
    }
    
    .header h1 {
        font-size: 2rem;
    }
}








# from flask import Flask, render_template, request, redirect, url_for, flash, session
# from flask_sqlalchemy import SQLAlchemy
# from datetime import datetime, timedelta
# import time
# import threading
# from collections import deque
# import os

# app = Flask(__name__)
# app.secret_key = 'college_notice_board_secret_2025'
# app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(hours=2)

# # Database configuration
# basedir = os.path.abspath(os.path.dirname(__file__))
# app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + os.path.join(basedir, 'notice_board.db')
# app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# db = SQLAlchemy(app)

# # Database Models
# class User(db.Model):
#     id = db.Column(db.Integer, primary_key=True)
#     username = db.Column(db.String(80), unique=True, nullable=False)
#     password = db.Column(db.String(80), nullable=False)
#     role = db.Column(db.String(20), nullable=False)
#     name = db.Column(db.String(100), nullable=False)
#     department = db.Column(db.String(50), nullable=False)
#     year = db.Column(db.String(10), nullable=True)

# class Notice(db.Model):
#     id = db.Column(db.Integer, primary_key=True)
#     title = db.Column(db.String(200), nullable=False)
#     content = db.Column(db.Text, nullable=False)
#     department = db.Column(db.String(50), nullable=False)
#     type = db.Column(db.String(50), nullable=False)
#     priority = db.Column(db.String(20), nullable=False)
#     author = db.Column(db.String(80), nullable=False)
#     author_name = db.Column(db.String(100), nullable=False)
#     timestamp = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
#     expiry = db.Column(db.DateTime, nullable=False)

# # In-memory storage (for backward compatibility)
# notices = deque(maxlen=100)
# users = {
#     # Admin Accounts
#     'admin': {'password': 'admin123', 'role': 'admin', 'name': 'College Admin', 'department': 'ALL'},
    
#     # HOD Accounts
#     'hod_cse': {'password': 'hod123', 'role': 'admin', 'name': 'HOD CSE', 'department': 'CSE'},
#     'hod_ece': {'password': 'hod123', 'role': 'admin', 'name': 'HOD ECE', 'department': 'ECE'},
#     'hod_eee': {'password': 'hod123', 'role': 'admin', 'name': 'HOD EEE', 'department': 'EEE'},
#     'hod_mech': {'password': 'hod123', 'role': 'admin', 'name': 'HOD MECH', 'department': 'MECH'},
#     'hod_civil': {'password': 'hod123', 'role': 'admin', 'name': 'HOD CIVIL', 'department': 'CIVIL'},
#     'hod_aids': {'password': 'hod123', 'role': 'admin', 'name': 'HOD AIDS', 'department': 'AIDS'},
#     'hod_it': {'password': 'hod123', 'role': 'admin', 'name': 'HOD IT', 'department': 'IT'},
    
#     # Student Accounts
#     'student1': {'password': 'student123', 'role': 'student', 'name': 'Shivaani', 'department': 'CSE', 'year': 'III'},
#     'student2': {'password': 'student123', 'role': 'student', 'name': 'Priya', 'department': 'ECE', 'year': 'II'},
#     'student3': {'password': 'student123', 'role': 'student', 'name': 'Pooja', 'department': 'EEE', 'year': 'IV'},
#     'student4': {'password': 'student123', 'role': 'student', 'name': 'Abi', 'department': 'MECH', 'year': 'III'},
#     'student5': {'password': 'student123', 'role': 'student', 'name': 'Anjali Singh', 'department': 'CIVIL', 'year': 'II'},
#     'student6': {'password': 'student123', 'role': 'student', 'name': 'Vikram Raj', 'department': 'AIDS', 'year': 'III'},
#     'student7': {'password': 'student123', 'role': 'student', 'name': 'Divya', 'department': 'IT', 'year': 'II'}
# }

# # Departments with AIDS and IT
# departments = ['ALL', 'CSE', 'ECE', 'EEE', 'MECH', 'CIVIL', 'AIDS', 'IT']
# notice_types = ['General', 'Academic', 'Event', 'Emergency', 'Placement', 'Exam']

# # Clear any existing notices
# notices.clear()

# def get_current_time():
#     """Get current time as timezone-naive datetime"""
#     return datetime.now().replace(microsecond=0)

# def make_timezone_naive(dt):
#     """Convert datetime to timezone-naive if it's timezone-aware"""
#     if dt.tzinfo is not None:
#         return dt.replace(tzinfo=None)
#     return dt

# def safe_datetime_compare(dt1, dt2):
#     """Safely compare two datetimes, making them both timezone-naive"""
#     dt1_naive = make_timezone_naive(dt1)
#     dt2_naive = make_timezone_naive(dt2)
#     return dt1_naive, dt2_naive

# # Add sample notices with current dates
# sample_notices = [
#     {
#         'id': 1,
#         'title': 'SIH 2025 Internal Registration Started',
#         'content': 'Smart India Hackathon 2025 internal registration portal is now open. Last date: 15th December 2024.',
#         'department': 'ALL',
#         'type': 'Event',
#         'priority': 'High',
#         'author': 'admin',
#         'author_name': 'College Admin',
#         'timestamp': get_current_time() - timedelta(days=1),
#         'expiry': get_current_time() + timedelta(days=20)
#     },
#     {
#         'id': 2,
#         'title': 'End Semester Exams Schedule',
#         'content': 'End semester examinations for odd semester 2024-25 will commence from December 10th, 2024.',
#         'department': 'ALL',
#         'type': 'Exam',
#         'priority': 'High',
#         'author': 'admin',
#         'author_name': 'College Admin',
#         'timestamp': get_current_time() - timedelta(days=2),
#         'expiry': get_current_time() + timedelta(days=15)
#     },
#     {
#         'id': 3,
#         'title': 'CSE Department Lab Maintenance',
#         'content': 'Computer Lab 1 will be closed for maintenance on 30th November 2024.',
#         'department': 'CSE',
#         'type': 'General',
#         'priority': 'Medium',
#         'author': 'hod_cse',
#         'author_name': 'HOD CSE',
#         'timestamp': get_current_time() - timedelta(hours=5),
#         'expiry': get_current_time() + timedelta(days=5)
#     },
#     {
#         'id': 4,
#         'title': 'ECE Workshop on IoT',
#         'content': 'Two-day workshop on Internet of Things for ECE students on 5th-6th December 2024.',
#         'department': 'ECE',
#         'type': 'Event',
#         'priority': 'Medium',
#         'author': 'hod_ece',
#         'author_name': 'HOD ECE',
#         'timestamp': get_current_time() - timedelta(days=1),
#         'expiry': get_current_time() + timedelta(days=10)
#     },
#     {
#         'id': 5,
#         'title': 'AIDS AI/ML Workshop',
#         'content': 'Hands-on workshop on Artificial Intelligence and Machine Learning for AIDS students.',
#         'department': 'AIDS',
#         'type': 'Academic',
#         'priority': 'High',
#         'author': 'hod_aids',
#         'author_name': 'HOD AIDS',
#         'timestamp': get_current_time() - timedelta(hours=3),
#         'expiry': get_current_time() + timedelta(days=25)
#     },
#     {
#         'id': 6,
#         'title': 'IT Department Hackathon',
#         'content': 'Annual coding hackathon for IT students on 15th December 2024.',
#         'department': 'IT',
#         'type': 'Event',
#         'priority': 'Medium',
#         'author': 'hod_it',
#         'author_name': 'HOD IT',
#         'timestamp': get_current_time() - timedelta(hours=8),
#         'expiry': get_current_time() + timedelta(days=18)
#     }
# ]

# # Add sample notices to the deque
# for notice in sample_notices:
#     notices.append(notice)

# notice_counter = 7

# def can_delete_notice(notice, user_department):
#     """Check if user can delete the notice"""
#     if user_department == 'ALL':
#         return True  # Main admin can delete any notice
#     return notice['department'] == user_department  # HOD can only delete their department notices

# def cleanup_expired_notices():
#     """Background thread to remove expired notices"""
#     while True:
#         current_time = get_current_time()
#         valid_notices = deque(maxlen=100)
#         for notice in notices:
#             # Ensure both are timezone-naive for comparison
#             expiry_naive = make_timezone_naive(notice['expiry'])
#             if expiry_naive > current_time:
#                 valid_notices.append(notice)
        
#         notices.clear()
#         notices.extend(valid_notices)
#         time.sleep(3600)  # Check every hour

# # Start cleanup thread
# cleanup_thread = threading.Thread(target=cleanup_expired_notices, daemon=True)
# cleanup_thread.start()

# # Initialize database with sample data
# def init_db():
#     with app.app_context():
#         # Drop all tables and recreate them to ensure clean schema
#         db.drop_all()
#         db.create_all()
        
#         # Add users to database
#         for username, user_data in users.items():
#             user = User(
#                 username=username,
#                 password=user_data['password'],
#                 role=user_data['role'],
#                 name=user_data['name'],
#                 department=user_data['department'],
#                 year=user_data.get('year')
#             )
#             db.session.add(user)
        
#         # Add notices to database
#         for notice_data in sample_notices:
#             notice = Notice(
#                 id=notice_data['id'],
#                 title=notice_data['title'],
#                 content=notice_data['content'],
#                 department=notice_data['department'],
#                 type=notice_data['type'],
#                 priority=notice_data['priority'],
#                 author=notice_data['author'],
#                 author_name=notice_data['author_name'],
#                 timestamp=notice_data['timestamp'],
#                 expiry=notice_data['expiry']
#             )
#             db.session.add(notice)
        
#         db.session.commit()
#         print("Database initialized successfully!")

# # Initialize database
# init_db()

# @app.route('/')
# def index():
#     """Public notice board - shows recent notices from ALL departments"""
#     # Show all recent notices (not just ALL department)
#     recent_notices = list(notices)[-5:]  # Last 5 notices regardless of department
#     return render_template('index.html', notices=recent_notices)

# @app.route('/login', methods=['GET', 'POST'])
# def login():
#     if request.method == 'POST':
#         username = request.form['username']
#         password = request.form['password']
        
#         if username in users and users[username]['password'] == password:
#             session.permanent = True
#             session['user'] = username
#             session['role'] = users[username]['role']
#             session['name'] = users[username]['name']
#             session['department'] = users[username]['department']
#             flash('Login successful!', 'success')
            
#             if users[username]['role'] == 'admin':
#                 return redirect(url_for('admin_dashboard'))
#             else:
#                 return redirect(url_for('student_dashboard'))
#         else:
#             flash('Invalid username or password!', 'error')
    
#     return render_template('login.html')

# @app.route('/student/dashboard')
# def student_dashboard():
#     if 'user' not in session or session['role'] != 'student':
#         return redirect(url_for('login'))
    
#     # Get ALL notices for students (no department filtering)
#     relevant_notices = list(notices)
    
#     # Check for new notices since last visit
#     last_visit = session.get('last_visit')
#     if last_visit is None:
#         last_visit = datetime.min.replace(tzinfo=None)  # Make it timezone-naive
#     else:
#         last_visit = make_timezone_naive(last_visit)
    
#     # Ensure both datetimes are timezone-naive for comparison
#     new_notices = []
#     for notice in relevant_notices:
#         notice_time = make_timezone_naive(notice['timestamp'])
#         if notice_time > last_visit:
#             new_notices.append(notice)
    
#     # Update last visit time (timezone-naive)
#     session['last_visit'] = get_current_time()
    
#     return render_template('student_dashboard.html',
#                          student=users[session['user']],
#                          notices=relevant_notices[-10:],  # Last 10 notices from all departments
#                          new_notices_count=len(new_notices),
#                          current_time=get_current_time())

# @app.route('/admin/dashboard')
# def admin_dashboard():
#     if 'user' not in session or session['role'] != 'admin':
#         return redirect(url_for('login'))
    
#     admin_dept = session['department']
    
#     # Get ALL notices for admin (no department filtering)
#     admin_notices = list(notices)
    
#     # Statistics - ensure timezone-naive comparison
#     current_time = get_current_time()
#     total_notices = len(admin_notices)
#     active_notices = len([n for n in admin_notices if make_timezone_naive(n['expiry']) > current_time])
#     emergency_notices = len([n for n in admin_notices if n['type'] == 'Emergency'])
    
#     # Notices by type
#     notices_by_type = {}
#     for notice_type in notice_types:
#         notices_by_type[notice_type] = len([n for n in admin_notices if n['type'] == notice_type])
    
#     return render_template('admin_dashboard.html',
#                          admin=users[session['user']],
#                          notices=admin_notices[-15:],  # Last 15 notices from all departments
#                          total_notices=total_notices,
#                          active_notices=active_notices,
#                          emergency_notices=emergency_notices,
#                          notices_by_type=notices_by_type,
#                          departments=departments,
#                          notice_types=notice_types,
#                          current_time=current_time,
#                          can_delete_notice=can_delete_notice)

# @app.route('/create_notice', methods=['GET', 'POST'])
# def create_notice():
#     if 'user' not in session or session['role'] != 'admin':
#         return redirect(url_for('login'))
    
#     if request.method == 'POST':
#         global notice_counter
        
#         title = request.form['title']
#         content = request.form['content']
        
#         # Determine department based on user role
#         if session['department'] == 'ALL':
#             # Main admin can choose department
#             department = request.form['department']
#         else:
#             # HOD can only use their own department
#             department = session['department']
            
#         notice_type = request.form['type']
#         priority = request.form['priority']
#         expiry_days = int(request.form['expiry_days'])
        
#         new_notice = {
#             'id': notice_counter,
#             'title': title,
#             'content': content,
#             'department': department,
#             'type': notice_type,
#             'priority': priority,
#             'author': session['user'],
#             'author_name': session['name'],
#             'timestamp': get_current_time(),
#             'expiry': get_current_time() + timedelta(days=expiry_days)
#         }
        
#         notices.append(new_notice)
        
#         # Also save to database
#         db_notice = Notice(
#             id=notice_counter,
#             title=title,
#             content=content,
#             department=department,
#             type=notice_type,
#             priority=priority,
#             author=session['user'],
#             author_name=session['name'],
#             timestamp=get_current_time(),
#             expiry=get_current_time() + timedelta(days=expiry_days)
#         )
#         db.session.add(db_notice)
#         db.session.commit()
        
#         notice_counter += 1
        
#         flash('Notice published successfully!', 'success')
#         return redirect(url_for('admin_dashboard'))
    
#     # Get available departments based on user role
#     available_departments = []
#     if session['department'] == 'ALL':
#         # Main admin can see all departments
#         available_departments = departments
#     else:
#         # HOD can only see their own department
#         available_departments = [session['department']]
    
#     return render_template('create_notice.html',
#                          departments=available_departments,
#                          notice_types=notice_types,
#                          user_department=session['department'])

# @app.route('/delete_notice/<int:notice_id>')
# def delete_notice(notice_id):
#     if 'user' not in session or session['role'] != 'admin':
#         return redirect(url_for('login'))
    
#     # Find and remove the notice from memory
#     for notice in notices:
#         if notice['id'] == notice_id:
#             # Check if admin has permission to delete this notice
#             if session['department'] == 'ALL' or notice['department'] == session['department']:
#                 notices.remove(notice)
                
#                 # Also delete from database
#                 db_notice = Notice.query.get(notice_id)
#                 if db_notice:
#                     db.session.delete(db_notice)
#                     db.session.commit()
                
#                 flash('Notice deleted successfully!', 'success')
#                 break
#             else:
#                 flash('You can only delete notices from your department!', 'error')
#                 break
#     else:
#         flash('Notice not found!', 'error')
    
#     return redirect(url_for('admin_dashboard'))

# @app.route('/search_notices', methods=['POST'])
# def search_notices():
#     if 'user' not in session:
#         return redirect(url_for('login'))
    
#     query = request.form['query'].lower()
#     department_filter = request.form.get('department', 'ALL')
#     type_filter = request.form.get('type', 'ALL')
    
#     filtered_notices = []
#     for notice in reversed(list(notices)):
#         # Apply filters
#         if department_filter != 'ALL' and notice['department'] != department_filter:
#             continue
#         if type_filter != 'ALL' and notice['type'] != type_filter:
#             continue
        
#         # Search in title and content
#         if (query in notice['title'].lower() or 
#             query in notice['content'].lower() or
#             query in notice['type'].lower()):
#             filtered_notices.append(notice)
    
#     if session['role'] == 'admin':
#         # For admin dashboard - show all notices
#         admin_notices = list(notices)
        
#         current_time = get_current_time()
#         total_notices = len(admin_notices)
#         active_notices = len([n for n in admin_notices if make_timezone_naive(n['expiry']) > current_time])
#         emergency_notices = len([n for n in admin_notices if n['type'] == 'Emergency'])
        
#         notices_by_type = {}
#         for notice_type in notice_types:
#             notices_by_type[notice_type] = len([n for n in admin_notices if n['type'] == notice_type])
        
#         return render_template('admin_dashboard.html',
#                              admin=users[session['user']],
#                              notices=filtered_notices,
#                              total_notices=total_notices,
#                              active_notices=active_notices,
#                              emergency_notices=emergency_notices,
#                              notices_by_type=notices_by_type,
#                              departments=departments,
#                              notice_types=notice_types,
#                              current_time=current_time,
#                              search_query=query,
#                              can_delete_notice=can_delete_notice)
#     else:
#         # For student dashboard - show all notices
#         last_visit = session.get('last_visit')
#         if last_visit is None:
#             last_visit = datetime.min.replace(tzinfo=None)
#         else:
#             last_visit = make_timezone_naive(last_visit)
        
#         # Ensure both datetimes are timezone-naive for comparison
#         new_notices = []
#         for notice in filtered_notices:
#             notice_time = make_timezone_naive(notice['timestamp'])
#             if notice_time > last_visit:
#                 new_notices.append(notice)
        
#         return render_template('student_dashboard.html',
#                              student=users[session['user']],
#                              notices=filtered_notices,
#                              new_notices_count=len(new_notices),
#                              current_time=get_current_time(),
#                              search_query=query)

# @app.route('/logout')
# def logout():
#     session.clear()
#     flash('You have been logged out successfully!', 'info')
#     return redirect(url_for('index'))

# if __name__ == '__main__':
#     app.run(debug=True, host='0.0.0.0', port=5000)





admin dashboard{% extends "base.html" %}

{% block content %}
<div class="dashboard-header">
    <h2>Admin Dashboard</h2>
    <p>Welcome, {{ admin.name }} | Department: {{ admin.department }}</p>
</div>

<div class="stats-container">
    <div class="stat-card">
        <h3>{{ total_notices }}</h3>
        <p>Total Notices</p>
    </div>
    <div class="stat-card">
        <h3>{{ active_notices }}</h3>
        <p>Active Notices</p>
    </div>
    <div class="stat-card">
        <h3>{{ emergency_notices }}</h3>
        <p>Emergency</p>
    </div>
</div>

<form method="POST" action="{{ url_for('search_notices') }}" class="search-form">
    <div class="form-row">
        <input type="text" name="query" placeholder="Search notices..." value="{{ search_query or '' }}">
        <select name="department">
            <option value="ALL">All Departments</option>
            {% for dept in departments %}
            <option value="{{ dept }}">{{ dept }}</option>
            {% endfor %}
        </select>
        <select name="type">
            <option value="ALL">All Types</option>
            {% for type in notice_types %}
            <option value="{{ type }}">{{ type }}</option>
            {% endfor %}
        </select>
        <button type="submit" class="btn btn-secondary">Search</button>
    </div>
</form>

<div class="notices-section">
    <h3>Recent Notices</h3>
    
    {% if notices %}
        {% for notice in notices %}
        <div class="notice-card {{ notice.priority|lower }}-priority admin-notice">
            <div class="notice-header">
                <h4>{{ notice.title }}</h4>
                <div>
                    <span class="notice-badge {{ notice.type|lower }}">{{ notice.type }}</span>
                    {% if can_delete_notice(notice, admin.department) %}
                    <a href="{{ url_for('delete_notice', notice_id=notice.id) }}" 
                       class="btn btn-danger btn-small" 
                       onclick="return confirm('Delete this notice?')">Delete</a>
                    {% endif %}
                </div>
            </div>
            <p class="notice-content">{{ notice.content }}</p>
            <div class="notice-meta">
                <span><strong>Department:</strong> {{ notice.department }}</span>
                <span><strong>Priority:</strong> {{ notice.priority }}</span>
                <span><strong>Author:</strong> {{ notice.author_name }}</span>
                <span><strong>Published:</strong> {{ notice.timestamp.strftime('%d-%m-%Y %H:%M') }}</span>
                <span><strong>Expires:</strong> {{ notice.expiry.strftime('%d-%m-%Y %H:%M') }}</span>
            </div>
        </div>
        {% endfor %}
    {% else %}
        <p class="no-notices">No notices found.</p>
    {% endif %}
</div>
{% endblock %}
