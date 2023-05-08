from flask import Flask, app
from flask_login import LoginManager, login_manager
import pymongo
import os
from .auth import User, collection
from bson.objectid import ObjectId
from pymongo import MongoClient
from flask_cors import CORS, cross_origin


def create_app():
    app = Flask(__name__)
    CORS(app, support_credentials=True)
    app.config['SECRET_KEY'] = 'jvhioef paefjmfvoqv'
    from .views import views
    from .auth import auth
    app.register_blueprint(views, url_prefix='/')
    app.register_blueprint(auth, url_prefix='/')
    login_manager = LoginManager()
    login_manager.login_view = "auth.login"
    login_manager.init_app(app)
    @login_manager.user_loader
    def user_loader(id):
        userloaded = collection.find_one({"_id":int(id)})
        loaduser = User(email=userloaded["Email"], name=userloaded["Name"], password=userloaded["Password"], sign_up=False)
        return loaduser
    return app