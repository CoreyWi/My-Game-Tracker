# GameShelf — Game Library Tracker for Cartridge & Crate Games

GameShelf is a Django web app built for **Cartridge & Crate Games**, a (fictional) local
new-and-used video game store. Store loyalty members get a free GameShelf account where they
log the games they own and track their progress in each one:

| Status | Meaning |
|---|---|
| New | Owned but not started |
| Incomplete | Started, in progress |
| Completed | Beaten at least once |
| 100% Completed | Everything done (all collectibles/achievements) |
| Forgotten | Dropped or set aside |

Every time a member beats a game, GameShelf adds one to its **times beaten** count and saves a
dated entry in the game's **completion history**.

## Features
- Member sign-up, log in, log out (each member only sees their own shelf)
- Add, edit, and remove games; add a new platform right from the form
- One-click status change, "+1 Beat", and "Mark 100%"
- Dashboard: count per status, % finished, total beats, backlog size, most-replayed games
- Search by title and filter by status or platform
- Staff admin site (`/admin/`) for store employees to manage platforms and help members
- 24 automated tests

## Tech
Python 3.12–3.14, Django 6.1, SQLite.

## Run it (Windows / VS Code terminal)
```
cd gameshelf_project
python -m venv venv
venv\Scripts\activate
pip install -r ..\requirements.txt
python manage.py migrate
python manage.py seed_demo          # platforms + demo member
python manage.py createsuperuser    # optional: staff admin login
python manage.py runserver
```
Open http://127.0.0.1:8000/ and log in as **demo** / **GameShelf2026!**, or sign up as a new member.

Run the tests: `python manage.py test`

## Project layout
```
gameshelf_project/
  manage.py
  gameshelf_project/     settings.py, urls.py (project config)
  tracker/               the app
    models.py            Platform, Game, CompletionLog (database tables)
    library.py           GameLibrary class: stats, filtering, grouping (lists/dicts/tuples)
    forms.py             GameForm, BeatForm, SignUpForm
    views.py             page logic
    urls.py              page addresses
    admin.py             staff admin setup
    tests.py             automated tests
    templates/           HTML pages
    static/tracker/      style.css
    management/commands/seed_demo.py
```
