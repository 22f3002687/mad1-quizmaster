from datetime import datetime, UTC, timezone
import pytz
from flask import Blueprint, render_template, request, redirect, session, url_for, flash
from flask_login import login_required, current_user
from models import *
from sqlalchemy import text
import re

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
        chapter = None
        quizzes = Quiz.query.order_by(Quiz.id.asc()).all()
    else:
        chapter = Chapter.query.get_or_404(chapter_id)
        quizzes = Quiz.query.filter_by(chapter_id=chapter_id).all()
    return render_template('user_quizzes.html', quizzes=quizzes,chapter_id=chapter_id,chapter=chapter, is_admin=False)

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


def get_option_text(q, option_num):
    if option_num == 1:
        return q.option1
    elif option_num == 2:
        return q.option2
    elif option_num == 3:
        return q.option3
    elif option_num == 4:
        return q.option4
    return "Skipped"

@user_bp.route('/attempt_quiz/<int:quiz_id>/<int:chapter_id>', methods=['GET', 'POST'])
@login_required
def attempt_quiz(quiz_id, chapter_id):
    quiz = Quiz.query.get_or_404(quiz_id)
    questions = quiz.questions

    now = datetime.now(UTC)
    due_date = quiz.date_of_quiz

    ist = pytz.timezone("Asia/Kolkata")
    due_date_ist = ist.localize(due_date)
    due_date = due_date_ist.astimezone(UTC)

    

    if request.method == 'POST':
        score = 0
        feedback = []
        for question in questions:
            is_correct = False
            user_answer = request.form.get(f'question_{question.id}')

            if user_answer and int(user_answer) == question.correct_option:
                is_correct = True
                score +=1
            
            feedback.append({
                'question_text': question.question_statement,
                'user_answer': user_answer if user_answer !="0" else "Skipped",
                'user_answer_text': get_option_text(question, int(user_answer)) if user_answer != "0" else "Skipped",
                'correct_answer': question.correct_option,
                'correct_answer_text': get_option_text(question, question.correct_option),
                'is_correct': is_correct if user_answer != "0" else False,  
            })
        
        session['feedback'] = feedback     
        user_score = (score / len(questions))*100
        score_entry = Score(quiz_id=quiz_id,
                            user_id=current_user.id,
                            total_scored=user_score)
        db.session.add(score_entry)
        db.session.commit()
        flash(f"Quiz submitted! Your score: {user_score:.2f}%", "success")
        return redirect(url_for('user.quiz_results', quiz_id=quiz_id, user_id=current_user.id))
    

    if now > due_date:
        flash("Quiz due date has passed. You cannot attempt this quiz.", "danger")
        return redirect(url_for('user.quizzes', chapter_id=chapter_id))
    

    duration_seconds = (quiz.time_duration.hour * 3600 + quiz.time_duration.minute * 60)
    return render_template('attempt_quiz.html', quiz=quiz, questions=questions,duration_seconds=duration_seconds, is_admin=False)

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
                           feedback=feedback, 
                           is_admin=False)

def escape_fts_query(query):
    return re.sub(r'[\W]+', ' ', query) 

@user_bp.route('/search_subjects', methods=['GET'])
@login_required
def search_subjects():
    query = request.args.get('q', '').strip()
    if not query:
        return redirect(url_for('user.subjects'))
    
    query = escape_fts_query(query)

    connection = db.engine.connect()
    subject_query = text("""
    SELECT id, name, description
    FROM subject_fts 
    WHERE name MATCH :query 
    OR description MATCH :query
    LIMIT 10;
    """)

    subject_results = connection.execute(subject_query, {'query': f'"{query}"*'}).fetchall()
    connection.close()

    return render_template("user_search_subjects.html", query=query, subject_results=subject_results, is_admin=False)

@user_bp.route('/search_quizzes/<int:chapter_id>', methods=['GET'])
@login_required
def search_quizzes(chapter_id=0):
    query = request.args.get('q', '').strip()
    if not query:
        return redirect(url_for('admin.quizzes', chapter_id=chapter_id))
    
    query = escape_fts_query(query)

    connection = db.engine.connect()

    if chapter_id == 0:
        quiz_query = text("""
        SELECT id, remarks, date_of_quiz, time_duration, chapter_name, subject_name
        FROM quiz_fts 
        WHERE remarks MATCH :query
        OR chapter_name MATCH :query
        OR subject_name MATCH :query
        LIMIT 10;
        """)
    else:
        quiz_query = text("""
        SELECT id, remarks, date_of_quiz, time_duration, chapter_name, subject_name
        FROM quiz_fts 
        WHERE remarks MATCH :query
        OR chapter_name MATCH :query
        OR subject_name MATCH :query
        AND chapter_id = :chapter_id
        LIMIT 10;
        """)

    quiz_results = connection.execute(quiz_query, {'query': f'"{query}"*', 'chapter_id': chapter_id }).fetchall()
    connection.close()

    return render_template("user_search_quizzes.html", query=query, quiz_results=quiz_results, chapter_id=chapter_id, is_admin=False)


@user_bp.route('/profile', methods=['GET'])
@login_required
def profile():
    user = User.query.get(current_user.id)
    quiz_attempts = Score.query.filter_by(user_id=current_user.id).all()
    no_of_attempts = len(quiz_attempts)
    avg_score = sum([score.total_scored for score in quiz_attempts]) / no_of_attempts if no_of_attempts > 0 else 0
    avg_score = round(avg_score,2)
    
    return render_template('user_profile.html', user=user, no_of_attempts=no_of_attempts, avg_score=avg_score, is_admin=False)


@user_bp.route('/quiz_history/<int:quiz_id>', methods=['GET'])
@login_required
def quiz_history(quiz_id):
    user_id = current_user.id

    if quiz_id == 0:
        attempts = Score.query.filter_by(user_id=user_id).order_by(Score.timestamp.desc()).all()
        no_of_attempts = len(attempts)
        avg_sore = sum([score.total_scored for score in attempts]) / no_of_attempts if no_of_attempts > 0 else 0

        avg_sore = round(avg_sore,2)
        return render_template('quiz_history.html', attempts=attempts,quiz_id=0,no_of_attempts=no_of_attempts, avg_sore=avg_sore, is_admin=False)
    else:

        attempts = Score.query.filter_by(user_id=user_id, quiz_id=quiz_id).order_by(Score.timestamp.desc()).all()
        quiz = Quiz.query.get_or_404(quiz_id)
        no_of_attempts = len(attempts)
        avg_sore = sum([score.total_scored for score in attempts]) / no_of_attempts if no_of_attempts > 0 else 0
        avg_sore = round(avg_sore,2)
        return render_template('quiz_history.html', attempts=attempts,quiz_id=quiz_id, no_of_attempts=no_of_attempts, avg_sore=avg_sore,quiz=quiz, is_admin=False)
