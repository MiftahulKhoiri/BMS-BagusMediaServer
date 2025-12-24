def yt_progress_hook(d):
    if d["status"] == "downloading":
        percent = d.get("_percent_str", "").strip()
        speed = d.get("_speed_str", "").strip()
        print(f"\r⬇️ {percent} | {speed}", end="")
    elif d["status"] == "finished":
        print("\n✅ Download selesai")