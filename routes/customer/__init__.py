from flask import Blueprint

customer_bp = Blueprint('customer', __name__)

# Import routes to register them with the blueprint
from routes.customer import flight_search, orders, booking

