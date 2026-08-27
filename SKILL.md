---
name: maintain-django-blog
description: Maintain, extend, debug, and verify the Ruang Tulis Django blog in this repository, including Docker Compose, PostgreSQL, Django models and migrations, the Medium-style admin editor, tag chips, moderated comments, public templates, static assets, and the custom admin login. Use for feature work, bug fixes, schema changes, admin customization, UI changes, container startup, or testing requests concerning this project.
---

# Maintain Ruang Tulis

Work from the repository root and read `AGENTS.md` before making changes. Treat it as the authoritative repository policy.

## Understand the application

Use these boundaries:

- Keep domain data in `blog/models.py`: posts have an author and tags; comments belong to posts and require moderation.
- Keep validation and HTML sanitization in `blog/forms.py`.
- Keep public request handling in `blog/views.py` and routes in `blog/urls.py`.
- Keep admin behavior in `blog/admin.py`.
- Keep custom widgets in `blog/widgets.py`, their templates under `blog/templates/blog/admin/widgets/`, and their assets under `blog/static/blog/admin/`.
- Keep public layouts under `templates/` and public styles in `blog/static/blog/site.css`.
- Keep environment-specific settings in environment variables consumed by `config/settings.py`.

## Choose the workflow

### Change models or relationships

1. Update `blog/models.py`.
2. Add a new numbered migration under `blog/migrations/`; prefer `makemigrations` when the container is available.
3. Update related forms, admin, queries, and templates together.
4. Rebuild and confirm the migration applies without losing existing data.

Do not rewrite existing migrations for new changes. Avoid deleting or recreating the PostgreSQL volume.

### Change the Medium-style editor

Update the widget template, `editor.js`, and `editor.css` as a unit when behavior and presentation interact. Maintain all of the following:

- Synchronize the contenteditable canvas into the hidden textarea before form submission.
- Normalize ordinary content to paragraphs.
- Sanitize saved HTML with Bleach.
- Keep toolbar active states synchronized with the selection.
- Provide a clear way to enter and exit code blocks.
- Do not add image upload controls.

When adding a supported HTML format, update both editor behavior and `ALLOWED_TAGS`/attributes. Verify saved content as well as visual editing.

### Change tags

Preserve tag suggestions, Enter/comma chip creation, duplicate prevention ignoring case, removal controls, and automatic creation on post save. Keep the server-side maximum of 12 tags; do not rely only on JavaScript validation.

### Change comments

Keep public submissions unapproved by default. Show only approved comments, keep emails private, preserve CSRF protection and honeypot validation, and keep all public comment text escaped. Test both the hidden-before-approval and visible-after-approval states.

### Change admin or public UI

Keep visible copy in Indonesian and match the established typography and spacing. Use local static files rather than a CDN. Preserve responsive behavior. Rebuild the image so `collectstatic` includes changed assets, then advise a hard refresh when browser caching may hide changes.

### Start or diagnose Docker

1. Run `docker compose up --build -d`.
2. If the daemon is unavailable, start Docker Desktop and wait until `docker info` succeeds.
3. Run `docker compose ps` and require the database to be healthy and web service to be running.
4. Inspect `docker compose logs --no-color --tail=80 web` for migration, static collection, and Gunicorn startup results.
5. Request `http://127.0.0.1:8000/` and expect HTTP 200.

## Verify changes

Run focused checks first:

```bash
python3 -m compileall -q config blog manage.py
node --check blog/static/blog/admin/editor.js
node --check blog/static/blog/admin/tags.js
docker compose config --quiet
```

After rebuilding, run:

```bash
docker compose exec -T web python manage.py check
docker compose ps
docker compose logs --no-color --tail=80 web
```

Exercise the changed endpoint. Use Django's test client for authenticated admin pages. Wrap temporary database writes in `transaction.atomic()`, assert the outcome, call `transaction.set_rollback(True)`, and exit the transaction so verification leaves no test data.

## Finish

State the implemented outcome first. Summarize migrations and behavior changes, report concrete checks and HTTP status, and provide the relevant local URL. Mention a hard refresh only for changed browser assets.
