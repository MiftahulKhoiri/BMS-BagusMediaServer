from flask import Blueprint, render_template, session, request, redirect
from app.routes.BMS_auth import (
    BMS_auth_is_root,
    BMS_auth_is_admin,
    BMS_auth_is_login
)

admin = Blueprint("admin", __name__, url_prefix="/admin")


# ===============================
#  Proteksi Halaman Admin
# ===============================

def BMS_admin_required():
    """Root dan Admin boleh masuk"""
    if not BMS_auth_is_login():
        return redirect("/auth/login")

    if not (BMS_auth_is_root() or BMS_auth_is_admin()):
        return "Akses ditolak! Khusus ROOT atau ADMIN!"
    return None


# ===============================
#  DASHBOARD ADMIN
# ===============================

@admin.route("/dashboard")
def BMS_admin_dashboard():
    check = BMS_admin_required()
    if check:
        return check

    return render_template("BMSadmin_dashboard.html")


# ===============================
#  LOADER HALAMAN AJAX
# ===============================

@admin.route("/page")
def BMS_admin_load_page():

    check = BMS_admin_required()
    if check:
        return check

    page = request.args.get("name")

    # HALAMAN HOME
    if page == "home":
        return """
        <h2>🏠 Admin Home</h2>
        <p>Selamat datang di BMS Admin Panel.</p>
        """

    # HALAMAN TOOLS
    if page == "tools":
        return """
        <h2>🛠 Tools</h2>
        <button onclick="fetch('/tools/update').then(r=>r.text()).then(alert)">Update Server</button>
        <br><br>
        <button onclick="fetch('/tools/restart').then(r=>r.text()).then(alert)">Restart Server</button>
        <br><br>
        <button onclick="fetch('/tools/shutdown').then(r=>r.text()).then(alert)">Shutdown Server</button>
        """

    # HALAMAN FILE MANAGER
    if page == "filemanager":
        return "<h2>📁 File Manager</h2><p>UI File Manager akan muncul di sini.</p>"

    # HALAMAN MP3
    if page == "mp3":
        return "<h2>🎵 MP3 Player</h2><iframe src='/mp3/player' width='100%' height='400px'></iframe>"

    # HALAMAN VIDEO
    if page == "video":
        return "<h2>🎬 Video Player</h2><iframe src='/video/player' width='100%' height='400px'></iframe>"

    # HALAMAN USER MANAGER
    if page == "users":
        return "<h2>👤 User Manager</h2><p>Manajemen user akan dibuat di sini.</p>"

    # HALAMAN UPDATE PANEL (BENAR DI SINI)
    if page == "update":
        return """
        <h2>🔄 Update Panel</h2>

        <h3>Git Update</h3>
        <button onclick="runUpdate()">Update (git pull)</button>

        <h3>Install Package</h3>
        <input id='pkg' placeholder='Nama package' />
        <button onclick="installPkg()">Install</button>

        <h3>Server Control</h3>
        <button onclick="runRestart()">Restart Server</button>
        <button onclick="runShutdown()">Shutdown Server</button>

        <h3>Logs</h3>
        <button onclick="loadLog()">Load Log</button>
        <button onclick="clearLog()">Clear Log</button>

        <pre id='logbox' style='background:#000;color:#0f0;padding:10px;height:300px;overflow:auto;'></pre>

        <script>

        function runUpdate(){
            fetch('/tools/update')
            .then(r=>r.text())
            .then(t=>{
                alert('Update selesai!');
                loadLog();
            });
        }

        function installPkg(){
            const pkg = document.getElementById('pkg').value;
            const form = new FormData();
            form.append('package', pkg);

            fetch('/tools/install', {method:'POST', body:form})
            .then(r=>r.text())
            .then(t=>{
                alert('Install: ' + t);
                loadLog();
            });
        }

        function runRestart(){
            fetch('/tools/restart')
            .then(r=>r.text())
            .then(t=>{
                alert('Server restart (simulasi)!');
            });
        }

        function runShutdown(){
            fetch('/tools/shutdown')
            .then(r=>r.text())
            .then(t=>{
                alert('Server shutdown!');
            });
        }

        function loadLog(){
            fetch('/tools/log')
            .then(r=>r.text())
            .then(t=>{
                document.getElementById('logbox').textContent = t;
            });
        }

        function clearLog(){
            fetch('/tools/log/clear')
            .then(r=>r.text())
            .then(t=>{
                loadLog();
            });
        }

        </script>
        """

    # DEFAULT JIKA TIDAK DITEMUKAN
    return "<p>Halaman tidak ditemukan.</p>"