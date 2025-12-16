from threading import Lock

upload_lock = Lock()
upload_sessions = {}   # { session_id : {...} }