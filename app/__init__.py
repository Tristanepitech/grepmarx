# -*- encoding: utf-8 -*-
"""
Copyright (c) 2019 - present AppSeed.us
Copyright (c) 2021 - present Orange Cyberdefense
"""

from importlib import import_module

from celery import Celery
from flask import Flask
from flask_ldap3_login import LDAP3LoginManager
from flask_login import LoginManager
from flask_migrate import Migrate
from flask_sqlalchemy import SQLAlchemy

# log tools

import logging
import sys

# load the extension

db = SQLAlchemy()
login_manager = LoginManager()
ldap_manager = LDAP3LoginManager()

# Instantiate Celery
celery = Celery(
    "grepmarx",
    broker="redis://redis:6379/0",
    backend="redis://redis:6379/0"
)


def register_extensions(app):
    db.init_app(app)
    login_manager.init_app(app)
    ldap_manager.app = app


def register_blueprints(app):
    for module_name in ("base", "administration", "analysis", "rules", "projects"):
        module = import_module("app.{}.routes".format(module_name))
        app.register_blueprint(module.blueprint)


def configure_database(app):
    with app.app_context():
        db.create_all()

    def initialize_database():
        db.create_all()

    @app.teardown_request
    def shutdown_session(exception=None):
        db.session.remove()
        

# def create_app(config):

#     # Init app and config
#     app = Flask(__name__, static_folder="base/static")
#     app.config.from_object(config)
    
#     # Configure Celery
#     celery.config_from_object(config)
#     celery.conf.update(app.config)
#     # Register modules
#     register_extensions(app)
#     register_blueprints(app)

#     # Configure DB
#     configure_database(app)
#     Migrate(app=app, db=db, compare_type=True)

#     return app

def configure_logging(app):
    # Delet default handlers (Gunicorn)
    app.logger.handlers.clear()

    handler = logging.StreamHandler(sys.stdout)
    handler.setLevel(logging.INFO)

    formatter = logging.Formatter(
        "[%(asctime)s] %(levelname)s in %(module)s: %(message)s"
    )
    handler.setFormatter(formatter)

    app.logger.addHandler(handler)
    app.logger.setLevel(logging.INFO)

    # Important pour Gunicorn
    app.logger.propagate = False


def create_app(config):

    # Init app and config
    app = Flask(__name__, static_folder="base/static")
    app.config.from_object(config)

    configure_logging(app)

    # Configure Celery
    celery.config_from_object(config)
    celery.conf.update(app.config)
    # Register modules
    register_extensions(app)
    register_blueprints(app)

    # Configure DB
    configure_database(app)
    Migrate(app=app, db=db, compare_type=True)

    app.logger.info("Grepmarx application started")

    return app


