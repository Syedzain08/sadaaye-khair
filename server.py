from flask import Flask, render_template, send_from_directory, abort
from flask_frozen import Freezer
from os import path, listdir
from markdown import markdown
from yaml import safe_load
from utils import *

app = Flask(__name__)
freezer = Freezer(app)

CONTENT_DIR = "content"


# --- Home page ---
@app.route("/")
def index():
    show_intiative_card = True
    blogs = []
    for slug in listdir(CONTENT_DIR):
        folder = path.join(CONTENT_DIR, slug)
        md_file = path.join(folder, f"{slug}.md")
        if path.isdir(folder) and path.exists(md_file):
            with open(md_file, "r", encoding="utf-8") as f:
                raw = f.read()
            if raw.startswith("---"):
                _, fm, _ = raw.split("---", 2)
                front = safe_load(fm)
            else:
                front = {}

            # Get thumbnail
            thumb_raw = front.get("thumbnail", "")
            if isinstance(thumb_raw, list):
                thumbnail = clean_thumbnail(thumb_raw)
            else:

                thumbnail = (
                    thumb_raw.replace("[[", "")
                    .replace("]]", "")
                    .replace('"', "")
                    .replace("'", "")
                )

            blogs.append(
                {
                    "slug": slug,
                    "title": front.get("title", slug.title()),
                    "description": front.get("description", ""),
                    "thumbnail": thumbnail,
                    "date": front.get("date", ""),
                }
            )

    return render_template(
        "index.html", show_intiative_card=show_intiative_card, blogs=blogs
    )


@app.route("/our-team/")
def our_team():
    return render_template("our_team.html")


# --- Article page ---
@app.route("/articles/<slug>/")
def article(slug):
    md_dir = path.join(CONTENT_DIR, slug)
    md_file = path.join(md_dir, f"{slug}.md")

    if not path.exists(md_file):
        abort(404)

    # --- Read Markdown ---
    with open(md_file, "r", encoding="utf-8") as f:
        raw = f.read()

    # --- Parse YAML frontmatter ---
    if raw.startswith("---"):
        _, fm, body = raw.split("---", 2)
        front = safe_load(fm)
    else:
        front = {}
        body = raw

    # --- Convert Obsidian syntax ---
    body = convert_obsidian_images(body, slug)
    body = convert_obsidian_links(body)

    # --- Convert Markdown → HTML ---
    html_body = markdown(body, extensions=["extra", "fenced_code", "toc", "sane_lists"])

    return render_template(
        "article_template.html",
        title=front.get("title", slug.title()),
        date=front.get("date", "Unknown date"),
        description=front.get("description", ""),
        content=html_body,
    )


# --- Serve assets from content folder ---
@app.route("/content/<slug>/<path:filename>")
def article_assets(slug, filename):
    dir_path = path.join(CONTENT_DIR, slug)
    return send_from_directory(dir_path, filename)


# --- Freezer generator for assets ---
@freezer.register_generator
def article_assets():
    for slug in listdir(CONTENT_DIR):
        folder = path.join(CONTENT_DIR, slug)
        if path.isdir(folder):
            for filename in listdir(folder):
                yield {"slug": slug, "filename": filename}


# --- Freezer generator ---
@freezer.register_generator
def article():
    """
    Generate pages for every folder inside /content
    """
    for entry in listdir(CONTENT_DIR):
        full = path.join(CONTENT_DIR, entry)
        if path.isdir(full):
            yield {"slug": entry}


# --- Freeze site ---
if __name__ == "__main__":
    freezer.init_app(app)
    freezer.freeze()
