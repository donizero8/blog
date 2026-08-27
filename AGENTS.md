# Repository instructions

## Project scope

Maintain **Dony’s Notebook**, an Indonesian-language Django blog running in Docker with PostgreSQL. Preserve the existing clean public design, WordPress-inspired admin login, Medium-style editor, tag chips, and moderated comments.

## Architecture

- `config/`: Django settings, root URLs, and WSGI entry point.
- `blog/models.py`: `Post`, `Tag`, `Comment`, `Book`, `BookNote`, and singleton `SiteProfile` domain models.
- `blog/forms.py`: sanitized post form, tag handling, and public comment form.
- `blog/admin.py`: admin configuration and comment moderation actions.
- `blog/widgets.py`: custom editor and tag widgets.
- `blog/templates/`: templates owned by custom form widgets. Keep widget templates here because Django's form renderer may not find project-level widget templates.
- `templates/`: public pages and the custom admin login.
- `blog/static/blog/`: public CSS and admin editor/tag/login assets.
- `blog/migrations/`: committed schema migrations; never edit an applied migration to represent a new schema change.
- `compose.yaml` and `Dockerfile`: PostgreSQL and Gunicorn runtime.

## Implementation rules

- Keep UI copy in Indonesian unless the user explicitly requests another language.
- Do not add image-upload functionality unless explicitly requested.
- Keep post HTML sanitized through `bleach`; extend `ALLOWED_TAGS` and allowed attributes deliberately when adding editor formats.
- Render only sanitized post HTML with `|safe`. Keep comments escaped; never render comment content with `|safe`.
- Keep new comments unapproved by default. Public queries must expose only `is_approved=True` comments.
- Never display commenter email addresses publicly.
- Keep `SiteProfile` as a singleton and store uploaded profile photos under the persistent media volume; do not add uploads to post content.
- Preserve case-insensitive tag reuse and the maximum of 12 tags per post.
- Avoid external CDN dependencies for admin widgets. Keep editor behavior usable with keyboard and mobile layouts.
- Use `select_related`/`prefetch_related` when adding related data to public list or detail pages.
- Add database indexes only when query patterns justify them; accompany model changes with a new migration.
- Store secrets in environment variables. Do not commit `.env`, credentials, database dumps, or generated `staticfiles/`.
- Preserve existing user data and PostgreSQL volumes during routine rebuilds. Do not run `docker compose down -v` unless the user explicitly requests data deletion.

## Change workflow

1. Inspect the relevant model, form, view, admin, template, static asset, and latest migration before editing.
2. Make the smallest coherent change and create a new migration for schema updates.
3. Run lightweight syntax checks before rebuilding.
4. Rebuild with `docker compose up --build -d` when Python, templates, or static assets change because source files are copied into the image rather than bind-mounted.
5. Confirm that PostgreSQL is healthy, migrations ran, static files were collected, and Gunicorn started.
6. Test the changed endpoint or form. For write-path tests, prefer a database transaction that is rolled back after assertions.
7. Report what changed, verification results, and any required hard refresh.

## Validation commands

```bash
python3 -m compileall -q config blog manage.py
node --check blog/static/blog/admin/editor.js
node --check blog/static/blog/admin/tags.js
docker compose config --quiet
docker compose up --build -d
docker compose exec -T web python manage.py check
docker compose exec -T web python manage.py showmigrations --plan
docker compose ps
docker compose logs --no-color --tail=80 web
curl -fsS http://127.0.0.1:8000/ >/dev/null
```

Run only the checks relevant to the change, but always run `manage.py check` after Django changes. If Docker Desktop is stopped, start it and wait for `docker info` to succeed before retrying Compose.
