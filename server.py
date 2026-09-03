import os

from dotenv import load_dotenv
from flask import Flask
from flask_cors import CORS

from app.routes.activity_routes import activity_bp
from app.routes.auth_routes import auth_bp
from app.routes.country_routes import country_bp
from app.routes.currency_routes import currency_bp
from app.routes.journey_routes import journey_bp
from app.routes.major_stage_routes import major_stage_bp
from app.routes.medium_routes import medium_bp
from app.routes.minor_stage_routes import minor_stage_bp
from app.routes.place_routes import place_bp
from app.routes.spending_routes import spending_bp
from app.routes.transportation_routes import transportation_bp
from app.routes.user_routes import user_bp
from db import db

load_dotenv()


def create_app(config=None):
    app = Flask(__name__)

    # Default configuration
    app.config.from_mapping(
        SECRET_KEY=os.getenv("SECRET_KEY"),
        SQLALCHEMY_DATABASE_URI=os.getenv("SQLALCHEMY_DATABASE_URI"),
        SQLALCHEMY_TRACK_MODIFICATIONS=False,
    )

    # Override configuration, e.g. during testing
    if config is not None:
        app.config.update(config)

    # Extensions
    db.init_app(app)

    CORS(
        app,
        resources={
            r"/*": {
                "origins": "*"
            }
        }
    )

    # Blueprints
    app.register_blueprint(
        journey_bp,
        url_prefix="/journey"
    )

    app.register_blueprint(
        major_stage_bp,
        url_prefix="/major_stage"
    )

    app.register_blueprint(
        minor_stage_bp,
        url_prefix="/minor_stage"
    )

    app.register_blueprint(
        auth_bp,
        url_prefix="/auth"
    )

    app.register_blueprint(
        country_bp,
        url_prefix="/country"
    )

    app.register_blueprint(
        place_bp,
        url_prefix="/place-to-visit"
    )

    app.register_blueprint(
        transportation_bp,
        url_prefix="/transportation"
    )

    app.register_blueprint(
        activity_bp,
        url_prefix="/activity"
    )

    app.register_blueprint(
        spending_bp,
        url_prefix="/spending"
    )

    app.register_blueprint(
        user_bp,
        url_prefix="/user"
    )

    app.register_blueprint(
        medium_bp,
        url_prefix="/medium"
    )

    app.register_blueprint(
        currency_bp,
        url_prefix="/currency"
    )

    return app


if __name__ == "__main__":
    app = create_app()

    # For local development:
    # create tables if they do not exist yet
    with app.app_context():
        db.create_all()

    host = os.getenv("HOST", "127.0.0.1")
    port = int(os.getenv("PORT", "5001"))
    debug = os.getenv(
        "FLASK_DEBUG",
        "false"
    ).lower() == "true"

    app.run(
        host=host,
        port=port,
        debug=debug,
    )