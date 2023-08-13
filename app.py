from flask import Flask, redirect, render_template, request
from flask_sqlalchemy import SQLAlchemy
from flask_login import (
    LoginManager,
    UserMixin,
    login_user,
    logout_user,
    login_required,
    current_user,
)
from werkzeug.security import generate_password_hash, check_password_hash
from sqlalchemy import or_
import os
import uuid


app = Flask(__name__)
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///test.db"
app.config["SECRET_KEY"] = os.urandom(24)
db = SQLAlchemy(app)
login_manager = LoginManager()
login_manager.init_app(app)


class Tweet(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(20), nullable=False)
    body = db.Column(db.String(140), nullable=False)


class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), nullable=False, unique=True)
    password = db.Column(db.String(25))


def create_user_table():
    with app.app_context():
        db.create_all()


create_user_table()


@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


@app.route("/")
def index():
    tweets = Tweet.query.all()
    text_input = request.args.get("search")
    if text_input is None or len(text_input) == 0:
        tweets = Tweet.query.all()
    else:
        tweets = (
            db.session.query(Tweet)
            .filter(or_(Tweet.body.like(text_input), Tweet.title.like(text_input)))
            .all()
        )
    return render_template("/index.html", tweets=tweets)


@app.route("/new", methods=["GET", "POST"])
def create():
    if request.method == "POST":
        # POSTメソッドの時の処理。
        title = request.form.get("title")
        body = request.form.get("body")
        tweet = Tweet(title=title, body=body)
        # DBに値を送り保存する
        db.session.add(tweet)
        db.session.commit()
        return redirect("/")
    else:
        # GETメソッドの時の処理
        return render_template("/new.html")


@app.route("/<int:id>/edit", methods=["GET", "POST"])
def update(id):
    tweets = Tweet.query.get(id)
    if request.method == "GET":
        return render_template("/edit.html", tweet=tweets)
    else:
        tweets.title = request.form.get("title")
        tweets.body = request.form.get("body")
        db.session.commit()
        return redirect("/")


@app.route("/<int:id>/delete", methods=["GET"])
def delete(id):
    tweets = Tweet.query.get(id)

    db.session.delete(tweets)

    db.session.commit()
    return redirect("/")


@app.route("/signup", methods=["GET", "POST"])
def signup():
    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")
        # Userのインスタンスを作成
        user = User(
            username=username,
            password=generate_password_hash(password, method="sha256"),
        )
        db.session.add(user)
        db.session.commit()
        return redirect("login")
    else:
        return render_template("signup.html")


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")
        # Userテーブルからusernameに一致するユーザを取得
        user = User.query.filter_by(username=username).first()
        if check_password_hash(user.password, password):
            login_user(user)
            return redirect("/")
        else:
            # ユーザーが存在しないか、パスワードが一致しない場合の処理
            return render_template("login.html", error="無効なユーザー名またはパスワードです")
    else:
        return render_template("login.html")


reset_password_tokens = {}
registered_emails = ["user1@example.com", "user2@example.com", "user3@example.com"]


@app.route("/reset_password", methods=["GET", "POST"])
def reset_password():
    if request.method == "POST":
        email = request.form["email"]

        # 仮に登録済みのメールアドレスがあるとする
        if email in registered_emails:
            # トークンを生成し、辞書に保存
            token = str(uuid.uuid4())
            reset_password_tokens[token] = email

            # トークンを含むリンクを送信するなどの処理
            # メール送信コードは省略

            # パスワード再設定用のページにリダイレクト
            return redirect("reset_password.html")

        # メールアドレスが登録されていない場合、エラーメッセージを表示
        error_message = "登録されていないメールアドレスです。"
        return render_template("reset_password.html", error_message=error_message)

    return render_template("reset_password.html")


@app.route("/reset_password/<token>", methods=["GET", "POST"])
def reset_password_form(token):
    if token in reset_password_tokens:
        if request.method == "POST":
            new_password = request.form["new_password"]

            # パスワードの再設定処理
            email = reset_password_tokens[token]
            # ここでパスワードの再設定処理を行う（例：データベースに新しいパスワードを保存する）

            # パスワード再設定完了のメッセージを表示するなどの処理
            success_message = "パスワードを再設定しました。"
            return render_template(
                "password_reset_success.html", success_message=success_message
            )

        return render_template("reset_password_form.html", token=token)

    # トークンが無効な場合、エラーメッセージを表示
    error_message = "無効なトークンです。"
    return render_template("password_reset_error.html", error_message=error_message)


@app.route("/logout")
@login_required
def logout():
    logout_user()
    return redirect("login")


if __name__ == "__main__":
    app.run(debug=True)
