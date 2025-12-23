import os
from flask import Flask
from flask_session import Session
from datetime import timedelta
from db import close_db
from routes.auth import auth_bp
from routes.customer import customer_bp
from routes.manager import manager_bp

app = Flask(__name__)
app.secret_key = 'your_secret_key_here'  # Change this for production

# Auto-create session directory to avoid errors on PA
session_dir = os.path.join(app.root_path, 'flask_session_data')
if not os.path.exists(session_dir):
    os.makedirs(session_dir)

# Configure Session
app.config.update(
    SESSION_TYPE='filesystem',
    SESSION_FILE_DIR=session_dir,
    SESSION_PERMANENT=True,
    PERMANENT_SESSION_LIFETIME=timedelta(minutes=30),
    SESSION_REFRESH_EACH_REQUEST=True,
    SESSION_COOKIE_SECURE=False
)
Session(app)

# Register the teardown context to close DB connection
app.teardown_appcontext(close_db)

# Register Blueprints
app.register_blueprint(auth_bp)
app.register_blueprint(customer_bp)
app.register_blueprint(manager_bp)

if __name__ == '__main__':
    app.run(debug=True)
