from flask import Flask, redirect, url_for, render_template, request, session, flash
from flask_sqlalchemy import SQLAlchemy
from threading import Thread
from time import sleep

app = Flask(__name__)

app.secret_key = "acomplexstring"
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///wikigame.sqlite3'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

# TODO: 
# IMPLEMENT ROOM USER RECOGNITION AND GAME FUNCTIONALITY
# CLEAN UP DATABASE AND SESSION STORAGE
# IMPLEMENT HTML INHERITENCE


class Users(db.Model):
    _id = db.Column("id", db.Integer, primary_key=True)
    nickname = db.Column(db.String(1000))
    roomname = db.Column(db.String(1000))
    is_admin = db.Column(db.Boolean())

    def __init__(self, nickname, roomname, is_admin):
        self.nickname = nickname
        self.roomname = roomname
        self.is_admin = is_admin


class Rooms(db.Model):
    _id = db.Column("id", db.Integer, primary_key=True)
    roomname = db.Column(db.String(1000))
    passcode = db.Column(db.String(1000))

    def __init__(self, roomname, passcode):
        self.roomname = roomname
        self.passcode = passcode


@app.route("/")
def home():
    return render_template("index.html")


@app.route("/join", methods=["GET", "POST"])
def join():
    if request.method == "POST":
        session.permanent = True

        nickname = request.form["nickname"]
        roomname = request.form["roomname"]
        passcode = request.form["passcode"]

        found_room = Rooms.query.filter_by(roomname=roomname).first()

        session["nickname"] = nickname
        session["roomname"] = roomname
        session["passcode"] = passcode

        if (found_room != None and found_room.passcode != passcode):
            found_room = None

        if (found_room != None):
            user = Users(nickname, roomname, False)
            db.session.add(user)
            db.session.commit()
            return redirect(url_for("room", rn=roomname))
        else:
            flash("Incorrect Passcode or Room could not be found!", "info")
            return render_template("join.html")
    else:
        return render_template("join.html")


@app.route("/create", methods=["GET", "POST"])
def create():
    if request.method == "POST":
        session.permanent = True

        roomname = request.form["roomname"]
        passcode = request.form["passcode"]

        session["roomname"] = roomname
        session["passcode"] = passcode

        if (Rooms.query.filter_by(roomname=roomname).first() != None):
            flash("Room name in use!", "info")
            return render_template("create.html")
        else:
            room = Rooms(roomname, passcode)
            db.session.add(room)
            db.session.commit()
            return redirect(url_for("nickname", rn=roomname))
    else:
        return render_template("create.html")


@app.route("/room/<rn>", methods=["POST", "GET"])
def room(rn):
    waiting = True
    userlist = Users.query.filter_by(roomname=rn).all()
    for user in userlist:
        flash(f"{user.nickname} just joined!", "message")

    while waiting:
        return render_template("room.html")


@app.route("/nickname/<rn>", methods=["POST", "GET"])
def nickname(rn):
    if request.method == "POST":
        nickname = request.form["nickname"]
        session["nickname"] = nickname

        room = Rooms.query.filter_by(roomname=rn).first()

        user = Users(nickname, rn, True)
        db.session.add(user)
        db.session.commit()

        return redirect(url_for("room", rn=rn))
    else:
        return render_template("nickname.html")


def thread(num):
    for i in range(num):
        print("running")
        sleep(1)


def clear_db():
    usersin = Users.query.all()

    if (usersin != None):
        for u in usersin:
            db.session.delete(u)

    roomsin = Rooms.query.all()

    if (roomsin != None):
        for r in roomsin:
            db.session.delete(r)

    db.session.commit()


if __name__ == "__main__":
    db.create_all()
    clear_db()
    app.run(debug=True)