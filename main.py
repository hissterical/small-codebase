import os

from flask import Flask, redirect, render_template, request, url_for

from gcp_storage import GCSImageStore
from sql_notes import SQLNoteStore


app = Flask(__name__)


def _get_store() -> GCSImageStore:
    folder = os.getenv("FOLDER", "uploads")
    return GCSImageStore(folder=folder)


def _get_note_store() -> SQLNoteStore:
    return SQLNoteStore()


@app.get("/")
def index():
    store = _get_store()
    image_urls = store.list_image_urls()
    notes: list[dict[str, str]] = []
    try:
        note_store = _get_note_store()
        notes = note_store.list_notes()
    except ValueError:
        # Keep page functional when DATABASE_URL is not configured yet.
        notes = []
    return render_template("index.html", images=image_urls, notes=notes)


@app.post("/upload")
def upload():
    file = request.files.get("image")
    if file and file.mimetype and file.mimetype.startswith("image/"):
        store = _get_store()
        store.upload_image(file)
    return redirect(url_for("index"))


@app.post("/notes")
def add_note():
    content = request.form.get("note", "")
    try:
        note_store = _get_note_store()
        note_store.add_note(content)
    except ValueError:
        pass
    return redirect(url_for("index"))


if __name__ == "__main__":
    app.run(debug=True)
