from flask import Flask, redirect, url_for, render_template, request, session, flash
from flask_sqlalchemy import SQLAlchemy

app = Flask(__name__)

app.secret_key = "acomplexstring"
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///users.sqlite3'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

# TODO: 
# IMPLEMENT ROOM USER RECOGNITION AND GAME FUNCTIONALITY
# CLEAN UP DATABASE AND SESSION STORAGE
# IMPLEMENT HTML INHERITENCE


class users(db.Model):
    _id = db.Column("id", db.Integer, primary_key=True)
    nickname = db.Column(db.String(1000))
    roomname = db.Column(db.String(1000))

    def __init__(self, nickname, roomname):
        self.nickname = nickname
        self.roomname = roomname


class rooms(db.Model):
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

        found_room = rooms.query.filter_by(roomname=roomname).first()

        session["nickname"] = nickname
        session["roomname"] = roomname
        session["passcode"] = passcode

        if (found_room != None and found_room.passcode != passcode):
            found_room = None

        if (found_room != None):
            return redirect(url_for("room"))
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

        if (rooms.query.filter_by(roomname=roomname).first() != None):
            flash("Room name in use!", "info")
            return render_template("create.html")
        else:
            room = rooms(roomname, passcode)
            db.session.add(room)
            db.session.commit()
            return redirect(url_for("nickname"))
    else:
        return render_template("create.html")


@app.route("/room", methods=["POST", "GET"])
def room():
    return render_template("room.html")


@app.route("/nickname", methods=["POST", "GET"])
def nickname():
    if request.method == "POST":
        nickname = request.form["nickname"]
        session["nickname"] = nickname
        return redirect(url_for("room"))
    else:
        return render_template("nickname.html")
    

def clear_db():
    usersin = users.query.all()

    for u in usersin:
        db.session.delete(u)

    roomsin = rooms.query.all()

    for r in roomsin:
        db.session.delete(r)

    db.session.commit()


if __name__ == "__main__":
    clear_db()
    db.create_all()
    app.run(debug=True)