import os
from dotenv import load_dotenv
from flask import Flask
from flask_cors import CORS

from db import db


# from app.journey_validation import JourneyValidation
from app.models import *
from app.routes.journey_routes  import journey_bp
from app.routes.major_stage_routes import major_stage_bp
from app.routes.minor_stage_routes import minor_stage_bp
from app.routes.auth_routes import auth_bp
from app.routes.country_routes import country_bp
from app.routes.place_routes import place_bp
from app.routes.transportation_routes import transportation_bp
from app.routes.activity_routes import activity_bp
from app.routes.spending_routes import spending_bp
from app.routes.user_routes import user_bp
from app.routes.medium_routes import medium_bp

# Load environment variables from .env file
load_dotenv()

app = Flask(__name__)
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY')
app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('SQLALCHEMY_DATABASE_URI')
CORS(app, resources={r'/*': {'origins': '*'}})

db.init_app(app)

# Register Blueprints
app.register_blueprint(journey_bp, url_prefix='/journey')
app.register_blueprint(major_stage_bp, url_prefix='/major_stage')
app.register_blueprint(minor_stage_bp, url_prefix='/minor_stage')
app.register_blueprint(auth_bp, url_prefix='/auth')
app.register_blueprint(country_bp, url_prefix='/country')
app.register_blueprint(place_bp, url_prefix='/place-to-visit')
app.register_blueprint(transportation_bp, url_prefix='/transportation')
app.register_blueprint(activity_bp, url_prefix='/activity')
app.register_blueprint(spending_bp, url_prefix='/spending')
app.register_blueprint(user_bp, url_prefix='/user')
app.register_blueprint(medium_bp, url_prefix='/medium')


with app.app_context():
    db.create_all()     # Create the database if not exists
    

HOST = os.getenv('HOST')

if __name__ == '__main__':
    app.run(host=HOST, debug=True, port=5001)