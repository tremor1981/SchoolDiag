from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_required, current_user
from functools import wraps
from models import db, User, Subject, Question, Student, TestSession, Answer

admin_bp = Blueprint('admin', __name__)


def admin_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if not current_user.is_authenticated or not current_user.is_admin():
            flash('Доступ запрещён', 'error')
            return redirect(url_for('auth.login'))
        return f(*args, **kwargs)
    return decorated


@admin_bp.route('/')
@login_required
@admin_required
def dashboard():
    total_students = Student.query.count()
    total_sessions = TestSession.query.filter_by(status='completed').count()
    total_teachers = User.query.filter_by(role='teacher').count()
    total_questions = Question.query.count()
    recent_sessions = (TestSession.query.filter_by(status='completed')
                       .order_by(TestSession.completed_at.desc()).limit(10).all())
    return render_template('admin/dashboard.html',
                           total_students=total_students,
                           total_sessions=total_sessions,
                           total_teachers=total_teachers,
                           total_questions=total_questions,
                           recent_sessions=recent_sessions)


@admin_bp.route('/questions')
@login_required
@admin_required
def questions():
    subjects = Subject.query.order_by(Subject.order).all()
    return render_template('admin/questions.html', subjects=subjects)


@admin_bp.route('/questions/add', methods=['POST'])
@login_required
@admin_required
def add_question():
    subject_id = request.form.get('subject_id')
    text = request.form.get('text', '').strip()
    description = request.form.get('description', '').strip()
    if not text or not subject_id:
        flash('Заполните все поля', 'error')
        return redirect(url_for('admin.questions'))
    max_order = (db.session.query(db.func.max(Question.order))
                 .filter_by(subject_id=subject_id).scalar() or 0)
    q = Question(subject_id=subject_id, text=text,
                 description=description or None, order=max_order + 1)
    db.session.add(q)
    db.session.commit()
    flash('Вопрос добавлен', 'success')
    return redirect(url_for('admin.questions'))


@admin_bp.route('/questions/<int:q_id>/delete', methods=['POST'])
@login_required
@admin_required
def delete_question(q_id):
    q = Question.query.get_or_404(q_id)
    # Delete linked answers first, then the question
    Answer.query.filter_by(question_id=q_id).delete()
    db.session.delete(q)
    db.session.commit()
    flash('Вопрос удалён', 'success')
    return redirect(url_for('admin.questions'))



@admin_bp.route('/teachers')
@login_required
@admin_required
def teachers():
    all_teachers = User.query.filter_by(role='teacher').order_by(User.created_at.desc()).all()
    return render_template('admin/teachers.html', teachers=all_teachers)


@admin_bp.route('/teachers/add', methods=['POST'])
@login_required
@admin_required
def add_teacher():
    username = request.form.get('username', '').strip()
    full_name = request.form.get('full_name', '').strip()
    password = request.form.get('password', '')
    if not username or not full_name or not password:
        flash('Заполните все поля', 'error')
        return redirect(url_for('admin.teachers'))
    if User.query.filter_by(username=username).first():
        flash('Логин уже занят', 'error')
        return redirect(url_for('admin.teachers'))
    t = User(username=username, full_name=full_name, role='teacher')
    t.set_password(password)
    db.session.add(t)
    db.session.commit()
    flash(f'Учитель «{full_name}» добавлен', 'success')
    return redirect(url_for('admin.teachers'))


@admin_bp.route('/teachers/<int:tid>/toggle', methods=['POST'])
@login_required
@admin_required
def toggle_teacher(tid):
    t = User.query.get_or_404(tid)
    t.is_active = not t.is_active
    db.session.commit()
    flash(f'Учитель {t.full_name} {"активирован" if t.is_active else "деактивирован"}', 'success')
    return redirect(url_for('admin.teachers'))


@admin_bp.route('/teachers/<int:tid>/reset-password', methods=['POST'])
@login_required
@admin_required
def reset_password(tid):
    t = User.query.get_or_404(tid)
    pwd = request.form.get('new_password', '')
    if not pwd:
        flash('Введите новый пароль', 'error')
        return redirect(url_for('admin.teachers'))
    t.set_password(pwd)
    db.session.commit()
    flash(f'Пароль для {t.full_name} обновлён', 'success')
    return redirect(url_for('admin.teachers'))


@admin_bp.route('/results')
@login_required
@admin_required
def results():
    sessions = (TestSession.query.filter_by(status='completed')
                .order_by(TestSession.completed_at.desc()).all())
    return render_template('admin/results.html', sessions=sessions)


@admin_bp.route('/results/<int:sid>')
@login_required
@admin_required
def result_detail(sid):
    session = TestSession.query.get_or_404(sid)
    subjects = Subject.query.order_by(Subject.order).all()
    return render_template('admin/result_detail.html', session=session, subjects=subjects)


@admin_bp.route('/export/students')
@login_required
@admin_required
def export_students():
    from export import export_by_students
    return export_by_students()


@admin_bp.route('/export/teachers')
@login_required
@admin_required
def export_teachers():
    from export import export_by_teachers
    return export_by_teachers()

@admin_bp.route('/export/report')
@login_required
@admin_required
def export_report():
    from export import export_print_report
    return export_print_report()
