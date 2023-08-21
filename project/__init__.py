import os
import json
import sqlite3
import datetime

# import logging
# from logging.handlers import TimedRotatingFileHandler

from flask import Flask, request, abort
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager 

from flask_limiter import Limiter
from flask_limiter.util import get_remote_address

from .models import User, get_user_info
from .config import USER_ADMIN_PATH , TRUSTED_IPS, LOG_PATH

# db = SQLAlchemy()

def create_app():
    app = Flask(__name__)

    limiter = Limiter(key_func=get_remote_address, default_limits=["5 per second"])
    limiter.init_app(app=app)
    
    app.config['SECRET_KEY'] = '9OLWxND4o83j4K4iuopO'
    app.config['SQLALCHEMY_DATABASE_URI'] = USER_ADMIN_PATH
    app.config['MAX_CONTENT_LENGTH'] = 10 * 1024 * 1024

    login_manager = LoginManager()
    login_manager.login_view = 'auth.login'
    login_manager.init_app(app)

    @login_manager.user_loader
    def load_user(user_id):
        return get_user_info(user_id)

    @app.before_request
    def before_request_func():
        if request.remote_addr not in TRUSTED_IPS:
            abort(404) # Not Found

    @app.after_request
    def after_request(response):
        log_conn = sqlite3.connect(LOG_PATH)
        
        path = request.path
        if not path.endswith((".css", ".js", ".png", ".jpg")) and not path.startswith("/static"):
            
            form_data = request.form.to_dict()
            if "csrf_token" in form_data:
                del form_data["csrf_token"]
            form_data_to_db = json.dumps(form_data)
            
            cursor = log_conn.cursor()
            cursor.execute(
                "INSERT INTO Log_Info (Request_Date, Request_IP, Request_Method, Request_Path, Request_Status, Request_Form) VALUES (?, ?, ?, ?, ?, ?)",
                (datetime.datetime.now(), request.remote_addr, request.method, request.full_path, response.status, form_data_to_db),
            )
            log_conn.commit()
        return response

    # blueprint for auth routes in our app
    from .auth import auth as auth_blueprint
    app.register_blueprint(auth_blueprint)

    # blueprint for non-auth parts of app
    from .main import main as main_blueprint
    app.register_blueprint(main_blueprint)
    
    from .create import create as create_blueprint
    app.register_blueprint(create_blueprint)
    
    from .create_cic import cic_creating as create_cic_blueprint
    app.register_blueprint(create_cic_blueprint)
    
    from .preview import preview as preview_blueprint
    app.register_blueprint(preview_blueprint)
    
    from .working import working as working_blueprint
    app.register_blueprint(working_blueprint)
    
    from .recom_referral import recom_referral
    app.register_blueprint(recom_referral)

    from .admin_manage import realboss
    app.register_blueprint(realboss)

    from .edd_track import tracking_edd
    app.register_blueprint(tracking_edd)

    return app
