from app.routes.BMS_downlod.progress_store import update_task

def yt_progress_hook(task_id=None):
    def hook(d):
        if not task_id:
            return

        if d["status"] == "downloading":
            percent = d.get("_percent_str", "").strip()
            update_task(task_id, status="downloading", progress=percent)
        elif d["status"] == "finished":
            update_task(task_id, status="finished", progress="100%")
    return hook