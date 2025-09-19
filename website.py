import os
from functools import wraps
from flask import Flask, request, redirect, url_for, render_template_string, session, send_from_directory, flash

# --- Configuration ---
UPLOAD_FOLDER = 'uploads'
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}
PASSWORD = 'secret'  # Change this to your desired password
SECRET_KEY = 'change_this_secret_key'

# --- App Setup ---
app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.secret_key = SECRET_KEY

if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

# --- Helper Functions ---
def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def login_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if not session.get('logged_in'):
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated

# --- Templates ---
LOGIN_TEMPLATE = '''
<!doctype html>
<html lang="en">
<head>
    <title>Login</title>
    <style>
        body { background: #181818; color: #eee; display: flex; height: 100vh; align-items: center; justify-content: center; }
        form { background: #222; padding: 2em; border-radius: 8px; box-shadow: 0 2px 8px #0008; }
        input[type=password], input[type=submit] { width: 100%; padding: 0.7em; margin-top: 1em; border: none; border-radius: 4px; }
        input[type=submit] { background: #444; color: #fff; cursor: pointer; }
    </style>
</head>
<body>
    <form method="post">
        <h2>Login</h2>
        {% with messages = get_flashed_messages() %}
          {% if messages %}
            <div style="color: #f66;">{{ messages[0] }}</div>
          {% endif %}
        {% endwith %}
        <input type="password" name="password" placeholder="Password" autofocus required>
        <input type="submit" value="Login">
    </form>
</body>
</html>
'''

GALLERY_TEMPLATE = '''
<!doctype html>
<html lang="en">
<head>
    <title>Image Gallery</title>
    <style>
        body { background: #181818; color: #eee; font-family: sans-serif; margin: 0; }
        header { padding: 1em 2em; background: #222; display: flex; justify-content: space-between; align-items: center; }
        .upload-form { margin: 2em auto; max-width: 400px; background: #222; padding: 1.5em; border-radius: 8px; }
        .gallery { display: grid; grid-template-columns: repeat(auto-fit, minmax(180px, 1fr)); gap: 1em; padding: 2em; }
        .img-card { background: #222; border-radius: 8px; overflow: hidden; position: relative; }
        .img-card img { width: 100%; display: block; }
        .delete-btn { position: absolute; top: 8px; right: 8px; background: #f44; color: #fff; border: none; border-radius: 4px; padding: 0.3em 0.7em; cursor: pointer; }
        .logout-btn { background: #444; color: #fff; border: none; border-radius: 4px; padding: 0.5em 1em; cursor: pointer; }
        input[type=file] { color: #eee; }
    </style>
</head>
<body>
    <header>
        <h2>Image Gallery</h2>
        <form action="{{ url_for('logout') }}" method="post" style="margin:0;">
            <button class="logout-btn">Logout</button>
        </form>
    </header>
    <div class="upload-form">
        <form method="post" enctype="multipart/form-data" action="{{ url_for('upload') }}">
            <input type="file" name="images" multiple required>
            <input type="submit" value="Upload" style="margin-top:1em; width:100%; background:#444; color:#fff; border:none; border-radius:4px; padding:0.7em; cursor:pointer;">
        </form>
    </div>
    <div class="gallery">
        {% for img in images %}
        <div class="img-card">
            <img src="{{ url_for('uploaded_file', filename=img) }}">
            <form method="post" action="{{ url_for('delete_image', filename=img) }}">
                <button class="delete-btn" onclick="return confirm('Delete this image?')">Delete</button>
            </form>
        </div>
        {% endfor %}
    </div>
</body>
</html>
'''

# --- Routes ---
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        if request.form.get('password') == PASSWORD:
            session['logged_in'] = True
            return redirect(url_for('gallery'))
        else:
            flash('Incorrect password.')
    return render_template_string(LOGIN_TEMPLATE)

@app.route('/logout', methods=['POST'])
@login_required
def logout():
    session.clear()
    return redirect(url_for('login'))

@app.route('/', methods=['GET'])
@login_required
def gallery():
    images = sorted(os.listdir(app.config['UPLOAD_FOLDER']))
    return render_template_string(GALLERY_TEMPLATE, images=images)

@app.route('/upload', methods=['POST'])
@login_required
def upload():
    files = request.files.getlist('images')
    for file in files:
        if file and allowed_file(file.filename):
            filename = file.filename
            save_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            # Avoid overwriting files
            base, ext = os.path.splitext(filename)
            i = 1
            while os.path.exists(save_path):
                filename = f"{base}_{i}{ext}"
                save_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
                i += 1
            file.save(save_path)
    return redirect(url_for('gallery'))

@app.route('/uploads/<filename>')
@login_required
def uploaded_file(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)

@app.route('/delete/<filename>', methods=['POST'])
@login_required
def delete_image(filename):
    path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
    if os.path.exists(path):
        os.remove(path)
    return redirect(url_for('gallery'))

# --- Run App ---
if __name__ == '__main__':
    app.run(debug=True)