from flask import Flask, redirect, jsonify
from flask_jwt_extended import JWTManager
from flasgger import Swagger, swag_from
import os

from .auth import auth
from .bookmarks import bookmarks
from .database import db, User, Bookmark
from .config.swagger import template, swagger_config

def create_app(test_config=None):
    app = Flask(__name__, instance_relative_config=True)

    if test_config is None:
        app.config.from_mapping(
            SECRET_KEY = os.environ.get("SECRET_KEY"),
            SQLALCHEMY_DATABASE_URI=os.environ.get('SQLALCHEMY_DB_URI'),
            JWT_SECRET_KEY=os.environ.get('JWT_SECRET_KEY'),
            SWAGGER = {
                'title': 'Bookmarks API',
                'uiversion': 3
            }
        )
    else:
        app.config.from_mapping(test_config)
    
    db.app = app
    db.init_app(app)

    JWTManager(app)

    app.register_blueprint(auth)
    app.register_blueprint(bookmarks)

    Swagger(app, config=swagger_config, template=template)

    @app.get('/<short_url>')
    @swag_from('./docs/short_url.yml')
    def redirect_to_url(short_url):
        bookmark = Bookmark.query.filter_by(short_url = short_url).first_or_404()

        if bookmark:
            bookmark.visits += 1
            db.session.commit()
            return redirect(bookmark.url)
    
    @app.errorhandler(404)
    def handle_404(e):
        return jsonify({"error": "Not found"}), 404

    @app.errorhandler(500)
    def handle_500(e):
        return jsonify({"error": "Something went wrong, we are working on it"}), 500
    
    return app