"""Build the static website from the SQLite database.

    python build.py            writes the site to ./site
    python build.py --serve    builds, then previews at http://localhost:8000

GitHub Actions runs `python build.py` on every push and publishes ./site to GitHub Pages.
"""

from __future__ import annotations

import argparse
import functools
import http.server
import json
import shutil
from datetime import date
from pathlib import Path

from jinja2 import Environment, FileSystemLoader, select_autoescape

import db

ROOT = Path(__file__).resolve().parent
OUT = ROOT / "site"


def safe_url(value: str) -> str:
    """Only allow https links into the page."""
    return value if value and db.HTTPS_URL.match(value) else ""


def json_for_script(data) -> str:
    """JSON that is safe to place inside a <script> tag."""
    return json.dumps(data, ensure_ascii=False).replace("<", "\\u003c")


def build() -> Path:
    conn = db.connect()
    try:
        projects = db.fetch_projects(conn)
        experience = db.fetch_experience(conn)
        education = db.fetch_education(conn)
        skills = db.fetch_skill_usage(conn)
    finally:
        conn.close()

    env = Environment(
        loader=FileSystemLoader(ROOT / "templates"),
        autoescape=select_autoescape(["html", "j2"]),
        trim_blocks=True,
        lstrip_blocks=True,
    )
    env.filters["safe_url"] = safe_url

    html = env.get_template("index.html.j2").render(
        projects=projects,
        projects_json=json_for_script(projects),
        experience=experience,
        education=education,
        skills=skills,
        year=date.today().year,
    )

    if OUT.exists():
        shutil.rmtree(OUT)
    (OUT / "static").mkdir(parents=True)
    (OUT / "index.html").write_text(html, encoding="utf-8")
    for f in (ROOT / "static").iterdir():
        if f.is_file():
            shutil.copy2(f, OUT / "static" / f.name)
    (OUT / ".nojekyll").write_text("", encoding="utf-8")  # tell GitHub Pages to serve files as-is

    print(f"Built {OUT / 'index.html'}: {len(projects)} project(s), {len(experience)} role(s), {len(skills)} skill tag(s).")
    return OUT


def serve(port: int) -> None:
    handler = functools.partial(http.server.SimpleHTTPRequestHandler, directory=str(OUT))
    with http.server.ThreadingHTTPServer(("127.0.0.1", port), handler) as httpd:
        print(f"Previewing at http://localhost:{port}  (Ctrl+C to stop)")
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            print("\nStopped.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Build the portfolio site.")
    parser.add_argument("--serve", action="store_true", help="preview the site after building")
    parser.add_argument("--port", type=int, default=8000)
    args = parser.parse_args()
    build()
    if args.serve:
        serve(args.port)
