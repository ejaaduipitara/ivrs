from flask import Blueprint

import requests

api = Blueprint('api', __name__)

@api.route('/getTodayActivity')
def getTodayActivity():
    r = requests.get('https://api.companieshouse.gov.uk/company/**COMPANY NUMBER**/filing-history')

    return '{"status": "success"}'
