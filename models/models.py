from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import DeclarativeBase, Session
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime, UTC
from sqlalchemy import event, DDL, text
import pytz

IST = pytz.timezone("Asia/Kolkata") 

class Base(DeclarativeBase):
  pass

db = SQLAlchemy(model_class=Base)

class Admin(db.Model, UserMixin):
    __tablename__ = 'admin'
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(100), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(256), nullable=False)
    
    
    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)
    
    def get_id(self):
        return f"admin-{self.id}"

class User(UserMixin, db.Model):
    __tablename__ = 'user'
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(100), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(256), nullable=False)
    full_name = db.Column(db.String(100), nullable=False)
    qualification = db.Column(db.String(100), nullable=False)
    dob = db.Column(db.Date, nullable=False)
    scores = db.relationship('Score', backref='user',cascade="all, delete", lazy=True)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)
    
    def get_id(self):
        return f"user-{self.id}"
    
    @staticmethod
    def after_insert(mapper, connection, target):
        connection.execute(text("""
            INSERT INTO user_fts (id, username, email, full_name, qualification, dob) 
            VALUES (:id, :username, :email, :full_name, :qualification, :dob)
        """), {"id": target.id, 
               "username": target.username, 
               "email": target.email, 
               "full_name": target.full_name, 
               "qualification": target.qualification,
               "dob": target.dob})

    @staticmethod
    def after_update(mapper, connection, target):
        connection.execute(text("DELETE FROM user_fts WHERE id = :id"), {"id": target.id})
        connection.execute(text("""
            INSERT INTO user_fts (id, username, email, full_name, qualification, dob) 
            VALUES (:id, :username, :email, :full_name, :qualification, :dob)
        """), {"id": target.id, 
               "username": target.username, 
               "email": target.email, 
               "full_name": target.full_name, 
               "qualification": target.qualification,
               "dob": target.dob})

    @staticmethod
    def after_delete(mapper, connection, target):
        connection.execute(text("DELETE FROM user_fts WHERE id = :id"), {"id": target.id})

event.listen(User, "after_insert", User.after_insert)
event.listen(User, "after_update", User.after_update)
event.listen(User, "after_delete", User.after_delete)
    
class Subject(db.Model):
    __tablename__ = 'subject'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text)
    chapters = db.relationship('Chapter', backref='subject', cascade="all, delete", lazy=True)

    @staticmethod
    def after_insert(mapper, connection, target):
        connection.execute(text("""
            INSERT INTO subject_fts (id, name, description) 
            VALUES (:id, :name, :description)
        """), {"id": target.id, "name": target.name, "description": target.description})

    @staticmethod
    def after_update(mapper, connection, target):
        connection.execute(text("DELETE FROM subject_fts WHERE id = :id"), {"id": target.id})
        connection.execute(text("""
            INSERT INTO subject_fts (id, name, description) 
            VALUES (:id, :name, :description)
        """), {"id": target.id, "name": target.name, "description": target.description})

    @staticmethod
    def after_delete(mapper, connection, target):
        connection.execute(text("DELETE FROM subject_fts WHERE id = :id"), {"id": target.id})

event.listen(Subject, "after_insert", Subject.after_insert)
event.listen(Subject, "after_update", Subject.after_update)
event.listen(Subject, "after_delete", Subject.after_delete)

class Chapter(db.Model):
    __tablename__ = 'chapter'
    id = db.Column(db.Integer, primary_key=True)
    subject_id = db.Column(db.Integer, db.ForeignKey('subject.id'), nullable=False)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text)
    quizzes = db.relationship('Quiz', backref='chapter',cascade="all, delete", lazy=True)

class Quiz(db.Model):
    __tablename__ = 'quiz'
    id = db.Column(db.Integer, primary_key=True)
    chapter_id = db.Column(db.Integer, db.ForeignKey('chapter.id'), nullable=False)
    date_of_quiz = db.Column(db.DateTime, nullable=False)
    time_duration = db.Column(db.Time, nullable=False)  
    remarks = db.Column(db.Text)
    questions = db.relationship('Question', backref='quiz', cascade="all, delete", lazy=True)
    scores = db.relationship('Score', backref='quiz', cascade="all, delete", lazy=True)

    @staticmethod
    def after_insert(mapper, connection, target):
        session = Session(connection)  # Create a session
        chapter = session.get(Chapter, target.chapter_id)  # Fetch chapter
        subject_name = chapter.subject.name if chapter and chapter.subject else "Unknown"
        session.close()

        connection.execute(text("""
            INSERT INTO quiz_fts (id, remarks, chapter_id, date_of_quiz, time_duration, chapter_name, subject_name) 
            VALUES (:id, :remarks, :chapter_id, :date_of_quiz, :time_duration, :chapter_name, :subject_name)
        """), {
            "id": target.id, 
            "remarks": target.remarks, 
            "chapter_id": target.chapter_id, 
            "date_of_quiz": target.date_of_quiz.strftime('%Y-%m-%d %H:%M'), 
            "time_duration": target.time_duration.strftime('%H:%M'),
            "chapter_name": chapter.name if chapter else "Unknown",
            "subject_name": subject_name
        })

    @staticmethod
    def after_update(mapper, connection, target):
        session = Session(connection)
        chapter = session.get(Chapter, target.chapter_id)  
        subject_name = chapter.subject.name if chapter and chapter.subject else "Unknown"
        session.close()

        connection.execute(text("DELETE FROM quiz_fts WHERE id = :id"), {"id": target.id})
        connection.execute(text("""
            INSERT INTO quiz_fts (id, remarks, chapter_id, date_of_quiz, time_duration, chapter_name, subject_name) 
            VALUES (:id, :remarks, :chapter_id, :date_of_quiz, :time_duration, :chapter_name, :subject_name)
        """), {
            "id": target.id, 
            "remarks": target.remarks, 
            "chapter_id": target.chapter_id, 
            "date_of_quiz": target.date_of_quiz.strftime('%Y-%m-%d %H:%M'), 
            "time_duration": target.time_duration.strftime('%H:%M'),
            "chapter_name": chapter.name if chapter else "Unknown",
            "subject_name": subject_name
        })

    @staticmethod
    def after_delete(mapper, connection, target):
        connection.execute(text("DELETE FROM quiz_fts WHERE id = :id"), {"id": target.id})

