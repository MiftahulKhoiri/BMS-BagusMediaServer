# core/nginx_tools.py
import os
from core.system_tools import run

def generate_nginx_config(project_dir: str):
    STATIC_DIR = os.path.join(project_dir, "app", "static")
    nginx_path = "/etc/nginx/sites-available/BMS.conf"
    nginx_enabled = "/etc/nginx/sites-enabled/BMS.conf"

    config = f"""
server {{
    listen 80;
    server_name _;

    access_log /var/log/nginx/bms_access.log;
    error_log  /var/log/nginx/bms_error.log;

    location / {{
        proxy_pass http://127.0.0.1:5000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }}

    location /static {{
        alias {STATIC_DIR};
        try_files $uri =404;
        expires 30d;
    }}
}}
"""
    print("[+] Menulis file konfigurasi NGINX sementara...")
    tmp = "BMS_nginx_temp.conf"
    with open(tmp, "w") as f:
        f.write(config)

    print("[+] Memindahkan konfigurasi NGINX ke /etc/nginx ...")
    run(f"sudo cp {tmp} {nginx_path}")
    run(f"sudo ln -sf {nginx_path} {nginx_enabled}")
    os.remove(tmp)
    print("[✓] Konfigurasi NGINX dibuat.")


def reload_nginx():
    print("[+] Menguji konfigurasi NGINX...")
    run("sudo nginx -t")
    print("[+] Merestart NGINX...")
    run("sudo systemctl restart nginx")
    print("[✓] Nginx direload.")