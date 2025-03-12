from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required, current_user
from models import *
from functools import wraps
from .forms import SubjectForm, ChapterForm, QuizForm, QuestionForm

admin_bp = Blueprint('admin', __name__, url_prefix='/admin')

def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if current_user.is_authenticated:
            user_identifier = current_user.get_id()  
            if user_identifier.startswith("admin-"):
                return f(*args, **kwargs)
            else:
                flash('Access denied', 'danger')
                return redirect(url_for('auth.home'))
        else:
            flash('Access denied', 'danger')
            return redirect(url_for('auth.home'))
    return decorated_function


@admin_bp.route('/dashboard')
@admin_required
def dashboard():
    total_users = User.query.count()
    total_subjects = Subject.query.count()
    recent_scores = Score.query.order_by(Score.timestamp.desc()).limit(10).all()

    return render_template('admin_dashboard.html', total_users=total_users,total_subjects=total_subjects, recent_scores=recent_scores, is_admin=True)

@admin_bp.route('/subjects', methods=['GET', 'POST'])
@admin_required
def subjects():
    form = SubjectForm()
    if form.validate_on_submit():
        subject = Subject(name=form.name.data, description=form.description.data)
        db.session.add(subject)
        db.session.commit()
        flash('Subject added successfully', 'success')
        return redirect(url_for('admin.subjects'))

    subjects = Subject.query.all()

    return render_template('admin_subjects.html', subjects=subjects, is_admin=True, form=form)

@admin_bp.route("/edit-subject/<int:subject_id>", methods=["GET", "POST"])
@admin_required
def edit_subject(subject_id):
    subject = Subject.query.get_or_404(subject_id)
    form = SubjectForm(request.form)  

    if form.validate_on_submit():
        subject.name = form.name.data
        subject.description = form.description.data
        db.session.commit()
        flash("Subject updated successfully", "success")

    return redirect(url_for("admin.subjects"))  

@admin_bp.route('/delete_subject/<int:subject_id>', methods=['POST'])
@admin_required
def delete_subject(subject_id):
    subject = Subject.query.get_or_404(subject_id)
    db.session.delete(subject)
    db.session.commit()
    flash('Subject deleted successfully', 'success')
    return redirect(url_for('admin.subjects'))

@admin_bp.route('/chapters/<int:subject_id>', methods=['GET', 'POST'])
@admin_required
def chapters(subject_id):
    subject = Subject.query.get_or_404(subject_id)

    form = ChapterForm()
    if form.validate_on_submit(): 
        chapter = Chapter(subject_id=subject_id, name=form.name.data, description=form.description.data)
        db.session.add(chapter)
        db.session.commit()

        flash('Chapter added successfully', 'success')
        return redirect(url_for('admin.chapters', subject_id=subject_id))

    return render_template('admin_chapters.html', subject=subject, chapters=subject.chapters, form=form, is_admin=True)

@admin_bp.route("/edit-chapter/<int:chapter_id>", methods=["GET", "POST"])
@admin_required
def edit_chapter(chapter_id):
    chapter = Chapter.query.get_or_404(chapter_id)
    subject_id = chapter.subject_id
    form = ChapterForm(request.form)  

    if form.validate_on_submit():
        chapter.name = form.name.data
        chapter.description = form.description.data
        db.session.commit()
        flash("Chapter updated successfully", "success")

    return redirect(url_for("admin.chapters", subject_id=subject_id)) 

@admin_bp.route('/delete_chapter/<int:chapter_id>', methods=['POST'])
@admin_required
def delete_chapter(chapter_id):
    chapter = Chapter.query.get_or_404(chapter_id)
    subject_id = chapter.subject_id
    db.session.delete(chapter)
    db.session.commit()
    flash('Chapter deleted successfully', 'success')
    return redirect(url_for('admin.chapters', subject_id=subject_id))

@admin_bp.route('/quizzes/<int:chapter_id>', methods=['GET', 'POST'])
@admin_required
def quizzes(chapter_id):
    chapter = Chapter.query.get_or_404(chapter_id)
    form = QuizForm()
    if form.validate_on_submit():
        print("form validate succesfully")
        quiz = Quiz(
            chapter_id=chapter_id,
            date_of_quiz=form.date_of_quiz.data,
            time_duration=form.time_duration.data,
            remarks=form.remarks.data
        )
        db.session.add(quiz)
        db.session.commit()
        flash('Quiz created successfully!', 'success')
        return redirect(url_for('admin.quizzes', chapter_id=chapter_id))

    return render_template('admin_quizzes.html', form=form,chapter=chapter, chapter_id=chapter_id,quizzes=chapter.quizzes, is_admin=True)


