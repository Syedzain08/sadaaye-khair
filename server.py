from flask import Flask, render_template
from flask_frozen import Freezer
import os

app = Flask(__name__)
freezer = Freezer(app)


# --- Home page ---
@app.route("/")
def index():
    show_intiative_card = True
    return render_template("index.html", show_intiative_card=show_intiative_card)


# --- Article page ---
@app.route("/articles/<slug>/")
def articles(slug):
    """
    Render a pre-rendered HTML blog post from templates/articles/<slug>/index.html
    """
    article_index_file = f"articles/{slug}/index.html"
    full_path = os.path.join(app.template_folder, article_index_file)

    if not os.path.exists(full_path):

        return "Article not found", 404

    return render_template(
        "article_template.html",
        title=slug.replace("-", " ").title(),  # placeholder title
        date="2025-11-23",  # placeholder date
        content=render_template(article_index_file),
    )


# --- Freezer generator ---
@freezer.register_generator
def articles():
    """
    Tell Flask-Freeze which slugs to generate.
    Scans templates/articles/ for directories.
    """
    articles_dir = os.path.join(app.template_folder, "articles")
    for entry in os.listdir(articles_dir):
        full_path = os.path.join(articles_dir, entry)
        if os.path.isdir(full_path):
            yield {"slug": entry}


# --- Freeze site ---
if __name__ == "__main__":
    freezer.init_app(app)
    freezer.freeze()
