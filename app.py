from flask import Flask, request, jsonify
import psycopg2
from google.cloud import storage
from flask_cors import CORS
import os

app = Flask(__name__)

CORS(app)

# Fetch environment variables
db_user = os.getenv('DB_USER', 'DB_USER')
db_pass = os.getenv('DB_PASS', 'DB_PASS')
db_name = os.getenv('DB_NAME', 'DB_NAME')
db_host = os.getenv('DB_HOST', 'DB_HOST')  # Localhost if using Cloud SQL Proxy

BUCKET_NAME = "c0904675-bucket"

# Database connection setup (change according to your GCP PostgreSQL details)
def connect_db():
    conn = psycopg2.connect(
        user=db_user,
        password=db_pass,
        host=db_host,
        database=db_name,
        port=5432  # Default PostgreSQL port
    )
    return conn

# GCP Bucket setup (change according to your bucket)
def upload_to_gcp(file):
    client = storage.Client()
    bucket = client.get_bucket(BUCKET_NAME)
    blob = bucket.blob(file.filename)
    blob.upload_from_file(file)
    return f'File {file.filename} uploaded to GCP Bucket'

# Endpoint to insert data into PostgreSQL
@app.route('/insert', methods=['POST'])
def insert_data():
    data = request.json
    name = data.get('name')
    email = data.get('email')

    conn = connect_db()
    cursor = conn.cursor()

    cursor.execute("CREATE TABLE IF NOT EXISTS users (id SERIAL PRIMARY KEY, name VARCHAR(100), email VARCHAR(100))")
    conn.commit()

    cursor.execute("INSERT INTO users (name, email) VALUES (%s, %s)", (name, email))
    conn.commit()
    cursor.close()
    conn.close()

    return jsonify({"message": "Data inserted successfully"}), 201

# Endpoint to fetch data from PostgreSQL
@app.route('/get', methods=['GET'])
def get_data():
    conn = connect_db()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM users")
    users = cursor.fetchall()
    cursor.close()
    conn.close()

    return jsonify(users)

# Endpoint to delete user from PostgreSQL
@app.route('/delete/<int:user_id>', methods=['DELETE'])
def delete_user(user_id):
    conn = connect_db()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM users WHERE id = %s", (user_id,))
    conn.commit()
    cursor.close()
    conn.close()
    return jsonify({"message": "User deleted successfully"}), 200

# Endpoint to upload file to GCP bucket
@app.route('/upload', methods=['POST'])
def upload_file():
    file = request.files['file']
    if not file:
        return jsonify({"message": "No file provided!"}), 400
    
    file = request.files['file']
    if file.filename == '':
        return jsonify({"message": "No selected file"}), 400

    message = upload_to_gcp(file)
    return jsonify({"message": message})
@app.route('/')
def index():
    return '''
    <h1>Select a File Please</h1>
    <form method="POST" action="/upload" enctype="multipart/form-data">
      <input type="file" name="file">
      <input type="submit">
    </form>
    '''
if __name__ == '__main__':
       app.run(host='0.0.0.0', port=5000, debug=True)
