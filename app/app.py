# pip install flask
# pip install flask-sqlalchemy
import math
import os
import time

from flask import Flask, render_template, url_for, request, jsonify, redirect, flash, session
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import LoginManager, login_user, logout_user, current_user, login_required, UserMixin

app = Flask(__name__)  # делаем app основным файлом для работы с Flask
app.secret_key = 'K5s2G9jP4FvA7rL3tQ1W6eD8'
# Настройки конфигурации
basedir = os.path.abspath(os.path.dirname(__file__))
class Config:
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or \
        'sqlite:///' + os.path.join(basedir, 'app.db')
    SQLALCHEMY_TRACK_MODIFICATIONS = False

app.config.from_object(Config)

app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///example.db'
db = SQLAlchemy(app)

login_manager = LoginManager()
login_manager.init_app(app)

class Users (db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(100), nullable=False)
    password = db.Column(db.String(100), nullable=False)
    time = db.Column(db.Integer, nullable=False)

    def __repr__(self):
        return f"<Пользователь: {self.name}>"
class Themes(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200), nullable=False)

    def __repr__(self): #чтобы получать запись из бд
        return f"<Тема: {self.name}>"

class Tasks(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    task_text = db.Column(db.String(500), nullable=False)
    theme_id = db.Column(db.Integer, db.ForeignKey('themes.id'), nullable=False)

    theme = db.relationship('Themes', backref=db.backref('tasks', lazy=True))

    def __repr__(self):
        return f"<Задание: {self.task_text}>"

class Templates(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    template = db.Column(db.String(200), nullable=False)
    template_SHOW = db.Column(db.String(200), nullable=False)
    theme_id = db.Column(db.Integer, db.ForeignKey('themes.id'), nullable=False)

    theme = db.relationship('Themes', backref=db.backref('templates', lazy=True))

    def __repr__(self):
        return f"<Шаблон: {self.template}>"

class SavedTasks(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    task = db.Column(db.String(500), nullable=False)
    theme_id = db.Column(db.Integer, db.ForeignKey('themes.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    template_id = db.Column(db.Integer, db.ForeignKey('templates.id'), nullable=False)

    theme = db.relationship('Themes', backref=db.backref('saved_tasks', lazy=True))
    user = db.relationship('Users', backref=db.backref('saved_tasks', lazy=True))
    template = db.relationship('Templates', backref=db.backref('saved_tasks', lazy=True))


    def __repr__(self):
        return f"<Сохраненная задача: {self.task}>"


@login_manager.user_loader
def load_user(user_id):
    return Users.query.get(user_id)

@app.route('/')  # отслеживаем главную страничку
def index():
    themes = Themes.query.all()
    return render_template('index.html', themes=themes)
    #user = db.session.get(Users, current_user.get_id())
    #return render_template("index.html")


@app.route('/login', methods=["POST", "GET"])
def login():
    if request.method == "POST":
        email = request.form['email']
        user = Users.query.filter_by(email=email).first()
        if user and check_password_hash(user.password, request.form['password']):
            login_user(user)
            current_user.get_id()
            return redirect(url_for('index'))
        flash("Неправильный логин или пароль")
        return redirect(url_for('login'))
    else:
        themes = Themes.query.all()
        return render_template("login.html", themes=themes)

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))

@app.route('/register', methods=["POST", "GET"])
def register():
    if request.method == "POST":
        name = request.form['name']
        email = request.form['email']
        password = request.form['password']
        password_rep = request.form['password_rep']

        # Проверка на пустые данные
        if not name or not email or not password:
            flash("Пожалуйста, заполните все поля")
            return redirect(url_for('register'))

        # Проверка на уникальность email
        existing_user = Users.query.filter_by(email=email).first()
        if existing_user:
            flash("Пользователь с таким email уже зарегистрирован")
            return redirect(url_for('register'))

        hash = generate_password_hash(password)

        if check_password_hash(hash, password_rep) == False:
            flash("Пароли не совпадают!")
            return redirect(url_for('register'))
        tm = math.floor(time.time())
        new_user = Users(name=name, email=email, password=hash, time=tm)
        db.session.add(new_user)
        db.session.commit()

        flash("Вы успешно зарегистрировались!")
        return redirect(url_for('login'))
    else:
        themes = Themes.query.all()
        return render_template("register.html", themes=themes)


@app.route('/calculate')
def calculate():
    themes = Themes.query.all()
    return render_template("calculate.html", themes=themes)


@app.route('/params', methods=['POST', 'GET'])
def params():
    theme_id = request.args.get('theme_id')
    if request.method == "POST":
        task_id = request.form['task_id']
        return redirect(url_for('rend2', task_id=task_id))
    else:
        themes = Themes.query.all()
        current_theme = Themes.query.filter_by(id=theme_id).first()
        templates = Templates.query.filter_by(theme_id=current_theme.id).all()
        saved_tasks = SavedTasks.query.filter_by(user_id=current_user.get_id()).filter_by(
            theme_id=current_theme.id).all()
        return render_template("params.html",
                               saved_tasks=saved_tasks, themes=themes, current_theme=current_theme, templates=templates)


@app.route('/rend')
def rend():
    req = request.args.get('theme_id')
    theme_id = req.split('?')[0]
    template_id = req.split('?')[1].split('=')[1]
    print(theme_id)
    print(template_id)
    current_theme = Themes.query.filter_by(id=theme_id).first()

    current_template = Templates.query.filter_by(id=template_id).first()
    task = Tasks.query.filter_by(theme_id=theme_id).first()
    themes = Themes.query.all()
    return render_template("rend.html", current_theme=current_theme, task=task, current_template=current_template, themes=themes)

@app.route('/rend2')
def rend2():
    print("sdasd")
    req = request.args.get('theme_id')
    theme_id = req.split('?')[0]
    task_id = req.split('?')[1].split('=')[1]
    print(theme_id)
    print(task_id)
    current_theme = Themes.query.filter_by(id=theme_id).first()

    current_task = SavedTasks.query.filter_by(id=task_id).first()
    task = Tasks.query.filter_by(theme_id=theme_id).first()
    themes = Themes.query.all()
    return render_template("rend2.html", current_theme=current_theme, task=task, current_task=current_task, themes=themes)


@app.route('/add_task', methods=['POST'])
def add_task():
    data = request.json
    task = data.get('task')
    theme_id = data.get('theme_id')
    template_id = data.get('template_id')
    print(theme_id)

    new_saved_task = SavedTasks(task=task, theme_id=theme_id, user_id=current_user.get_id(), template_id=template_id)
    db.session.add(new_saved_task)
    db.session.commit()

    return jsonify({'message': 'Task added successfully'})


# Создаем таблицы в базе данных
with app.app_context():
    # db.create_all()
    pass

if __name__ == "__main__":  # для того чтобы проект запускался как приложение flask
    app.run(debug=True)  # debug чтобы выводились на страничке все ошибки
