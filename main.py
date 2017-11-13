import json

from bson import json_util
from flask import Flask, request, Response, session, jsonify
from flask_bcrypt import Bcrypt
from flask_pymongo import PyMongo
from pymongo.errors import DuplicateKeyError
from werkzeug.exceptions import BadRequest, NotFound, UnsupportedMediaType, Unauthorized

from exceptions import JSONExceptionHandler

# This defines a Flask application
app = Flask(__name__)

# This code here converts Flask's default (HTML) errors to Json errors.
# This is helpful because HTML breaks clients that are expecting JSON
JSONExceptionHandler(app)

# We configure the app object
app.config['MONGO_DBNAME'] = 'moving_database'
app.secret_key = 'A0Zr98j/3yX R~XHH!!!jmN]LWX/,?RT'

# This initializes PyMongo and makes `mongo` available
mongo = PyMongo(app)
bcrypt = Bcrypt(app)

@app.route('/logout')
def logout():
    """
    This 'logs out' the user by clearing the session data
    """
    session.clear()
    return Response(status=200)


@app.route('/user', methods=['GET'])
def who_am_i():
    """
    Simple method just to show how you can access session data
    :return:
    """
    if session.get('user') is None:
        raise Unauthorized()
    return jsonify(session.get('user'))


@app.route('/user', methods=['PUT'])
def login():
    """
    This method logs the user in by checking username + password
    against the mongo database
    :return:
    """
    # Bounce any requests that are not JSON type requests
    if not request.is_json:
        raise UnsupportedMediaType()

    # Check that the request body has `username` and `password` properties
    body = request.get_json()
    if body.get('username') is None:
        raise BadRequest('missing username property')
    if body.get('password') is None:
        raise BadRequest('missing password property')

    user = mongo.db.users.find_one({'username': body.get('username')})
    if user is None:
        session.clear()
        raise BadRequest('User not found')
    if not bcrypt.check_password_hash(user['password_hash'], body.get('password')):
        session.clear()
        raise BadRequest('Password does not match')

    # this little trick is necessary because MongoDb sends back objects that are
    # CLOSE to json, but not actually JSON (principally the ObjectId is not JSON serializable)
    # so we just convert to json and use `loads` to get a dict
    serializable_user_obj = json.loads(json_util.dumps(user))
    session['user'] = serializable_user_obj
    return Response(status=200)


@app.route('/user', methods=['POST'])
def add_new_user():
    """
    This method is used to register a new user.
    :return:
    """
    # Bounce any requests that are not JSON type requests
    if not request.is_json:
        raise UnsupportedMediaType()

    # Check that the request body has `username` and `password` properties
    body = request.get_json()
    if body.get('username') is None:
        raise BadRequest('missing username property')
    if body.get('password') is None:
        raise BadRequest('missing password property')

    password_hash = bcrypt.generate_password_hash(body.get('password'))
    try:
        mongo.db.users.insert_one({'username': body.get('username'), 'password_hash': password_hash})
    except DuplicateKeyError:
        raise NotFound('User already exists')

    # check that mongo didn't fail
    return Response(status=201)


@app.route('/jobs', methods=['POST'])
def create_job():
    """
    Create a record in the jobs collection.
    Only possible if the user is logged in!!
    """
    # Bounce any requests that are not JSON type requests
    if not request.is_json:
        raise UnsupportedMediaType()

    if session.get('user') is None:
        raise Unauthorized()

    # Check that the JSON request has the fields you expect
    body = request.get_json()
    if body.get('start_time') is None:
        raise BadRequest('missing start_time property')
    if body.get('end_time') is None:
        raise BadRequest('missing end_time property')
    # ... obviously you'll want to have many more fields

    # Create a dictionary that will be inserted into Mongo
    job_record = {'start_time': body.get('start_time'), 'end_time': body.get('end_time')}
    job_record.update({'user': session['user']['_id']['$oid']})

    # Insert into the mongo collection
    res = mongo.db.jobs.insert_one(job_record)
    return Response(str(res.inserted_id), 200)


# This allows you to run locally.
# When run in GCP, Gunicorn is used instead (see entrypoint in app.yaml) to
# Access the Flack app via WSGI
if __name__ == '__main__':
    app.run(host='127.0.0.1', port=8080, debug=True)
