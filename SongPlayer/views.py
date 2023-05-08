from flask import Blueprint, render_template, request, flash, redirect, url_for
from werkzeug.wrappers import request
from flask_login import current_user

views = Blueprint('views', __name__)
@views.route('/')
def home():
    return render_template('home.html', user=current_user)