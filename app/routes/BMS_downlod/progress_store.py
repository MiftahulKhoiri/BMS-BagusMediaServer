import uuid

PROGRESS_STORE = {}

def buat_task():
    task_id = str(uuid.uuid4())
    PROGRESS_STORE[task_id] = {
        "status": "init",
        "progress": "0%"
    }
    return task_id

def update_task(task_id, status=None, progress=None):
    if task_id in PROGRESS_STORE:
        if status:
            PROGRESS_STORE[task_id]["status"] = status
        if progress:
            PROGRESS_STORE[task_id]["progress"] = progress

def get_task(task_id):
    return PROGRESS_STORE.get(task_id)