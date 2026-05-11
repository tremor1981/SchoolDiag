from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_required, current_user, logout_user
from functools import wraps
from sqlalchemy import or_
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
    total_students = (db.session.query(db.func.count(db.distinct(TestSession.student_id)))
                      .filter(TestSession.status == 'completed')
                      .scalar() or 0)
    total_sessions = TestSession.query.filter_by(status='completed').count()
    total_active_sessions = TestSession.query.filter_by(status='in_progress').count()
    total_teachers = User.query.filter_by(role='teacher', is_active=True).count()
    total_questions = Question.query.count()
    recent_sessions = (TestSession.query.filter_by(status='completed')
                       .order_by(TestSession.completed_at.desc()).limit(10).all())
    return render_template('admin/dashboard.html',
                           total_students=total_students,
                           total_sessions=total_sessions,
                           total_active_sessions=total_active_sessions,
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


@admin_bp.route('/teachers/<int:tid>/edit', methods=['POST'])
@login_required
@admin_required
def edit_teacher(tid):
    t = User.query.get_or_404(tid)
    username = request.form.get('username', '').strip()
    full_name = request.form.get('full_name', '').strip()
    if not username or not full_name:
        flash('Заполните все поля', 'error')
        return redirect(url_for('admin.teachers'))
    existing = User.query.filter_by(username=username).first()
    if existing and existing.id != tid:
        flash('Этот логин уже используется другим пользователем', 'error')
        return redirect(url_for('admin.teachers'))
    t.username = username
    t.full_name = full_name
    db.session.commit()
    flash(f'Данные учителя «{full_name}» обновлены', 'success')
    return redirect(url_for('admin.teachers'))


@admin_bp.route('/teachers/<int:tid>/delete', methods=['POST'])
@login_required
@admin_required
def delete_teacher(tid):
    t = User.query.get_or_404(tid)
    if t.id == current_user.id:
        flash('Нельзя удалить самого себя', 'error')
        return redirect(url_for('admin.teachers'))
    # Delete all associated data
    sessions = TestSession.query.filter_by(teacher_id=tid).all()
    for s in sessions:
        Answer.query.filter_by(session_id=s.id).delete()
        db.session.delete(s)
    db.session.delete(t)
    db.session.commit()
    flash(f'Учитель «{t.full_name}» и все связанные данные удалены', 'success')
    return redirect(url_for('admin.teachers'))


@admin_bp.route('/users/<int:uid>/change-role', methods=['POST'])
@login_required
@admin_required
def change_role(uid):
    user = User.query.get_or_404(uid)
    new_role = request.form.get('role')
    
    if user.id == current_user.id:
        flash('Вы не можете изменить свою собственную роль', 'error')
        return redirect(request.referrer or url_for('admin.dashboard'))
        
    if new_role not in ['admin', 'teacher']:
        flash('Неверная роль', 'error')
        return redirect(request.referrer or url_for('admin.dashboard'))
        
    # If demoting the last active admin
    if user.role == 'admin' and new_role == 'teacher':
        active_admins_count = User.query.filter_by(role='admin', is_active=True).count()
        if active_admins_count <= 1:
            flash('Нельзя лишить прав последнего активного администратора', 'error')
            return redirect(url_for('admin.admins'))

    user.role = new_role
    db.session.commit()
    flash(f'Роль пользователя {user.full_name} изменена на {"Администратор" if new_role == "admin" else "Учитель"}', 'success')
    
    if new_role == 'admin':
        return redirect(url_for('admin.admins'))
    else:
        return redirect(url_for('admin.teachers'))


@admin_bp.route('/admins')
@login_required
@admin_required
def admins():
    admins_list = User.query.filter_by(role='admin').order_by(User.created_at.desc()).all()
    active_admins_count = User.query.filter_by(role='admin', is_active=True).count()
    return render_template('admin/admins.html',
                           admins=admins_list,
                           active_admins_count=active_admins_count)


@admin_bp.route('/admins/add', methods=['POST'])
@login_required
@admin_required
def add_admin():
    username = request.form.get('username', '').strip()
    full_name = request.form.get('full_name', '').strip()
    password = request.form.get('password', '')
    if not username or not full_name or not password:
        flash('Заполните все поля', 'error')
        return redirect(url_for('admin.admins'))
    if User.query.filter_by(username=username).first():
        flash('Логин уже занят', 'error')
        return redirect(url_for('admin.admins'))
    a = User(username=username, full_name=full_name, role='admin', is_active=True)
    a.set_password(password)
    db.session.add(a)
    db.session.commit()
    flash(f'Администратор «{full_name}» добавлен', 'success')
    return redirect(url_for('admin.admins'))


@admin_bp.route('/admins/<int:aid>/toggle', methods=['POST'])
@login_required
@admin_required
def toggle_admin(aid):
    a = User.query.get_or_404(aid)
    if a.id == current_user.id:
        flash('Нельзя изменить статус текущего администратора', 'error')
        return redirect(url_for('admin.admins'))
    if a.is_active:
        active_admins_count = User.query.filter_by(role='admin', is_active=True).count()
        if active_admins_count <= 1:
            flash('Нельзя отключить последнего активного администратора', 'error')
            return redirect(url_for('admin.admins'))
    a.is_active = not a.is_active
    db.session.commit()
    flash(f'Администратор {a.full_name} {"активирован" if a.is_active else "деактивирован"}', 'success')
    return redirect(url_for('admin.admins'))


@admin_bp.route('/admins/<int:aid>/reset-password', methods=['POST'])
@login_required
@admin_required
def reset_admin_password(aid):
    a = User.query.get_or_404(aid)
    pwd = request.form.get('new_password', '')
    if not pwd:
        flash('Введите новый пароль', 'error')
        return redirect(url_for('admin.admins'))
    a.set_password(pwd)
    db.session.commit()
    flash(f'Пароль для {a.full_name} обновлён', 'success')
    return redirect(url_for('admin.admins'))


@admin_bp.route('/results')
@login_required
@admin_required
def results():
    q = TestSession.query.filter_by(status='completed')
    student_id = request.args.get('student_id', type=int)
    teacher_id = request.args.get('teacher_id', type=int)
    term = (request.args.get('q') or '').strip()
    if student_id:
        q = q.filter_by(student_id=student_id)
    if teacher_id:
        q = q.filter_by(teacher_id=teacher_id)
    if term:
        like = f'%{term}%'
        q = (q.join(Student, TestSession.student_id == Student.id)
             .join(User, TestSession.teacher_id == User.id)
             .filter(or_(Student.full_name.ilike(like),
                         User.full_name.ilike(like),
                         User.username.ilike(like))))
    sessions = q.order_by(TestSession.completed_at.desc()).all()
    return render_template('admin/results.html',
                           sessions=sessions,
                           student_id=student_id,
                           teacher_id=teacher_id,
                           q=term)


@admin_bp.route('/active-sessions')
@login_required
@admin_required
def active_sessions():
    sessions = (TestSession.query.filter_by(status='in_progress')
                .order_by(TestSession.started_at.desc()).all())
    return render_template('admin/active_sessions.html', sessions=sessions)


@admin_bp.route('/results/students')
@login_required
@admin_required
def results_students():
    term = (request.args.get('q') or '').strip().lower()
    sessions = (TestSession.query.filter_by(status='completed')
                .order_by(TestSession.completed_at.desc()).all())
    rows_map = {}
    for s in sessions:
        sid = s.student_id
        if sid not in rows_map:
            rows_map[sid] = {
                'student': s.student,
                'count': 0,
                'pct_sum': 0.0,
                'last_completed_at': None,
            }
        rows_map[sid]['count'] += 1
        rows_map[sid]['pct_sum'] += s.percentage()
        if not rows_map[sid]['last_completed_at'] or (s.completed_at and s.completed_at > rows_map[sid]['last_completed_at']):
            rows_map[sid]['last_completed_at'] = s.completed_at

    rows = []
    for item in rows_map.values():
        avg_pct = round(item['pct_sum'] / item['count'], 1) if item['count'] else 0
        rows.append({
            'student': item['student'],
            'count': item['count'],
            'avg_pct': avg_pct,
            'last_completed_at': item['last_completed_at'],
        })
    rows.sort(key=lambda r: (r['last_completed_at'] is None, r['last_completed_at']), reverse=True)
    if term:
        rows = [r for r in rows if term in (r['student'].full_name or '').lower()]
    return render_template('admin/results_students.html', rows=rows, q=term)


@admin_bp.route('/results/teachers')
@login_required
@admin_required
def results_teachers():
    term = (request.args.get('q') or '').strip().lower()
    sessions = (TestSession.query.filter_by(status='completed')
                .order_by(TestSession.completed_at.desc()).all())
    rows_map = {}
    for s in sessions:
        tid = s.teacher_id
        if tid not in rows_map:
            rows_map[tid] = {
                'teacher': s.teacher,
                'count': 0,
                'pct_sum': 0.0,
                'last_completed_at': None,
            }
        rows_map[tid]['count'] += 1
        rows_map[tid]['pct_sum'] += s.percentage()
        if not rows_map[tid]['last_completed_at'] or (s.completed_at and s.completed_at > rows_map[tid]['last_completed_at']):
            rows_map[tid]['last_completed_at'] = s.completed_at

    rows = []
    for item in rows_map.values():
        avg_pct = round(item['pct_sum'] / item['count'], 1) if item['count'] else 0
        rows.append({
            'teacher': item['teacher'],
            'count': item['count'],
            'avg_pct': avg_pct,
            'last_completed_at': item['last_completed_at'],
        })
    rows.sort(key=lambda r: (r['last_completed_at'] is None, r['last_completed_at']), reverse=True)
    if term:
        rows = [r for r in rows if term in (r['teacher'].full_name or '').lower() or term in (r['teacher'].username or '').lower()]
    return render_template('admin/results_teachers.html', rows=rows, q=term)


@admin_bp.route('/results/<int:sid>')
@login_required
@admin_required
def result_detail(sid):
    session = TestSession.query.get_or_404(sid)
    subjects = Subject.query.order_by(Subject.order).all()
    return render_template('admin/result_detail.html', session=session, subjects=subjects)


@admin_bp.route('/results/<int:sid>/delete', methods=['POST'])
@login_required
@admin_required
def delete_session(sid):
    session = TestSession.query.get_or_404(sid)
    # Allow deleting both completed and in_progress sessions
    Answer.query.filter_by(session_id=sid).delete()
    db.session.delete(session)
    db.session.commit()
    flash('Тест удалён', 'success')
    # Redirect back to where we came from if possible
    ref = request.referrer
    if ref and 'active-sessions' in ref:
        return redirect(url_for('admin.active_sessions'))
    return redirect(url_for('admin.results'))


@admin_bp.route('/change-password', methods=['GET', 'POST'])
@login_required
@admin_required
def change_password():
    if request.method == 'POST':
        current_password = request.form.get('current_password', '')
        new_password = request.form.get('new_password', '')
        new_password2 = request.form.get('new_password2', '')

        if not current_password or not new_password or not new_password2:
            flash('Заполните все поля', 'error')
            return redirect(url_for('admin.change_password'))

        if not current_user.check_password(current_password):
            flash('Текущий пароль неверный', 'error')
            return redirect(url_for('admin.change_password'))

        if new_password != new_password2:
            flash('Пароли не совпадают', 'error')
            return redirect(url_for('admin.change_password'))

        if len(new_password) < 6:
            flash('Пароль должен быть минимум 6 символов', 'error')
            return redirect(url_for('admin.change_password'))

        current_user.set_password(new_password)
        db.session.commit()
        logout_user()
        flash('Пароль обновлён. Войдите снова', 'success')
        return redirect(url_for('auth.login'))

    return render_template('admin/change_password.html')


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
