from flask import Flask, render_template, send_from_directory, abort, url_for, Response
from flask_frozen import Freezer
from os import path, listdir
from markdown import markdown
from yaml import safe_load
from utils import *
from shutil import copy

app = Flask(__name__)
freezer = Freezer(app)

CONTENT_DIR = "content"


# --- Home page ---
@app.route("/")
def index():
    show_intiative_card = False
    initiative_description = "Supporting underprivileged communities through education and healthcare initiatives."

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
        "index.html",
        show_intiative_card=show_intiative_card,
        initiative_description=initiative_description,
        blogs=blogs,
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


@app.route("/donate/")
def donate():
    return render_template("donate.html")


# --- Sitemap Route---- #
@app.route("/sitemap.xml")
def sitemap():
    urls = [
        {"loc": url_for("index", _external=True), "priority": "1.0"},
        {"loc": url_for("our_team", _external=True), "priority": "0.8"},
        {"loc": url_for("donate", _external=True), "priority": "0.8"},
    ]

    # Add all articles to sitemap
    for slug in listdir(CONTENT_DIR):
        folder = path.join(CONTENT_DIR, slug)
        if path.isdir(folder):
            md_file = path.join(folder, f"{slug}.md")
            if path.exists(md_file):
                urls.append(
                    {
                        "loc": url_for("article", slug=slug, _external=True),
                        "priority": "0.6",
                    }
                )

    xml = ['<?xml version="1.0" encoding="UTF-8"?>']
    xml.append('<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">')
    for url in urls:
        xml.append("  <url>")
        xml.append(f"    <loc>{url['loc']}</loc>")
        xml.append(f"    <priority>{url['priority']}</priority>")
        xml.append("  </url>")
    xml.append("</urlset>")

    return Response("\n".join(xml), mimetype="text/xml")


# --- Robots.txt Route ---#
@app.route("/robots.txt")
def robots_txt():
    lines = [
        "User-Agent: *",
        "Disallow:",
        f"Sitemap: {url_for('sitemap', _external=True)}",
    ]
    return Response("\n".join(lines), mimetype="text/plain")


@app.route("/404/")
def not_found():
    return render_template("404.html")


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
    app.config["FREEZER_BASE_URL"] = "https://sadaaye-khair.vercel.app/"
    freezer.init_app(app)
    freezer.freeze()
    copy("build/404/index.html", "build/404.html")
