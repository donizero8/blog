# Editor browser regression tests

Start Docker with `docker compose up --build -d`, then run from the repository:

```sh
python3 tests/browser/editor_server.py
```

Open <http://localhost:8765/> in a browser. The page automatically runs the
suite and reports each assertion and a pass/fail total. Reload to rerun; Ctrl+C
stops the server. No additional Python or JavaScript dependencies are required.

The fixture renders the actual Django widgets from the running container and
serves the working-tree editor JavaScript. It runs separately from the admin
site, without authentication, database writes, or changes to admin drafts.
Rebuild/restart the fixture server after changing widget templates.

Coverage includes default, compact, and dynamically cloned inline editors:
format on/off, active button state, text preservation, hidden form value,
pointer event sequence, empty-editor typing, click activation after toolbar
focus, emoji insertion/dismissal, dialog opening, link removal, and isolation
between editors. It also checks repeated inline initialization, nested headings,
collapsed cursors in lists, and link creation, editing, removal, cancellation
and URL validation using the real link dialog.

These tests use the browser's real contenteditable, Selection and execCommand
implementations. Click activation and pointer sequences are dispatched by the
test script; they are not OS-level keyboard, touch, or layout tests.
Upload/network flows are outside
this suite. `manage.py test blog` runs the separate server-side tests.

## Floating save/delete actions

After rebuilding Docker, run `python3 -m http.server 8766 --bind 127.0.0.1 --directory tests/browser`
and open <http://localhost:8766/floating-actions.html>. The fixture loads the built
Django and application CSS from localhost:8000. It checks post/book action rows
at 1078, 768, and 390 pixels, at three scroll positions: equal button heights,
contained delete text, visible controls, and no action-row overflow. Expected:
`18 passed, 0 failed`. This fixture does not submit forms or change stored data.
