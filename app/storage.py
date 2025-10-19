from __future__ import annotations

import secrets
import shutil
import subprocess
from datetime import datetime, timedelta
from pathlib import Path
from typing import BinaryIO

from flask import current_app


def _build_path(filename: str, suffix: str = '') -> Path:
    storage_dir = Path(current_app.config['STORAGE_DIR'])
    storage_dir.mkdir(parents=True, exist_ok=True)
    token = secrets.token_hex(8)
    return storage_dir / f"{datetime.utcnow():%Y%m%d}_{token}_{filename}{suffix}"


def save_upload(fileobj: BinaryIO, filename: str) -> Path:
    destination = _build_path(filename)
    with open(destination, 'wb') as f:
        shutil.copyfileobj(fileobj, f)
    return destination


def convert_to_pdf(path: Path) -> Path:
    if path.suffix.lower() == '.pdf':
        return path
    output_dir = path.parent
    command = ['soffice', '--headless', '--convert-to', 'pdf', '--outdir', str(output_dir), str(path)]
    subprocess.run(command, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    pdf_path = output_dir / (path.stem + '.pdf')
    if not pdf_path.exists():
        raise FileNotFoundError(pdf_path)
    return pdf_path


def purge_expired_files(storage_dir: Path, days: int = 30) -> None:
    threshold = datetime.utcnow() - timedelta(days=days)
    for item in storage_dir.iterdir():
        if item.is_file():
            if datetime.fromtimestamp(item.stat().st_mtime) < threshold:
                item.unlink(missing_ok=True)
