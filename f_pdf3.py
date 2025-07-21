from flask import Flask, send_file, jsonify
from pdf_exporter import PDFExporter
import threading
import os

app = Flask(__name__)
output_path = "static/InsightDash_Dashboard.pdf"

@app.route("/generate_pdf", methods=["GET"])
def generate_pdf():
    urls = [
        ("http://127.0.0.1:5000/", "Home Dashboard"),
        ("http://127.0.0.1:5000/productivity", "Productivity Dashboard")
    ]

    def run_export():
        exporter = PDFExporter(urls, output_path)
        exporter.start()

    thread = threading.Thread(target=run_export)
    thread.start()

    return jsonify({"message": "PDF generation started", "download": "/download_pdf"})

@app.route("/download_pdf", methods=["GET"])
def download_pdf():
    if os.path.exists(output_path):
        return send_file(output_path, as_attachment=True)
    else:
        return jsonify({"error": "PDF not ready"}), 404

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
