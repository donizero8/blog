"""Run with python3 tests/browser/editor_server.py, then open localhost:8765.

Renders the real Django widgets in Docker and tests the real editor script in
a browser. No database writes, login, browser driver, or npm packages required.
"""
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path
import subprocess

ROOT = Path(__file__).resolve().parents[2]
widgets = subprocess.check_output([
    "docker", "compose", "exec", "-T", "web", "python", "manage.py", "shell", "-c",
    "from blog.widgets import MediumEditorWidget; "
    "print('<form id=fixture>' + "
    "MediumEditorWidget().render('thoughts', '<p>Alpha beta</p>') + "
    "MediumEditorWidget(variant='compact').render('notes-0-body', '<p>Alpha beta</p>') + "
    "'<div class=empty-form>' + "
    "MediumEditorWidget(variant='compact').render('notes-__prefix__-body', '') + "
    "'</div></form>')",
], cwd=ROOT, text=True)
widgets = widgets[widgets.index('<form'):]


class Handler(BaseHTTPRequestHandler):
    def do_GET(self):
        assets = {
            '/editor.js': ROOT / 'blog/static/blog/admin/editor.js',
            '/tests.js': ROOT / 'tests/browser/editor.test.js',
        }
        if self.path in assets:
            body = assets[self.path].read_bytes()
            content_type = 'text/javascript'
        elif self.path == '/':
            body = ('''<!doctype html><html lang="en"><meta charset="utf-8">
<title>Editor toggle regression tests</title>
<style>textarea,.empty-form {display:none} .medium-canvas {border:1px solid #999;min-height:40px}
body {font:16px system-ui} .pass {color:green} .fail {color:red}</style>
<h1>Editor toggle regression tests</h1><p id="summary">Running…</p><ol id="results"></ol>
<script>
for (const name of ['thoughts', 'notes-0-body', 'notes-1-body']) {
  localStorage.removeItem(`dony-notebook:editor-draft:/:${name}`);
}
</script>''' + widgets + '''
<script src="/editor.js"></script><script src="/tests.js"></script></html>''').encode()
            content_type = 'text/html'
        else:
            self.send_error(404)
            return
        self.send_response(200)
        self.send_header('Content-Type', content_type + '; charset=utf-8')
        self.send_header('Cache-Control', 'no-store')
        self.end_headers()
        self.wfile.write(body)


if __name__ == '__main__':
    print('Open http://localhost:8765/ to run editor regression tests.', flush=True)
    HTTPServer(('127.0.0.1', 8765), Handler).serve_forever()
