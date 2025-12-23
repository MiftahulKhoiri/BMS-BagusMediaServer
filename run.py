#!/usr/bin/env python3
"""
RUN SCRIPT untuk BAGUS MEDIA SERVER (BMS)
Script utama untuk menjalankan server Flask BMS
"""

import sys
import os

# Tambahkan path project ke sys.path
project_root = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, project_root)

# Import dan jalankan aplikasi
from app import create_app

if __name__ == "__main__":
    print("""
╔══════════════════════════════════════════════════════╗
║     BAGUS MEDIA SERVER (BMS) - STARTING SERVER      ║
╚══════════════════════════════════════════════════════╝
    """)
    
    app = create_app()
    
    # Konfigurasi host dan port
    host = "0.0.0.0"
    port = 5000
    
    print(f"🌐 Server akan berjalan di: http://{host}:{port}")
    print(f"📁 Project Root: {app.config['PROJECT_ROOT']}")
    print("🔧 Debug Mode: ON")
    print("\nTekan Ctrl+C untuk menghentikan server\n")
    
    try:
        app.run(
            host=host,
            port=port,
            debug=True,
            threaded=True  # Mendukung multiple connections
        )
    except KeyboardInterrupt:
        print("\n\n👋 Server dihentikan oleh pengguna")
        sys.exit(0)
    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        sys.exit(1)