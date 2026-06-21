# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Overview

Django academic-journal site for *jurnal-komparativistika.uz* (a comparative literature / critical studies journal). Trilingual (Uzbek default, plus English and Russian), SQLite-backed, with CKEditor rich-text content and a Django-admin-driven content model.

## Commands

```bash
# Run dev server
python manage.py runserver

# Migrations
python manage.py makemigrations
python manage.py migrate

# Tests (each app has a tests.py; most are empty stubs)
python manage.py test            # all
python manage.py test issue      # one app
python manage.py test issue.tests.SomeTestCase.test_method   # single test

# Seeding (custom management commands, defined in core/management/commands/)
python manage.py setup_journal                          # full reset: seed_db --clear + articles + subscribers
python manage.py setup_journal --articles 50 --subscribers 100
python manage.py seed_db --clear                        # core/Default settings, about, issues, etc.
python manage.py seed_articles --count 25
python manage.py seed_subscribers --count 50

# Translations (see i18n section)
python manage.py makemessages -l uz -l en -l ru
python manage.py compilemessages
```

There is no requirements pin for the dev DB; `db.sqlite3` is gitignored. `db_old.sqlite3` is a committed snapshot — do not assume it is the live database.

## Architecture

Project package is `config/` (settings, urls, wsgi/asgi). Five domain apps, each a thin Django app (models + admin + translation + urls + views):

- **core** — home page (`index` → `journal_home.html`), mailing-list `join` form, and two cross-cutting models: `Joining` (mailing-list signups) and `Default` (site-wide key/value config, see below). Also holds all seed commands.
- **issue** — the heart of the content model. `Issue` = a journal volume/issue; `JournalIssue` = an individual article (FK to `Issue`). Despite the name, **`JournalIssue` is an article**. Sitemaps live here.
- **about / submit / subscribe** — each holds one CKEditor-content model (`About`, `Permission`, `Subscribe`) rendered as static-ish editorial pages.

### Site config via the `Default` model + context processor

`core.context_processors.site_context` (registered in `TEMPLATES`) runs on every request. It loads all `Default` rows into a `{name: value}` dict and exposes `site_config` plus many named keys (`site_title`, `publisher`, `issn_print`, `editor_in_chief`, `google_analytics_id`, etc.) with hardcoded fallbacks. **To add a new site-wide setting**: add a `Default` row (via admin or a seed command) and read it in the context processor — templates do not query the DB directly for these. The whole processor is wrapped in try/except so the site renders even with an empty DB.

### Internationalization (django-modeltranslation + rosetta)

This is the most load-bearing cross-cutting concern.

- `LANGUAGE_CODE = 'uz'`, languages = uz/en/ru. All page URLs are wrapped in `i18n_patterns` (config/urls.py), so they carry a `/uz/`, `/en/`, `/ru/` prefix. `admin/`, `rosetta/`, `sitemap.xml`, `robots.txt` are *not* prefixed.
- Each app has a `translation.py` registering translatable model fields with `modeltranslation`. **Adding a translatable field means: edit the model, edit that app's `translation.py`, then `makemigrations`/`migrate`** — modeltranslation generates per-language columns (`title_uz`, `title_en`, `title_ru`).
- Translations are edited live at `/rosetta/` (admin login required). `config/rosetta_reload_patch.py` (imported at the top of settings.py) monkeypatches Rosetta's `translate` view to flush Django's translation cache after a save, so edits take effect without a restart.

### CKEditor

Rich text uses `ckeditor.fields.RichTextField`. Two configs in settings: `default` (full toolbar) and `subscription_editor` (curated toolbar). Uploads go to `media/uploads/` (`CKEDITOR_UPLOAD_PATH`).

### Google Scholar citations (optional)

`JournalIssue.update_scholar_metadata()` fetches citation counts via the `scholarly` package, which is **not in requirements.txt** — the method degrades gracefully ("scholarly not installed") if absent. It self-throttles to once per day unless `force=True`.

## Conventions / gotchas

- `config/settings.py` docstrings say Django 5.2 but `requirements.txt` pins **Django 4.2.23**; follow the pin.
- `DEBUG = True` and a checked-in `SECRET_KEY` / `ALLOWED_HOSTS = ["...", "*"]` are committed — production hardening is not done in this repo.
- Templates live in a single top-level `templates/` dir (set via `TEMPLATES['DIRS']`), not per-app. `templates/components/` holds reusable sidebar/accordion partials. Note the misspelled dir `templates/sumbit/`.
- Several models override `db_table` (`issue`, `joining`, `default`, …) — table names don't match the `app_model` default.
- Article view counts: `article_detail` increments `views` atomically with `F('views') + 1`.
