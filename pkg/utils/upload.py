import os
import secrets
from werkzeug.utils import secure_filename
from flask import current_app


ALLOWED_NIN_EXTENSIONS = {"pdf", "jpg", "jpeg", "png"}
ALLOWED_NIN_MIME_TYPES = {
    "application/pdf",
    "image/jpeg",
    "image/png",
}


def save_nin_document(file):
    """
    Save uploaded NIN document with a unique filename.
    Returns the relative path to store in the database.
    """

    if not file or not getattr(file, "filename", ""):
        raise ValueError("NIN document is required.")

    secured_name = secure_filename(file.filename)
    _, extension = os.path.splitext(secured_name)
    extension = extension.lower().lstrip(".")

    if extension not in ALLOWED_NIN_EXTENSIONS:
        raise ValueError("Only PDF, JPG, JPEG and PNG files are allowed.")

    content_type = (getattr(file, "mimetype", "") or "").lower()
    if content_type and content_type not in ALLOWED_NIN_MIME_TYPES:
        raise ValueError("Unsupported NIN document format.")

    max_bytes = int(current_app.config.get("MAX_UPLOAD_FILE_BYTES", 5 * 1024 * 1024))
    file.stream.seek(0, os.SEEK_END)
    file_size = file.stream.tell()
    file.stream.seek(0)
    if file_size > max_bytes:
        raise ValueError(f"NIN document exceeds the maximum upload size of {max_bytes // (1024 * 1024)}MB.")

    filename = f"{secrets.token_hex(16)}.{extension}"

    upload_root = current_app.config.get("UPLOAD_FOLDER", "private_uploads")
    if not os.path.isabs(upload_root):
        upload_root = os.path.abspath(os.path.join(current_app.root_path, "..", upload_root))

    folder = os.path.join(upload_root, "host_documents", "nin")

    os.makedirs(folder, exist_ok=True)

    filepath = os.path.join(folder, filename)

    file.save(filepath)

    return os.path.join(
        "host_documents",
        "nin",
        filename
    )