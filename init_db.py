"""Initialize database with default data."""
from app import create_app
from models import db, User, Subject

app = create_app()

with app.app_context():
    db.create_all()

    # Create admin if not exists
    if not User.query.filter_by(username='admin').first():
        admin = User(username='admin', full_name='Администратор', role='admin')
        admin.set_password('admin123')
        db.session.add(admin)
        print('Admin created: login=admin, password=admin123')

    # Create default subjects
    default_subjects = [
        ('Математика', '📐', 1),
        ('Логика', '🧠', 2),
        ('Русский язык', '🇷🇺', 3),
        ('Таджикский язык', '🇹🇯', 4),
        ('Английский язык', '🇬🇧', 5),
    ]
    for name, icon, order in default_subjects:
        if not Subject.query.filter_by(name_ru=name).first():
            db.session.add(Subject(name_ru=name, icon=icon, order=order))
            print(f'Subject created: {name}')

    # Demo teacher
    if not User.query.filter_by(username='teacher1').first():
        t = User(username='teacher1', full_name='Иванова Марина Петровна', role='teacher')
        t.set_password('teacher123')
        db.session.add(t)
        print('Demo teacher: login=teacher1, password=teacher123')

    db.session.commit()
    print('Database initialized successfully!')
