from flask import Flask, redirect, url_for, render_template, request, session, flash
from flask_sqlalchemy import SQLAlchemy
from threading import Thread
from time import sleep
from random import randint

app = Flask(__name__)

app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///wikigame.sqlite3'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

# TODO: 
# UPDATE GAMEPLAY:
#### SET ROUNDS, IMPLEMENT A 'SHUFFLE' OR 'NEW ARTICLES' BUTTON, WAY FOR GUESSER TO PICK A USER THEY THINK IS TRUTHER


class Users(db.Model):
    _id = db.Column("id", db.Integer, primary_key=True)
    nickname = db.Column(db.String(1000))
    roomname = db.Column(db.String(1000))
    is_admin = db.Column(db.Boolean())
    activated = db.Column(db.Boolean())
    status = db.Column(db.String(10))

    def __init__(self, nickname, roomname, is_admin):
        self.nickname = nickname
        self.roomname = roomname
        self.is_admin = is_admin
        self.activated = False
        self.status = 'null'


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
    truth = db.Column(db.Boolean())

    def __init__(self, title, description):
        self.title = title
        self.description = description
        self.truth = False


@app.route("/")
def home():
    session.pop('_flashes', None)
    return render_template("index.html")


@app.route("/join", methods=["GET", "POST"])
def join():
    if request.method == "POST":
        session.permanent = True

        nickname = request.form["nickname"]
        roomname = request.form["roomname"]
        passcode = request.form["passcode"]

        found_room = Rooms.query.filter_by(roomname=roomname).first()

        if (found_room != None and found_room.passcode != passcode):
            found_room = None

        found_user = Users.query.filter_by(nickname=nickname).first()

        if found_user != None:
            flash("Username in use!")
            return render_template("join.html")

        if found_room != None:
            session["nickname"] = nickname
            session["roomname"] = roomname
            session["passcode"] = passcode
            session["is_admin"] = False
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

        if (Rooms.query.filter_by(roomname=roomname).first() != None):
            flash("Room name in use!", "info")
            return render_template("create.html")
        else:
            session["roomname"] = roomname
            session["passcode"] = passcode
            session["is_admin"] = True
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

        found_user = Users.query.filter_by(nickname=nickname).first()

        if found_user != None:
            flash("Username in use!")
            return render_template("nickname.html", rn=rn)

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

    truth_wikis = Wiki.query.filter_by(truth=True).all()

    for tw in truth_wikis:
        tw.truth = False

    db.session.commit()

    if session["is_admin"]:
            user_len = len(user_list)
            guesser_index = randint(0, user_len - 1)
            guesser = user_list[guesser_index]
            guesser.status = "guesser"

            user_list.pop(guesser_index)

            user_len = len(user_list)
            truther_index = randint(0, user_len - 1)
            truther = user_list[truther_index]
            truther.status = "truther"

            user_list.pop(truther_index)

            for u in user_list:
                u.status = "liar"

            truther_article = Wiki.query.filter_by(_id=randint(1, 16907)).first()
            truther_article.truth = True

            db.session.commit()

    
    all_status_set = False

    while not all_status_set:
        db.session.commit()
        all_status_set = True

        for u in user_list:
            if u.status == "null":
                all_status_set = False

    i_am_guesser = False
    i_am_truther = False

    if this_user.status == "guesser":
        i_am_guesser = True
    elif this_user.status == "truther":
        i_am_truther = True

    truther_article = Wiki.query.filter_by(truth=True).first()

    if i_am_truther:
        title = "You are the Truther!"
        description = "You have the true article! The Guesser is trying to find you! Explain your article to the best of your ability!"
        wiki_title = truther_article.title
        wiki_sum = truther_article.description
    elif i_am_guesser:
        title = "You are the Guesser!"
        description = "You are trying to find the person with the article title listed below! Interrogate your friends to find the Truther!"
        wiki_title = truther_article.title
        wiki_sum = ""
    else:
        wiki_target = Wiki.query.filter_by(_id=randint(1, 16907)).first()
        wiki_title = wiki_target.title
        wiki_sum = wiki_target.description
        title = "You are a Liar!"
        description = "Someone else has the true article! Pretend like you know what you're talking about. You may use this article to help with that!"

    return render_template("game.html", title=title, description=description, wiki_title=wiki_title, wiki_sum=wiki_sum)


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
        if chunks[1].endswith(':') or chunks[1].endswith(': '):
            continue
        wiki = Wiki(chunks[0], chunks[1])
        db.session.add(wiki)
        db.session.commit()

    print('Done!')
    file.close()
"""


if __name__ == "__main__":
    app.secret_key = str(randint(100, 1000000))
    db.create_all()
    clear_db()
    #parseWiki()
    app.run(debug=True)