@admin_bp.route("/edit-quiz/<int:quiz_id>", methods=["GET", "POST"])
@admin_required
def edit_quiz(quiz_id):
    print("edit quiz")
    quiz = Quiz.query.get_or_404(quiz_id)
    chapter_id = quiz.chapter_id
    form = QuizForm(request.form)  

    if form.validate_on_submit():
        print("form validate succesfully")
        quiz.date_of_quiz = form.date_of_quiz.data
        quiz.time_duration = form.time_duration.data
        quiz.remarks = form.remarks.data
        db.session.commit()
        flash("Quiz updated successfully", "success")

    return redirect(url_for("admin.quizzes", chapter_id=chapter_id))

@admin_bp.route('/delete_quiz/<int:quiz_id>', methods=['POST'])
@admin_required
def delete_quiz(quiz_id):
    quiz = Quiz.query.get_or_404(quiz_id)
    chapter_id = quiz.chapter_id
    db.session.delete(quiz)
    db.session.commit()
    flash('Quiz deleted successfully', 'success')
    return redirect(url_for('admin.quizzes', chapter_id=chapter_id))

@admin_bp.route('/scores/<int:quiz_id>', methods=['GET'])
@admin_required
def scores(quiz_id):
    quiz = Quiz.query.get_or_404(quiz_id)
    scores = Score.query.filter_by(quiz_id=quiz_id).all()

    return render_template('admin_scores.html', quiz=quiz, scores=scores, is_admin=True)

@admin_bp.route('/question/<int:quiz_id>', methods=['GET', 'POST'])
@admin_required
def questions(quiz_id):
    quiz = Quiz.query.get_or_404(quiz_id)
    form = QuestionForm()
    if form.validate_on_submit():
        question = Question(
            quiz_id=quiz_id,
            question_statement=form.question_statement.data,
            option1=form.option1.data,
            option2=form.option2.data,
            option3=form.option3.data,
            option4=form.option4.data,
            correct_option=form.correct_option.data
        )
        db.session.add(question)
        db.session.commit()
        flash('Question added successfully!', 'success')
        return redirect(url_for('admin.questions', quiz_id=quiz_id))
    
    return render_template('admin_questions.html', form=form, quiz=quiz, questions=quiz.questions, is_admin=True)

@admin_bp.route('/edit_question/<int:question_id>', methods=['POST'])
@admin_required
def edit_question(question_id):
    question = Question.query.get_or_404(question_id)
    form = QuestionForm(request.form)

    if form.validate_on_submit():
        question.question_statement = form.question_statement.data
        question.option1 = form.option1.data
        question.option2 = form.option2.data
        question.option3 = form.option3.data
        question.option4 = form.option4.data
        question.correct_option = form.correct_option.data
        db.session.commit()
        flash('Question updated successfully!', 'success')
    
    return redirect(url_for('admin.questions', quiz_id=question.quiz_id))

@admin_bp.route('/delete_question/<int:question_id>', methods=['POST'])
@admin_required
def delete_question(question_id):
    question = Question.query.get_or_404(question_id)
    quiz_id = question.quiz_id
    db.session.delete(question)
    db.session.commit()
    flash('Chapter deleted successfully', 'success')
    return redirect(url_for('admin.questions', quiz_id=quiz_id))

@admin_bp.route('/users')
@admin_required
def users():
    users = User.query.all()
    return render_template('admin_users.html', users=users, is_admin=True)

@admin_bp.route('/user_scores/<int:user_id>', methods=['GET'])
@admin_required
def user_scores(user_id):
    user = User.query.get_or_404(user_id)
    scores = Score.query.filter_by(user_id=user_id).all()
    return render_template('admin_user_scores.html', user=user, scores=scores, is_admin=True)

@admin_bp.route('/delete_user/<int:user_id>', methods=['POST'])
@admin_required
def delete_user(user_id):

    user = User.query.get_or_404(user_id)
    db.session.delete(user)
    db.session.commit()

    flash('User deleted successfully', 'success')
    return redirect(url_for('admin.users'))