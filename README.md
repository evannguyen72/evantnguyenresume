# evantnguyenresume

Evan Thanh Nguyen's portfolio. **Python** builds the website from a **SQLite (SQL) database**,
and **GitHub Actions** publishes it to **GitHub Pages** every time you push.

```
database/schema.sql      table definitions (projects, tags, project_tags, experience, education, skill_usage view)
database/seed.sql        starting data, loaded once
database/portfolio.db    the live database (commit this file)
database/dump.sql        readable SQL copy of the database, rewritten on every change
db.py                    all SQL queries and writes
manage.py                command line for adding, editing and deleting projects
build.py                 renders templates/index.html.j2 with data from the database into ./site
templates/index.html.j2  page template (Jinja2)
static/                  styles.css and app.js (skill map, filters, project details)
.github/workflows/       builds and deploys the site on every push to main
```

## 1. One-time setup on your PC

Install Python 3.12+ from https://www.python.org/downloads/ (tick **Add Python to PATH**) and
Git from https://git-scm.com/download/win. Then in PowerShell:

```powershell
cd C:\Users\frien\evantnguyenresume-site
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
python build.py --serve          # creates database/portfolio.db and opens a preview at http://localhost:8000
```

## 2. Put it on GitHub

1. Create a free account at https://github.com. Naming it **evantnguyenresume** gives you the address
   **https://evantnguyenresume.github.io**.
2. Create a new **public** repository:
   - named `evantnguyenresume.github.io` for the address above, or
   - with any name (e.g. `resume`) for `https://<username>.github.io/resume/`.
3. Push this folder:
   ```powershell
   git init -b main
   git add .
   git commit -m "Portfolio site"
   git remote add origin https://github.com/<username>/<repository>.git
   git push -u origin main
   ```
4. On GitHub, open the repository's **Settings → Pages**, and under **Build and deployment → Source** pick **GitHub Actions**.
5. Open the **Actions** tab. When the "Build and deploy site" run turns green, the site is live.

## 3. Add or change projects

```powershell
python manage.py add          # answers a few questions and saves to the database
python manage.py list         # shows every project with its id
python manage.py edit 2       # change project 2
python manage.py feature 2    # pin/unpin project 2 to the front
python manage.py delete 2
python manage.py skills       # projects per skill, from the skill_usage SQL view
python manage.py sql "SELECT title, dates FROM projects ORDER BY created_at DESC"

python build.py --serve       # check it locally
git add . ; git commit -m "Add project" ; git push    # goes live in about a minute
```

Tag projects with the skill map's names (Python, SQL, JavaScript, Java, Bash, TCP/IP, Routing, DHCP,
Network Security, Linux, Windows, macOS, REST APIs, Gemini API, Log Analysis, AI Evaluation,
Troubleshooting, Documentation, Excel) to light up those nodes. Any other tag still shows as a filter.

Experience and education live in the `experience`, `experience_bullets` and `education` tables.
Change them with `python manage.py sql "UPDATE ..."` or with DB Browser for SQLite (https://sqlitebrowser.org).

## Custom domain (optional)

Buy a domain such as `evantnguyenresume.com`, then in **Settings → Pages → Custom domain** enter it and
follow GitHub's DNS instructions. Tick **Enforce HTTPS** once it's available.
