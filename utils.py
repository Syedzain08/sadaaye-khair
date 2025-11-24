import re


def convert_obsidian_images(md_text, slug):
    """
    Convert ![[image.png]] → ![image.png](/content/<slug>/image.png)
    """

    def repl(m):
        filename = m.group(1)
        return f"![{filename}](/content/{slug}/{filename})"

    return re.sub(r"!\[\[([^\]]+)\]\]", repl, md_text)


def convert_obsidian_links(md_text):
    def repl(m):
        target = m.group(1)
        label = m.group(2) or target
        slug = target.lower().replace(" ", "-") + ".html"
        return f"[{label}]({slug})"

    return re.sub(r"\[\[([^]|]+)(?:\|([^]]+))?\]\]", repl, md_text)


def clean_thumbnail(thumbnail_list):
    """
    Convert Obsidian-style [[image.png]] → image.png
    """
    if not thumbnail_list:
        return None

    thumb = thumbnail_list[0]

    thumb = thumb.replace("[[", "").replace("]]", "").replace('"', "").replace("'", "")
    return thumb
