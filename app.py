from flask import Flask, render_template, request, redirect, url_for, flash, abort
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from werkzeug.security import generate_password_hash, check_password_hash
import os
import requests

app = Flask(__name__)
app.config['SECRET_KEY'] = 'supersecretkey'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///news.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['UPLOAD_FOLDER'] = 'static/uploads'

NEWS_API_KEY = "175d388775224e2a93da404219ba4bc7"

db = SQLAlchemy(app)

login_manager = LoginManager()
login_manager.login_view = 'login'
login_manager.init_app(app)

# ======================
# MODELS
# ======================

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(100), unique=True, nullable=False)
    password_hash = db.Column(db.String(200), nullable=False)
    role = db.Column(db.String(20), default="editor")

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def is_admin(self):
        return self.role == "admin"


class News(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    content = db.Column(db.Text, nullable=False)
    image = db.Column(db.String(200))


@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


# ======================
# FETCH LIVE NEWS
# ======================

def fetch_live_news():
    url = f"https://newsapi.org/v2/top-headlines?country=us&pageSize=6&apiKey={NEWS_API_KEY}"
    try:
        response = requests.get(url)
        data = response.json()

        if data.get("status") != "ok":
            print("News API Error:", data)
            return []

        return data.get("articles", [])

    except Exception as e:
        print("Request Failed:", e)
        return []


# ======================
# HOME (LIVE + DB)
# ======================

@app.route('/')
def home():
    page = request.args.get('page', 1, type=int)
    search_query = request.args.get('search', '')

    if search_query:
        news_query = News.query.filter(
            (News.title.contains(search_query)) |
            (News.content.contains(search_query))
        )
    else:
        news_query = News.query

    news_pagination = news_query.order_by(News.id.desc()).paginate(page=page, per_page=6)

    live_news = fetch_live_news()

    return render_template(
        'index.html',
        news_pagination=news_pagination,
        search_query=search_query,
        live_news=live_news
    )


# ======================
# DASHBOARD
# ======================

@app.route('/dashboard')
@login_required
def dashboard():
    total_news = News.query.count()
    total_users = User.query.count()
    recent_news = News.query.order_by(News.id.desc()).limit(5).all()

    return render_template(
        'dashboard.html',
        total_news=total_news,
        total_users=total_users,
        recent_news=recent_news
    )


# ======================
# AUTH
# ======================

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')

        user = User.query.filter_by(username=username).first()

        if user and user.check_password(password):
            login_user(user)
            return redirect(url_for('dashboard'))
        else:
            flash("Invalid username or password!", "danger")

    return render_template('login.html')


@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('home'))


# ======================
# CREATE USER (ADMIN)
# ======================

@app.route('/create-user', methods=['GET', 'POST'])
@login_required
def create_user():
    if not current_user.is_admin():
        abort(403)

    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        role = request.form.get('role')

        new_user = User(
            username=username,
            password_hash=generate_password_hash(password),
            role=role
        )

        db.session.add(new_user)
        db.session.commit()

        return redirect(url_for('dashboard'))

    return render_template('create_user.html')


# ======================
# CRUD
# ======================

@app.route('/add', methods=['GET', 'POST'])
@login_required
def add_news():
    if request.method == 'POST':
        title = request.form.get('title')
        content = request.form.get('content')
        image_file = request.files.get('image')

        image_filename = None

        if image_file and image_file.filename != "":
            os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
            image_path = os.path.join(app.config['UPLOAD_FOLDER'], image_file.filename)
            image_file.save(image_path)
            image_filename = image_file.filename

        new_news = News(title=title, content=content, image=image_filename)
        db.session.add(new_news)
        db.session.commit()

        return redirect(url_for('dashboard'))

    return render_template('add_news.html')


@app.route('/edit/<int:id>', methods=['GET', 'POST'])
@login_required
def edit_news(id):
    news_item = News.query.get_or_404(id)

    if request.method == 'POST':
        news_item.title = request.form.get('title')
        news_item.content = request.form.get('content')

        image_file = request.files.get('image')

        if image_file and image_file.filename != "":
            os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
            image_path = os.path.join(app.config['UPLOAD_FOLDER'], image_file.filename)
            image_file.save(image_path)
            news_item.image = image_file.filename

        db.session.commit()
        return redirect(url_for('dashboard'))

    return render_template('edit_news.html', news=news_item)


@app.route('/delete/<int:id>')
@login_required
def delete_news(id):
    if not current_user.is_admin():
        abort(403)

    news_item = News.query.get_or_404(id)
    db.session.delete(news_item)
    db.session.commit()
    return redirect(url_for('dashboard'))


# ======================
# RUN
# ======================

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True)
