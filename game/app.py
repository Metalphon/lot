from flask import Flask, render_template, request, redirect, url_for, flash
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
import os

app = Flask(__name__)
app.config['SECRET_KEY'] = os.urandom(24)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///game.db'
db = SQLAlchemy(app)
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

# 玩家模型
class Player(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password = db.Column(db.String(120), nullable=False)
    
    # 基础属性
    level = db.Column(db.Integer, default=1)
    exp = db.Column(db.Integer, default=0)
    gold = db.Column(db.Integer, default=1000)
    
    # 魔法属性
    strength = db.Column(db.Integer, default=10)  # 力量
    agility = db.Column(db.Integer, default=10)   # 敏捷
    constitution = db.Column(db.Integer, default=10)  # 体质
    intelligence = db.Column(db.Integer, default=10)  # 智力
    spirit = db.Column(db.Integer, default=10)    # 精神
    charm = db.Column(db.Integer, default=10)     # 魅力
    
    # 状态
    hp = db.Column(db.Integer, default=100)       # 体力
    mp = db.Column(db.Integer, default=100)       # 魔力
    
    # 元素亲和力
    wind_affinity = db.Column(db.Integer, default=0)   # 风元素亲和力
    fire_affinity = db.Column(db.Integer, default=0)   # 火元素亲和力
    water_affinity = db.Column(db.Integer, default=0)  # 水元素亲和力
    earth_affinity = db.Column(db.Integer, default=0)  # 土元素亲和力

@login_manager.user_loader
def load_user(user_id):
    return Player.query.get(int(user_id))

# 路由
@app.route('/')
def index():
    return render_template('index.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        user = Player.query.filter_by(username=username).first()
        if user and user.password == password:
            login_user(user)
            return redirect(url_for('game'))
        flash('用户名或密码错误')
    return render_template('login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        if Player.query.filter_by(username=username).first():
            flash('用户名已存在')
            return redirect(url_for('register'))
        new_player = Player(username=username, password=password)
        db.session.add(new_player)
        db.session.commit()
        flash('注册成功，请登录')
        return redirect(url_for('login'))
    return render_template('register.html')

@app.route('/game')
@login_required
def game():
    return render_template('game.html')

@app.route('/laboratory')
@login_required
def laboratory():
    return render_template('laboratory.html')

@app.route('/study')
@login_required
def study():
    return render_template('study.html')

@app.route('/shop')
@login_required
def shop():
    return render_template('shop.html')

@app.route('/profile')
@login_required
def profile():
    return render_template('profile.html')

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True) 