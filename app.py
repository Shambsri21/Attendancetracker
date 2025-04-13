from flask import Flask, render_template, request, redirect, url_for, flash, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime, date, timedelta
import os
from dotenv import load_dotenv
from sqlalchemy import func, and_, or_

# Load environment variables
load_dotenv()

app = Flask(__name__)
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'your-secret-key')
app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('DATABASE_URL', 'mysql://root:root@localhost/employee_management')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

# Models
class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    role = db.Column(db.String(20), nullable=False)  # admin, hr, employee
    employee = db.relationship('Employee', backref='user', uselist=False, cascade='all, delete-orphan')

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

class Employee(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    department = db.Column(db.String(50), nullable=False)
    position = db.Column(db.String(50), nullable=False)
    salary = db.Column(db.Float, nullable=False)
    hire_date = db.Column(db.DateTime, default=datetime.utcnow)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id', ondelete='CASCADE'), unique=True)
    attendance = db.relationship('Attendance', backref='employee', lazy=True, cascade='all, delete-orphan')

    @property
    def is_present(self):
        today = date.today()
        return Attendance.query.filter(
            Attendance.employee_id == self.id,
            Attendance.date == today,
            Attendance.clock_out.is_(None)
        ).first() is not None

    @property
    def present_days(self):
        start_of_month = date.today().replace(day=1)
        return Attendance.query.filter(
            Attendance.employee_id == self.id,
            Attendance.date >= start_of_month
        ).count()

    @property
    def avg_hours(self):
        start_of_month = date.today().replace(day=1)
        records = Attendance.query.filter(
            Attendance.employee_id == self.id,
            Attendance.date >= start_of_month,
            Attendance.clock_out.isnot(None)
        ).all()
        
        if not records:
            return 0
            
        total_hours = sum(
            (record.clock_out - record.clock_in).total_seconds() / 3600
            for record in records
        )
        return round(total_hours / len(records), 2)

    @property
    def last_attendance(self):
        return Attendance.query.filter_by(
            employee_id=self.id
        ).order_by(Attendance.date.desc()).first()

    @property
    def recent_attendance(self):
        return Attendance.query.filter_by(
            employee_id=self.id
        ).order_by(Attendance.date.desc()).limit(5).all()

class Attendance(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    employee_id = db.Column(db.Integer, db.ForeignKey('employee.id'), nullable=False)
    clock_in = db.Column(db.DateTime, nullable=False)
    clock_out = db.Column(db.DateTime)
    date = db.Column(db.Date, nullable=False)

class Activity(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    type = db.Column(db.String(50), nullable=False)  # clock_in, clock_out, new_employee, update_employee, delete_employee
    message = db.Column(db.String(255), nullable=False)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    
    @classmethod
    def log(cls, type, message, user_id):
        activity = cls(type=type, message=message, user_id=user_id)
        db.session.add(activity)
        db.session.commit()

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# Routes
@app.route('/')
def index():
    return render_template('index.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        user = User.query.filter_by(username=username).first()
        
        if user and user.check_password(password):
            login_user(user)
            flash('Logged in successfully.', 'success')
            return redirect(url_for('dashboard'))
        flash('Invalid username or password', 'danger')
    return render_template('login.html')

@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        name = request.form.get('name')
        department = request.form.get('department')
        position = request.form.get('position')
        salary = float(request.form.get('salary'))

        # Check if username already exists
        if User.query.filter_by(username=username).first():
            flash('Username already exists. Please choose another.', 'danger')
            return redirect(url_for('signup'))

        try:
            # Create user with employee role only
            user = User(username=username, role='employee')
            user.set_password(password)
            db.session.add(user)
            db.session.flush()  # Get the user ID

            # Create employee record
            employee = Employee(
                name=name,
                department=department,
                position=position,
                salary=salary,
                user_id=user.id
            )
            db.session.add(employee)
            
            db.session.commit()
            flash('Account created successfully! Please login.', 'success')
            return redirect(url_for('login'))
        except Exception as e:
            db.session.rollback()
            flash('An error occurred while creating your account. Please try again.', 'danger')
            return redirect(url_for('signup'))

    return render_template('signup.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash('Logged out successfully.', 'success')
    return redirect(url_for('index'))

@app.route('/dashboard')
@login_required
def dashboard():
    # Get total employees
    total_employees = Employee.query.count()
    
    # Get present employees today
    today = datetime.now().date()
    present_today = Attendance.query.filter(
        db.func.date(Attendance.clock_in) == today,
        Attendance.clock_out.is_(None)
    ).count()
    
    # Get department distribution
    dept_counts = db.session.query(
        Employee.department,
        db.func.count(Employee.id).label('count')
    ).group_by(Employee.department).all()
    
    # Standardize department names (combine HR and Human Resources)
    dept_dict = {}
    for dept, count in dept_counts:
        # Standardize HR department names
        if dept.lower() in ['hr', 'human resources']:
            dept = 'Human Resources'
        dept_dict[dept] = dept_dict.get(dept, 0) + count
    
    department_labels = list(dept_dict.keys())
    department_data = list(dept_dict.values())
    
    # Get total departments (after standardization)
    total_departments = len(department_labels)
    
    # Calculate average salary
    avg_salary = db.session.query(db.func.avg(Employee.salary)).scalar() or 0
    
    # Get recent activities (last 10)
    recent_activities = Activity.query.order_by(Activity.timestamp.desc()).limit(10).all()
    
    return render_template('dashboard.html',
                         total_employees=total_employees,
                         present_today=present_today,
                         total_departments=total_departments,
                         avg_salary=avg_salary,
                         department_labels=department_labels,
                         department_data=department_data,
                         recent_activities=recent_activities)

@app.route('/employees')
@login_required
def employees():
    print("Current user role:", current_user.role)  # Debug log
    
    search = request.args.get('search', '')
    department = request.args.get('department', '')
    
    query = Employee.query
    
    if search:
        search_filter = or_(
            Employee.name.ilike(f'%{search}%'),
            Employee.department.ilike(f'%{search}%'),
            Employee.position.ilike(f'%{search}%')
        )
        query = query.filter(search_filter)
    
    if department:
        query = query.filter(Employee.department == department)
    
    employees = query.all()
    print("Number of employees found:", len(employees))  # Debug log
    for emp in employees:  # Debug log
        print(f"Employee: {emp.name}, Dept: {emp.department}, Position: {emp.position}")
    
    departments = db.session.query(Employee.department).distinct().all()
    departments = [d[0] for d in departments]
    print("Available departments:", departments)  # Debug log
    
    return render_template('employees.html', 
                         employees=employees,
                         departments=departments)

@app.route('/add_employee', methods=['GET', 'POST'])
@login_required
def add_employee():
    if current_user.role not in ['admin', 'hr']:
        flash('You do not have permission to add employees.', 'danger')
        return redirect(url_for('employees'))

    if request.method == 'POST':
        # Get form data
        name = request.form.get('name')
        department = request.form.get('department')
        # Standardize HR department name
        if department.lower() in ['hr', 'human resources']:
            department = 'Human Resources'
        position = request.form.get('position')
        salary = float(request.form.get('salary'))
        username = request.form.get('username')
        password = request.form.get('password')

        # Check if username already exists
        if User.query.filter_by(username=username).first():
            flash('Username already exists. Please choose another.', 'danger')
            return redirect(url_for('add_employee'))

        try:
            # Create user account
            user = User(username=username, role='employee')
            user.set_password(password)
            db.session.add(user)
            db.session.flush()  # Get the user ID

            # Create employee record
            employee = Employee(
                name=name,
                department=department,
                position=position,
                salary=salary,
                user_id=user.id
            )
            db.session.add(employee)
            
            # Log the activity
            Activity.log(
                type='new_employee',
                message=f'New employee {name} added to {department}',
                user_id=current_user.id
            )
            
            db.session.commit()
            flash('Employee added successfully!', 'success')
            return redirect(url_for('employees'))

        except Exception as e:
            db.session.rollback()
            flash('An error occurred while adding the employee. Please try again.', 'danger')
            return redirect(url_for('add_employee'))

    return render_template('add_employee.html')

@app.route('/add_hr', methods=['GET', 'POST'])
@login_required
def add_hr():
    # Check if user is admin
    if current_user.role != 'admin':
        flash('Only administrators can create HR accounts.', 'danger')
        return redirect(url_for('employees'))

    if request.method == 'POST':
        # Get form data
        name = request.form.get('name')
        username = request.form.get('username')
        password = request.form.get('password')
        salary = float(request.form.get('salary'))

        # Check if username already exists
        if User.query.filter_by(username=username).first():
            flash('Username already exists. Please choose another.', 'danger')
            return redirect(url_for('add_hr'))

        try:
            # Create HR user account
            hr_user = User(username=username, role='hr')
            hr_user.set_password(password)
            db.session.add(hr_user)
            db.session.flush()  # Get the user ID

            # Create HR employee record
            hr_employee = Employee(
                name=name,
                department='Human Resources',
                position='HR Manager',
                salary=salary,
                user_id=hr_user.id
            )
            db.session.add(hr_employee)
            db.session.commit()

            flash('HR account created successfully!', 'success')
            return redirect(url_for('employees'))

        except Exception as e:
            db.session.rollback()
            flash('An error occurred while creating the HR account. Please try again.', 'danger')
            return redirect(url_for('add_hr'))

    return render_template('add_hr.html')

@app.route('/edit_employee/<int:id>', methods=['GET', 'POST'])
@login_required
def edit_employee(id):
    # Check if user has permission to edit employees
    if current_user.role not in ['admin', 'hr']:
        flash('You do not have permission to edit employees.', 'danger')
        return redirect(url_for('employees'))

    employee = Employee.query.get_or_404(id)
    user = User.query.get(employee.user_id)

    if request.method == 'POST':
        try:
            # Update employee details
            employee.name = request.form.get('name')
            department = request.form.get('department')
            # Standardize HR department name
            if department.lower() in ['hr', 'human resources']:
                department = 'Human Resources'
            employee.department = department
            employee.position = request.form.get('position')
            employee.salary = float(request.form.get('salary'))

            # Update username if changed and not already taken
            new_username = request.form.get('username')
            if new_username != user.username:
                if User.query.filter_by(username=new_username).first():
                    flash('Username already exists. Please choose another.', 'danger')
                    return redirect(url_for('edit_employee', id=id))
                user.username = new_username

            # Update password if provided
            new_password = request.form.get('password')
            if new_password:
                user.set_password(new_password)

            # Log the activity
            Activity.log(
                type='update_employee',
                message=f'Employee {employee.name} updated',
                user_id=current_user.id
            )
            
            db.session.commit()
            flash('Employee updated successfully!', 'success')
            return redirect(url_for('employees'))

        except Exception as e:
            db.session.rollback()
            flash('An error occurred while updating the employee. Please try again.', 'danger')
            return redirect(url_for('edit_employee', id=id))

    return render_template('edit_employee.html', employee=employee, user=user)

@app.route('/delete_employee/<int:id>', methods=['POST'])
@login_required
def delete_employee(id):
    if current_user.role not in ['admin', 'hr']:
        flash('You do not have permission to delete employees.', 'danger')
        return redirect(url_for('employees'))

    try:
        employee = Employee.query.get_or_404(id)
        
        # Prevent deleting your own account
        if employee.user_id == current_user.id:
            flash('You cannot delete your own account.', 'danger')
            return redirect(url_for('employees'))

        # Store employee name for activity log
        employee_name = employee.name
        
        # Get the associated user
        user = User.query.get(employee.user_id)
        
        # Delete the user first (this will cascade delete the employee and attendance records)
        if user:
            db.session.delete(user)
        
        # Log the activity
        Activity.log(
            type='delete_employee',
            message=f'Employee {employee_name} deleted',
            user_id=current_user.id
        )
        
        db.session.commit()
        flash('Employee deleted successfully!', 'success')
        
    except Exception as e:
        print(f"Error deleting employee: {str(e)}")  # Add debug logging
        db.session.rollback()
        flash('An error occurred while deleting the employee. Please try again.', 'danger')
    
    return redirect(url_for('employees'))

@app.route('/attendance')
@login_required
def attendance():
    # Get current month for default filter
    today = date.today()
    selected_month = request.args.get('month', today.strftime('%Y-%m'))
    year, month = map(int, selected_month.split('-'))
    start_date = date(year, month, 1)
    if month == 12:
        end_date = date(year + 1, 1, 1)
    else:
        end_date = date(year, month + 1, 1)
    
    # Get current user's attendance status
    current_status = None
    employee = Employee.query.filter_by(user_id=current_user.id).first()
    if employee:
        current_status = Attendance.query.filter(
            Attendance.employee_id == employee.id,
            Attendance.date == today,
            Attendance.clock_out.is_(None)
        ).first()
    
    # Get attendance records for both employees and HR
    attendance_records = []
    if employee:
        attendance_records = Attendance.query.filter(
            Attendance.employee_id == employee.id,
            Attendance.date >= start_date,
            Attendance.date < end_date
        ).order_by(Attendance.date.desc()).all()
    
    # Get all employees' attendance for today (for admin/HR)
    today_all_records = []
    if current_user.role in ['admin', 'hr']:
        today_all_records = Attendance.query.filter(
            Attendance.date == today
        ).all()
    
    return render_template('attendance.html',
                         current_status=current_status,
                         attendance_records=attendance_records,
                         today_all_records=today_all_records,
                         selected_month=selected_month)

@app.route('/clock-in', methods=['POST'])
@login_required
def clock_in():
    if current_user.role not in ['employee', 'hr']:
        flash('Only employees and HR can clock in.', 'danger')
        return redirect(url_for('attendance'))
    
    employee = Employee.query.filter_by(user_id=current_user.id).first()
    if not employee:
        flash('Employee record not found.', 'danger')
        return redirect(url_for('attendance'))
    
    today = date.today()
    existing_record = Attendance.query.filter(
        Attendance.employee_id == employee.id,
        Attendance.date == today,
        Attendance.clock_out.is_(None)
    ).first()
    
    if existing_record:
        flash('You are already clocked in.', 'warning')
        return redirect(url_for('attendance'))
    
    attendance = Attendance(
        employee_id=employee.id,
        clock_in=datetime.now(),
        date=today
    )
    db.session.add(attendance)
    
    # Log the activity
    Activity.log(
        type='clock_in',
        message=f'{employee.name} clocked in',
        user_id=current_user.id
    )
    
    db.session.commit()
    flash('Clocked in successfully.', 'success')
    return redirect(url_for('attendance'))

@app.route('/clock-out', methods=['POST'])
@login_required
def clock_out():
    if current_user.role not in ['employee', 'hr']:
        flash('Only employees and HR can clock out.', 'danger')
        return redirect(url_for('attendance'))
    
    employee = Employee.query.filter_by(user_id=current_user.id).first()
    if not employee:
        flash('Employee record not found.', 'danger')
        return redirect(url_for('attendance'))
    
    today = date.today()
    current_record = Attendance.query.filter(
        Attendance.employee_id == employee.id,
        Attendance.date == today,
        Attendance.clock_out.is_(None)
    ).first()
    
    if not current_record:
        flash('No active clock-in record found.', 'warning')
        return redirect(url_for('attendance'))
    
    current_record.clock_out = datetime.now()
    
    # Log the activity
    Activity.log(
        type='clock_out',
        message=f'{employee.name} clocked out',
        user_id=current_user.id
    )
    
    db.session.commit()
    flash('Clocked out successfully.', 'success')
    return redirect(url_for('attendance'))

if __name__ == '__main__':
    with app.app_context():
        # Create tables if they don't exist
        db.create_all()
        
        # Create default admin user if not exists
        admin = User.query.filter_by(username='admin').first()
        if not admin:
            admin = User(username='admin', role='admin')
            admin.set_password('admin123')
            db.session.add(admin)
            db.session.flush()  # Get the user ID

            # Create admin employee record
            admin_employee = Employee(
                name='System Administrator',
                department='Administration',
                position='System Administrator',
                salary=80000,
                user_id=admin.id
            )
            db.session.add(admin_employee)
            db.session.commit()

        # Create default HR user if not exists
        hr_user = User.query.filter_by(username='hr').first()
        if not hr_user:
            hr_user = User(username='hr', role='hr')
            hr_user.set_password('hr123')
            
            # Create HR employee record
            hr_employee = Employee.query.filter_by(user_id=hr_user.id).first()
            if not hr_employee:
                hr_employee = Employee(
                    name='HR Manager',
                    department='Human Resources',
                    position='HR Manager',
                    salary=60000,
                    user_id=hr_user.id
                )
                db.session.add(hr_user)
                db.session.add(hr_employee)
                db.session.commit()
        
    app.run(debug=True) 