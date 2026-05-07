from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_required, current_user
from models import db, Subject, Question, Student, TestSession, Answer
from datetime import datetime

teacher_bp = Blueprint('teacher', __name__)


@teacher_bp.route('/')
@login_required
def dashboard():
    my_sessions = (TestSession.query.filter_by(teacher_id=current_user.id)
                   .order_by(TestSession.started_at.desc()).limit(20).all())
    in_progress = (TestSession.query
                   .filter_by(teacher_id=current_user.id, status='in_progress')
                   .first())
    completed_count = (TestSession.query
                       .filter_by(teacher_id=current_user.id, status='completed')
                       .count())
    return render_template('teacher/dashboard.html',
                           my_sessions=my_sessions,
                           in_progress=in_progress,
                           completed_count=completed_count)


@teacher_bp.route('/new-test', methods=['GET', 'POST'])
@login_required
def new_test():
    if request.method == 'POST':
        full_name = request.form.get('full_name', '').strip()
        birth_date_str = request.form.get('birth_date', '')
        notes = request.form.get('notes', '').strip()
        if not full_name or not birth_date_str:
            flash('Заполните все обязательные поля', 'error')
            return render_template('teacher/new_test.html')
        try:
            birth_date = datetime.strptime(birth_date_str, '%Y-%m-%d').date()
        except ValueError:
            flash('Неверный формат даты', 'error')
            return render_template('teacher/new_test.html')
        student = Student(full_name=full_name, birth_date=birth_date)
        db.session.add(student)
        db.session.flush()
        session = TestSession(student_id=student.id,
                              teacher_id=current_user.id,
                              notes=notes or None)
        db.session.add(session)
        db.session.commit()
        return redirect(url_for('teacher.test_form', session_id=session.id))
    return render_template('teacher/new_test.html')


@teacher_bp.route('/test/<int:session_id>', methods=['GET', 'POST'])
@login_required
def test_form(session_id):
    session = TestSession.query.get_or_404(session_id)
    if session.teacher_id != current_user.id and not current_user.is_admin():
        flash('Доступ запрещён', 'error')
        return redirect(url_for('teacher.dashboard'))
    if session.status == 'completed':
        flash('Этот тест уже завершён', 'info')
        return redirect(url_for('teacher.dashboard'))

    subjects = Subject.query.order_by(Subject.order).all()

    if request.method == 'POST':
        for subject in subjects:
            for question in subject.questions:
                score_key = f'score_{question.id}'
                try:
                    score = max(0, min(100, int(request.form.get(score_key, 0))))
                except (ValueError, TypeError):
                    score = 0
                existing = Answer.query.filter_by(session_id=session.id,
                                                  question_id=question.id).first()
                if existing:
                    existing.score = score
                else:
                    db.session.add(Answer(session_id=session.id,
                                         question_id=question.id, score=score))
        if 'complete' in request.form:
            session.status = 'completed'
            session.completed_at = datetime.utcnow()
            db.session.commit()
            flash('Тест успешно завершён и сохранён!', 'success')
            return redirect(url_for('teacher.dashboard'))
        db.session.commit()
        flash('Данные сохранены', 'success')
        return redirect(url_for('teacher.test_form', session_id=session_id))

    existing_answers = {a.question_id: a.score for a in session.answers}
    return render_template('teacher/test_form.html',
                           session=session,
                           subjects=subjects,
                           existing_answers=existing_answers)


@teacher_bp.route('/history')
@login_required
def history():
    sessions = (TestSession.query
                .filter_by(teacher_id=current_user.id, status='completed')
                .order_by(TestSession.completed_at.desc()).all())
    return render_template('teacher/history.html', sessions=sessions)
