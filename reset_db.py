from app import db, app, User, Employee
from datetime import datetime

def reset_database():
    with app.app_context():
        # Drop all tables
        db.drop_all()
        
        # Create all tables
        db.create_all()
        
        # Create default admin user
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

        # Create default HR user
        hr_user = User(username='hr', role='hr')
        hr_user.set_password('hr123')
        db.session.add(hr_user)
        db.session.flush()  # Get the user ID

        # Create HR employee record
        hr_employee = Employee(
            name='HR Manager',
            department='Human Resources',
            position='HR Manager',
            salary=60000,
            user_id=hr_user.id
        )
        db.session.add(hr_employee)
        
        # Commit all changes
        db.session.commit()
        
        print("Database reset successfully!")
        print("Default users created:")
        print("Admin - Username: admin, Password: admin123")
        print("HR - Username: hr, Password: hr123")

if __name__ == '__main__':
    reset_database() 