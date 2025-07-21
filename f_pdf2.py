from flask import Flask, send_file, jsonify
from flask_socketio import SocketIO
from flask_sqlalchemy import SQLAlchemy
from PyQt5.QtWidgets import QApplication
import sys
import os
# ... (other imports from your original app.py)
from pdf_exporter import PDFExporter  # Import the modified PDFExporter

app = Flask(__name__)
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'your-secret-key')
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///comments.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
socketio = SocketIO(app)
db = SQLAlchemy(app)

# Initialize QApplication once at startup
qt_app = QApplication(sys.argv)

# ... (your existing Comment model, data generation functions, and routes)

@app.route('/api/export_pdf', methods=['GET'])
def export_pdf():
    try:
        # Define URLs to export (same as in your original pdf_exporter.py)
        urls = [
            ("http://127.0.0.1:5000/", "Home Dashboard"),
            ("http://127.0.0.1:5000/productivity", "Productivity Dashboard"),
            ("http://127.0.0.1:5000/fte", "FTE Dashboard"),
            ("http://127.0.0.1:5000/sankey", "Sankey Dashboard")
        ]
        output_file = "InsightDash_Dashboard.pdf"
        
        # Initialize PDFExporter with the shared QApplication instance
        exporter = PDFExporter(urls, output_file, qt_app)
        exporter.start()
        
        # Wait for the PDF to be generated (blocking, but can be made async if needed)
        while not os.path.exists(output_file):
            import time
            time.sleep(1)
        
        # Serve the PDF file
        return send_file(output_file, as_attachment=True, download_name="InsightDash_Dashboard.pdf")
    except Exception as e:
        return jsonify({"error": f"Failed to generate PDF: {str(e)}"}), 500

# ... (rest of your existing app.py code)

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    socketio.run(app, debug=True, host='0.0.0.0', port=5000)
