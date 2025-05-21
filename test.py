import flask
import os

app = flask.Flask(__name__)


@app.route("/")
def home():
    return "home"


@app.route("/favicon.ico")
def favicon():
    print("sending favicon")
    path = os.path.abspath("assets/lyrX.png")
    if not os.path.exists(path):
        print("File does not exist:", path)
        return "not found", 404
    return flask.send_file(path, mimetype="image/png")


@app.errorhandler(404)
def not_found(e):
    print("404 handler triggered")
    return flask.render_template("404.html"), 404


if __name__ == "__main__":
    app.run("0.0.0.0", 5001, debug=True)