event.listen(Quiz, "after_insert", Quiz.after_insert)
event.listen(Quiz, "after_update", Quiz.after_update)
event.listen(Quiz, "after_delete", Quiz.after_delete)

class Question(db.Model):
    __tablename__ = 'question'
    id = db.Column(db.Integer, primary_key=True)
    quiz_id = db.Column(db.Integer, db.ForeignKey('quiz.id'), nullable=False)
    question_statement = db.Column(db.Text, nullable=False)
    option1 = db.Column(db.String(200), nullable=False)
    option2 = db.Column(db.String(200), nullable=False)
    option3 = db.Column(db.String(200), nullable=False)
    option4 = db.Column(db.String(200), nullable=False)
    correct_option = db.Column(db.Integer, nullable=False)  

    @staticmethod
    def after_insert(mapper, connection, target):
        connection.execute(text("""
            INSERT INTO question_fts (id, question_statement, option1, option2, option3, option4, correct_option, quiz_id) 
            VALUES (:id, :question_statement, :option1, :option2, :option3, :option4, :correct_option, :quiz_id)
        """), {
            "id": target.id, 
            "question_statement": target.question_statement,
            "option1": target.option1,
            "option2": target.option2,
            "option3": target.option3,
            "option4": target.option4,
            "correct_option": target.correct_option,
            "quiz_id": target.quiz_id
        })

    @staticmethod
    def after_update(mapper, connection, target):
        connection.execute(text("DELETE FROM question_fts WHERE id = :id"), {"id": target.id})
        connection.execute(text("""
            INSERT INTO question_fts (id, question_statement, option1, option2, option3, option4, correct_option, quiz_id) 
            VALUES (:id, :question_statement, :option1, :option2, :option3, :option4, :correct_option, :quiz_id)
        """), {
            "id": target.id, 
            "question_statement": target.question_statement,
            "option1": target.option1,
            "option2": target.option2,
            "option3": target.option3,
            "option4": target.option4,
            "correct_option": target.correct_option,
            "quiz_id": target.quiz_id
        })

    @staticmethod
    def after_delete(mapper, connection, target):
        connection.execute(text("DELETE FROM question_fts WHERE id = :id"), {"id": target.id})

event.listen(Question, "after_insert", Question.after_insert)
event.listen(Question, "after_update", Question.after_update)
event.listen(Question, "after_delete", Question.after_delete)

class Score(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    quiz_id = db.Column(db.Integer, db.ForeignKey('quiz.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    timestamp = db.Column(db.DateTime, default=lambda: datetime.now(UTC).astimezone(IST), nullable=False)
    total_scored = db.Column(db.Float, nullable=False)


@event.listens_for(User.__table__, 'after_create')
def create_user_fts5(target, connection, **kw):
    connection.execute(DDL('''
        CREATE VIRTUAL TABLE IF NOT EXISTS user_fts USING fts5(id, username, email, full_name, qualification, dob);
    '''))

@event.listens_for(Subject.__table__, 'after_create')
def create_subject_fts5(target, connection, **kw):
    connection.execute(DDL('''
        CREATE VIRTUAL TABLE IF NOT EXISTS subject_fts USING fts5(id, name, description);
    '''))

@event.listens_for(Quiz.__table__, 'after_create')
def create_quiz_fts5(target, connection, **kw):
    connection.execute(DDL('''
        CREATE VIRTUAL TABLE IF NOT EXISTS quiz_fts USING fts5(id, remarks, chapter_id, date_of_quiz, time_duration, chapter_name, subject_name);
    '''))

@event.listens_for(Question.__table__, 'after_create')
def create_question_fts5(target, connection, **kw):
    connection.execute(DDL('''
        CREATE VIRTUAL TABLE IF NOT EXISTS question_fts USING fts5(id, question_statement, option1, option2, option3, option4, correct_option, quiz_id);
    '''))


