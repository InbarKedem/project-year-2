from flask import Flask
from db import close_db
from routes.auth import auth_bp
from routes.customer import customer_bp
from routes.manager import manager_bp

app = Flask(__name__)
app.secret_key = 'your_secret_key_here'  # Change this for production

# Register the teardown context to close DB connection
app.teardown_appcontext(close_db)

# Register Blueprints
app.register_blueprint(auth_bp)
app.register_blueprint(customer_bp)
app.register_blueprint(manager_bp)

if __name__ == '__main__':
    app.run(debug=True)
