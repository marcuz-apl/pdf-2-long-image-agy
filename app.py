import os
import uuid
import shutil
import zipfile
import time
import threading
import re
from flask import Flask, request, jsonify, render_template, abort, send_from_directory
from werkzeug.utils import secure_filename
from pdf2image import convert_from_path
from PIL import Image

def pdf_to_long_image(pdf_path, output_path, output_format, dpi=200):
    """Converts a PDF file to a single long image of format output_format (TIFF/PNG/JPEG)."""
    poppler_path = None
    if os.name == 'nt':
        # Check environment variable first
        env_path = os.environ.get('POPPLER_PATH')
        if env_path:
            poppler_path = env_path
        else:
            # Check local project folder
            local_poppler = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'poppler', 'bin')
            if os.path.isdir(local_poppler):
                poppler_path = local_poppler

    pages = convert_from_path(pdf_path, dpi=dpi, poppler_path=poppler_path)
    if not pages:
        return False
        
    total_width = max(page.width for page in pages)
    total_height = sum(page.height for page in pages)
    
    # Create canvas with white background
    long_image = Image.new('RGB', (total_width, total_height), (255, 255, 255))
    
    current_y = 0
    for page in pages:
        long_image.paste(page, (0, current_y))
        current_y += page.height
        
    output_format_upper = output_format.upper()
    if output_format_upper == 'TIFF':
        long_image.save(output_path, format='TIFF', compression='tiff_lzw')
    elif output_format_upper == 'PNG':
        long_image.save(output_path, format='PNG')
    elif output_format_upper == 'JPEG' or output_format_upper == 'JPG':
        long_image.save(output_path, format='JPEG', quality=90)
    else:
        raise ValueError(f"Unsupported format: {output_format}")
        
    return True


import logging

class NoDevServerWarningFilter(logging.Filter):
    def filter(self, record):
        return "This is a development server" not in record.getMessage()

logging.getLogger('werkzeug').addFilter(NoDevServerWarningFilter())

import flask.cli
flask.cli.show_server_banner = lambda *x: None

app = Flask(__name__)
# Enforce 50MB maximum payload size at the WSGI/Flask server level
app.config['MAX_CONTENT_LENGTH'] = 50 * 1024 * 1024

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
TEMP_DIR = os.path.join(BASE_DIR, "temp_jobs")
os.makedirs(TEMP_DIR, exist_ok=True)

def cleanup_old_jobs():
    """Periodically clean up jobs older than 15 minutes (900 seconds) in a background thread."""
    while True:
        try:
            now = time.time()
            if os.path.exists(TEMP_DIR):
                for job_id in os.listdir(TEMP_DIR):
                    job_path = os.path.join(TEMP_DIR, job_id)
                    if os.path.isdir(job_path):
                        mtime = os.path.getmtime(job_path)
                        if now - mtime > 900:  # 15 minutes
                            shutil.rmtree(job_path)
                            print(f"Cleaned up expired job directory: {job_id}")
        except Exception as e:
            print(f"Error in cleanup thread: {e}")
        time.sleep(60)

# Start background cleanup thread as daemon
threading.Thread(target=cleanup_old_jobs, daemon=True).start()

def is_safe_job_id(job_id):
    """Verifies that job_id is a valid UUID to prevent path traversal."""
    return bool(re.match(r'^[a-fA-F0-9\-]{36}$', job_id))

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/favicon.ico')
def favicon():
    return send_from_directory(os.path.join(app.root_path, 'static'),
                               'favicon.ico', mimetype='image/vnd.microsoft.icon')


@app.route('/upload', methods=['POST'])
def upload_files():
    if 'files' not in request.files:
        return jsonify({'error': 'No files uploaded'}), 400
        
    files = request.files.getlist('files')
    if not files or files[0].filename == '':
        return jsonify({'error': 'No selected files'}), 400
        
    output_format = request.form.get('format', 'tiff').lower()
    if output_format not in ['tiff', 'png', 'jpeg']:
        return jsonify({'error': 'Invalid format selected'}), 400
        
    try:
        dpi = int(request.form.get('dpi', 200))
    except ValueError:
        return jsonify({'error': 'Invalid DPI value'}), 400
        
    # Verify total file size using stream seek/tell (avoids reading full content into memory)
    total_size = 0
    for f in files:
        f.seek(0, os.SEEK_END)
        total_size += f.tell()
        f.seek(0)
        
    if total_size > 50 * 1024 * 1024:
        return jsonify({'error': 'Total upload size exceeds 50MB limit'}), 400
        
    job_id = str(uuid.uuid4())
    job_dir = os.path.join(TEMP_DIR, job_id)
    inputs_dir = os.path.join(job_dir, "inputs")
    outputs_dir = os.path.join(job_dir, "outputs")
    
    os.makedirs(inputs_dir, exist_ok=True)
    os.makedirs(outputs_dir, exist_ok=True)
    
    results = []
    success_count = 0
    
    ext_map = {'tiff': 'tiff', 'png': 'png', 'jpeg': 'jpg'}
    file_ext = ext_map.get(output_format, 'tiff')
    
    for f in files:
        if not f.filename.lower().endswith('.pdf'):
            results.append({
                'original': f.filename,
                'status': 'error',
                'error_message': 'File is not a PDF.'
            })
            continue
            
        pdf_path = os.path.join(inputs_dir, f.filename)
        f.save(pdf_path)
        
        base_name = os.path.splitext(f.filename)[0]
        output_filename = f"{base_name}_long_image.{file_ext}"
        output_path = os.path.join(outputs_dir, output_filename)
        
        try:
            if pdf_to_long_image(pdf_path, output_path, output_format, dpi):
                results.append({
                    'original': f.filename,
                    'converted': output_filename,
                    'status': 'success',
                    'url': f"/download/{job_id}/{output_filename}"
                })
                success_count += 1
            else:
                results.append({
                    'original': f.filename,
                    'status': 'error',
                    'error_message': 'Could not extract pages from PDF.'
                })
        except Exception as e:
            results.append({
                'original': f.filename,
                'status': 'error',
                'error_message': str(e)
            })
            
    zip_url = None
    if success_count > 0:
        zip_filename = f"converted_images_{job_id[:8]}.zip"
        zip_path = os.path.join(job_dir, zip_filename)
        with zipfile.ZipFile(zip_path, 'w') as zipf:
            for res in results:
                if res['status'] == 'success':
                    img_path = os.path.join(outputs_dir, res['converted'])
                    zipf.write(img_path, res['converted'])
        zip_url = f"/download-zip/{job_id}"
        
    return jsonify({
        'job_id': job_id,
        'results': results,
        'zip_url': zip_url,
        'success_count': success_count,
        'total_count': len(files)
    })

@app.route('/download/<job_id>/<filename>')
def download_file(job_id, filename):
    if not is_safe_job_id(job_id):
        abort(400)
        
    secured_name = secure_filename(filename)
    if not secured_name or secured_name != filename:
        abort(400)
        
    outputs_dir = os.path.join(TEMP_DIR, job_id, "outputs")
    return send_from_directory(outputs_dir, filename, as_attachment=True)

@app.route('/download-zip/<job_id>')
def download_zip(job_id):
    if not is_safe_job_id(job_id):
        abort(400)
        
    job_dir = os.path.join(TEMP_DIR, job_id)
    if not os.path.exists(job_dir):
        abort(404)
        
    zip_files = [f for f in os.listdir(job_dir) if f.endswith('.zip')]
    if not zip_files:
        abort(404)
        
    zip_filename = zip_files[0]
    return send_from_directory(job_dir, zip_filename, as_attachment=True)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=False)
