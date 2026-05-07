import os, sys
sys.path.insert(0, r'C:\Users\Latif\Desktop\SchoolDiag')
os.chdir(r'C:\Users\Latif\Desktop\SchoolDiag')
from app import create_app
from models import db, User, Subject

app = create_app()
with app.app_context():
    # Add/update teacher
    t = User.query.filter_by(username='teacher1').first()
    if not t:
        t = User(username='teacher1', full_name='Иванова Марина Петровна', role='teacher')
        db.session.add(t)
    t.set_password('1234')
    t.is_active = True
    db.session.commit()
    print('Teacher password ok:', t.check_password('1234'))

    # Add subjects if missing
    if Subject.query.count() == 0:
        subjects = [
            ('Математика', '📐', 1),
            ('Логика', '🧠', 2),
            ('Русский язык', '🇷🇺', 3),
            ('Таджикский язык', '🇹🇯', 4),
            ('Английский язык', '🇬🇧', 5),
        ]
        for name, icon, order in subjects:
            db.session.add(Subject(name_ru=name, icon=icon, order=order))
        db.session.commit()
        print('Subjects added')

    print('All users:')
    for u in User.query.all():
        pwd_ok = u.check_password('1234')
        print(f'  {u.username} | role={u.role} | active={u.is_active} | pwd_1234={pwd_ok}')
