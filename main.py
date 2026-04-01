import os

from flask import Flask, redirect, render_template, request, url_for

from gcp_storage import GCSImageStore


app = Flask(__name__)


def _get_store() -> GCSImageStore:
    folder = os.getenv("GCS_FOLDER", "uploads")
    return GCSImageStore(folder=folder)


@app.get("/")
def index():
    store = _get_store()
    image_urls = store.list_image_urls()
    return render_template("index.html", images=image_urls)


@app.post("/upload")
def upload():
    file = request.files.get("image")
    if file and file.mimetype and file.mimetype.startswith("image/"):
        store = _get_store()
        store.upload_image(file)
    return redirect(url_for("index"))


if __name__ == "__main__":
    app.run(debug=True)
