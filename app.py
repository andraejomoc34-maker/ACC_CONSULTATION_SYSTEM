from flask import Flask, render_template

from database import init_db

from routes.auth_routes import auth
from routes.admin_routes import admin
from routes.expert_routes import expert
from routes.student_routes import student


app = Flask(__name__)

app.config["SECRET_KEY"] = "acc-consultation-development-key"


app.register_blueprint(auth)
app.register_blueprint(admin)
app.register_blueprint(expert)
app.register_blueprint(student)


@app.route("/")
def home():
    return render_template("login.html")


@app.errorhandler(403)
def access_denied(error):
    return render_template("errors/403.html"), 403


@app.errorhandler(404)
def page_not_found(error):
    return render_template("errors/404.html"), 404


if __name__ == "__main__":

    init_db()

    app.run(
        debug=True,
        host="127.0.0.1",
        port=5000
    )