from flask import Blueprint

api = Blueprint('api', __name__)

@api.route('/upload')
def upload():
    return 'upload'

@api.route('/refresh')
def refresh():
    return 'refresh'