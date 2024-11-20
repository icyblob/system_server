from flask import Flask, request, jsonify
import os
import hashlib

UPLOAD_DIR = "/app/bet_external_asset"
os.makedirs(UPLOAD_DIR, exist_ok=True)

app = Flask(__name__)

def calculate_md5(file_path):
    hash_md5 = hashlib.md5()
    with open(file_path, "rb") as f:
        for chunk in iter(lambda: f.read(4096), b""):
            hash_md5.update(chunk)
    return hash_md5.hexdigest()

@app.route('/sync_file', methods=['POST'])
def upload_file():
    file = request.files.get('file')
    if not file:
        return jsonify({"error": "No file provided"}), 400

    file_path = os.path.join(UPLOAD_DIR, file.filename)
    file.save(file_path)
    return jsonify({"message": f"File {file.filename} uploaded successfully."}), 200

@app.route('/sync_file/list', methods=['GET'])
def list_files():
    files = {f: calculate_md5(os.path.join(UPLOAD_DIR, f)) for f in os.listdir(UPLOAD_DIR) if os.path.isfile(os.path.join(UPLOAD_DIR, f))}
    return jsonify(files)

if __name__ == '__main__':
    app.run(host="0.0.0.0", port=80)

