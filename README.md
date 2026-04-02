## Simple GCS Image Gallery

This app provides:

- one page with an image upload form
- a gallery grid showing images already stored in Google Cloud Storage

## Requirements

- Python 3.12+
- `uv` installed
- A Google Cloud Storage bucket
- GCP credentials available through Application Default Credentials

## Setup

Install dependencies:

```bash
uv sync
```

Set environment variables (PowerShell):

```powershell
$env:GCS_BUCKET_NAME="your-bucket-name"
$env:GCS_FOLDER="uploads"
```

If needed, also set your credentials path:

```powershell
$env:GOOGLE_APPLICATION_CREDENTIALS="C:\path\to\service-account.json"
```

## Run

```bash
uv run flask --app main run --debug
```

Open:

http://127.0.0.1:5000
