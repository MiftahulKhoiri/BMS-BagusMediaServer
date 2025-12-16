import os
import time
import uuid
import shutil
from flask import Blueprint, request, jsonify, session, render_template
from werkzeug.utils import secure_filename

from .upload_auth import fm_auth
from .upload_paths import (
    ROOT, UPLOAD_INTERNAL, BACKUP_INTERNAL,
    safe_path, internal_path
)
from .upload_sessions import upload_lock, upload_sessions
from .upload_utils import check_disk_space, CATEGORIES, verify_md5

upload = Blueprint("upload", __name__, url_prefix="/upload")