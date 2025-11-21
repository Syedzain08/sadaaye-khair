from flask import Flask, render_template
from flask_frozen import Freezer

app = Flask(__name__)
freezer = Freezer(app)


@app.route("/")
def index():
    return render_template("index.html")


if __name__ == "__main__":
    freezer.init_app(app)
    freezer.freeze()
