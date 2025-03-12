from datetime import datetime, UTC, timezone
import pytz
from flask import Blueprint, render_template, request, redirect, session, url_for, flash
from flask_login import login_required, current_user
from wtforms import RadioField
from wtforms.validators import DataRequired
from models import *
from .forms import AttemptQuizForm

user_bp = Blueprint('user', __name__, url_prefix='/user')

@user_bp.route('/dashboard')
@login_required
def dashboard():
    total_subjects = Subject.query.count()
    total_quizzes = Quiz.query.count()
    recent_scores = Score.query.filter_by(user_id=current_user.id).order_by(Score.timestamp.desc()).limit(10).all()

    return render_template('user_dashboard.html', total_subjects=total_subjects, total_quizzes=total_quizzes, recent_scores=recent_scores, is_admin=False)

@user_bp.route('/quizzes/<int:chapter_id>', methods=['GET', 'POST'])
@login_required
def quizzes(chapter_id=0):
    if chapter_id == 0:
        quizzes = Quiz.query.order_by(Quiz.id.asc()).all()
    else:
        quizzes = Quiz.query.filter_by(chapter_id=chapter_id).all()
    return render_template('user_quizzes.html', quizzes=quizzes,chapter_id=chapter_id, is_admin=False)

@user_bp.route('/subjects', methods=['GET'])
@login_required
def subjects():
    subjects = Subject.query.all()
    return render_template('user_subjects.html', subjects=subjects, is_admin=False)

@user_bp.route('/chapters/<int:subject_id>', methods=['GET'])
@login_required
def chapters(subject_id):
    chapters = Chapter.query.filter_by(subject_id=subject_id).all()
    return render_template('user_chapters.html', chapters=chapters, is_admin=False)


@user_bp.route('/attempt_quiz/<int:quiz_id>/<int:chapter_id>', methods=['GET', 'POST'])
@login_required
def attempt_quiz(quiz_id, chapter_id):
    quiz = Quiz.query.get_or_404(quiz_id)
    now = datetime.now(UTC)
    due_date = quiz.date_of_quiz

    ist = pytz.timezone("Asia/Kolkata")
    due_date_ist = ist.localize(due_date)
    due_date = due_date_ist.astimezone(UTC)


    if now > due_date:
        flash("Quiz due date has passed. You cannot attempt this quiz.", "danger")
        return redirect(url_for('user.quizzes', chapter_id=chapter_id)) 


    questions = Question.query.filter_by(quiz_id=quiz_id).all()
    form = AttemptQuizForm()

    for question in questions:
        field_name = f"question_{question.id}"
 
        if not hasattr(AttemptQuizForm, field_name):
            setattr(AttemptQuizForm, field_name, RadioField(
                label=question.question_statement,
                choices=[('1', question.option1),
                         ('2', question.option2),
                         ('3', question.option3),
                         ('4', question.option4)],
                validators=[DataRequired()]
            ))
    
    form = AttemptQuizForm()
    
    if form.validate_on_submit():
        score = 0
        feedback = []

        def get_option_text(q, option_num):
            if option_num == 1:
                return q.option1
            elif option_num == 2:
                return q.option2
            elif option_num == 3:
                return q.option3
            elif option_num == 4:
                return q.option4
            return ""
        
        for question in questions:
            field_name = f"question_{question.id}"
            user_ans = int(form[field_name].data)
            is_correct = (user_ans == question.correct_option)
            if is_correct:
                score += 1
            feedback.append({
                'question_text': question.question_statement,
                'user_answer': user_ans,
                'user_answer_text': get_option_text(question, user_ans),
                'correct_answer': question.correct_option,
                'correct_answer_text': get_option_text(question, question.correct_option),
                'is_correct': is_correct,
            })

        score = (score/len(questions)) * 100
        new_score = Score(quiz_id=quiz_id, user_id=current_user.id, total_scored=score)
        db.session.add(new_score)
        db.session.commit()
 
        session['feedback'] = feedback

        flash(f"Quiz submitted! Your score: {score}%", "success")
        return redirect(url_for('user.quiz_results', quiz_id=quiz_id, user_id=current_user.id))
    

    duration_seconds = (quiz.time_duration.hour * 3600 +
                        quiz.time_duration.minute * 60)
    
    return render_template('attempt_quiz.html', quiz=quiz, questions=questions, form=form, duration_seconds=duration_seconds, is_admin=False)

@user_bp.route('/quiz_results/<int:quiz_id>/<int:user_id>', methods=['GET'])
@login_required
def quiz_results(quiz_id, user_id):

    attempts = Score.query.filter_by(quiz_id=quiz_id, user_id=user_id).order_by(Score.timestamp.desc()).all()
    
    if attempts:
        latest_attempt = attempts[0]
        previous_attempts = attempts[1:]
    else:
        latest_attempt = None
        previous_attempts = []

    feedback = session.pop('feedback', None)
    
    return render_template('quiz_results.html', 
                           latest_attempt=latest_attempt, 
                           previous_attempts=previous_attempts, 
                           feedback=feedback)

