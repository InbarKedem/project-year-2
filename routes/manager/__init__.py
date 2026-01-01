from flask import Blueprint

manager_bp = Blueprint('manager', __name__)

# Import routes to register them with the blueprint
from routes.manager import dashboard, flights, staff

