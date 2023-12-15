from flask import Blueprint

api = Blueprint('api', __name__)

@api.route('/upload')
def upload():
    return '{"status": "success"}'

@api.route('/refresh')
def refresh():
    return '{"status": "success"}'