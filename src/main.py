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
# IMPLEMENT GAMEPLAY:
#### SET ROUNDS, CHOOSE PLAYER TURNS, SHOW ARTICLE INFORMATION


class Users(db.Model):
    _id = db.Column("id", db.Integer, primary_key=True)
    nickname = db.Column(db.String(1000))
    roomname = db.Column(db.String(1000))
    is_admin = db.Column(db.Boolean())
    activated = db.Column(db.Boolean())

    def __init__(self, nickname, roomname, is_admin):
        self.nickname = nickname
        self.roomname = roomname
        self.is_admin = is_admin
        self.activated = False


class Rooms(db.Model):
    _id = db.Column("id", db.Integer, primary_key=True)
    roomname = db.Column(db.String(1000))
    passcode = db.Column(db.String(1000))
    activated = db.Column(db.Boolean())

    def __init__(self, roomname, passcode, activated):
        self.roomname = roomname
        self.passcode = passcode
        self.activated = activated


class Wiki(db.Model):
    _id = db.Column("id", db.Integer, primary_key=True)
    title = db.Column(db.String(1000))
    description = db.Column(db.String(100000))

    def __init__(self, title, description):
        self.title = title
        self.description = description


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
        session["is_admin"] = False

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
        session["is_admin"] = True

        if (Rooms.query.filter_by(roomname=roomname).first() != None):
            flash("Room name in use!", "info")
            return render_template("create.html")
        else:
            room = Rooms(roomname, passcode, False)
            db.session.add(room)
            db.session.commit()
            return redirect(url_for("nickname", rn=roomname))
    else:
        return render_template("create.html")


@app.route("/room/<rn>", methods=["GET", "POST"])
def room(rn):
    game_start = request.method == "POST"
    user_list = Users.query.filter_by(roomname=rn).all()
    room = Rooms.query.filter_by(roomname=rn).first()
    print(session["nickname"])

    for user in user_list:
        flash(f"{user.nickname} is here!", "message")

    if not game_start and not room.activated:
        return render_template("room.html", adminbutton = session["is_admin"])
    else:
        room.activated = True
        db.session.commit()
        return redirect(url_for("game", rn=rn))


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


@app.route("/game/<rn>", methods=["GET", "POST"])
def game(rn):
    this_user_nickname = session["nickname"]
    user_list = Users.query.filter_by(roomname=rn).all()
    this_user = Users.query.filter_by(nickname=this_user_nickname).first()
    this_user.activated = True
    db.session.commit()
    all_activated = False

    while not all_activated:
        db.session.commit()
        all_activated = True

        for user in user_list:
            if not user.activated:
                all_activated = False

    return render_template("game.html")


"""
def thread(num):
    for i in range(num):
        print("running")
        sleep(1)
"""


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


"""
def parseWiki():
    file = open("wiki.txt", "r")

    line = file.readline()

    for i in range(16907):
        line = file.readline()
        chunks = line.split(" ||| ")
        wiki = Wiki(chunks[0], chunks[1])
        db.session.add(wiki)
        db.session.commit()

    print('Done!')
    file.close()
"""


if __name__ == "__main__":
    db.create_all()
    clear_db()
    #parseWiki()
    app.run(debug=True)