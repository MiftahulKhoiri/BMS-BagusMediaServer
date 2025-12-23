from flask import Flask
from app.routes import register_blueprints

app = Flask(__name__)

# 🔥 WAJIB DIPANGGIL
register_blueprints(app)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)