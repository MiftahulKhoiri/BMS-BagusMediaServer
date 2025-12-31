import shutil

def check_disk_space(required_size: int) -> bool:
    total, used, free = shutil.disk_usage("/")
    return free > required_size