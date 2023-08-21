from flask import Flask, render_template, request
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from flask import Flask, request, abort

from config import USER_ADMIN_PATH , TRUSTED_IPS, LOG_PATH


app = Flask(__name__)
limiter = Limiter(key_func=get_remote_address, default_limits=["5 per second"])
limiter.init_app(app=app)

@app.before_request
def before_request_func():
    if request.remote_addr not in TRUSTED_IPS:
        abort(404) # Not Found
            
            
@app.route('/', methods=['GET'])
def create_case():
    return render_template('maintenance.html')

if __name__ == '__main__':
    app.run(debug=True, port=1000)
    # app.run(host="0.0.0.0", port=1000)
