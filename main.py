import json

from bson import json_util
from flask import Flask, request, Response, session, jsonify
from flask_bcrypt import Bcrypt
from flask_pymongo import PyMongo
from pymongo.errors import DuplicateKeyError
from werkzeug.exceptions import BadRequest, NotFound, UnsupportedMediaType, Unauthorized
from exceptions import JSONExceptionHandler


from bson.json_util import dumps



# This defines a Flask application
app = Flask(__name__)

# This code here converts Flask's default (HTML) errors to Json errors.
# This is helpful because HTML breaks clients that are expecting JSON
JSONExceptionHandler(app)

# We configure the app object
# app.config['MONGO_DBNAME'] = 'moving_database'
app.config['MONGO_DBNAME'] = 'cam_db'
app.config['MONGO_HOST'] = 'ds129166.mlab.com:29166'
app.config['MONGO_USERNAME'] = 'cameronUsername'
app.config['MONGO_PASSWORD'] = 'cameron25'



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


# @app.route('/user', methods=['GET'])
# def who_am_i():
#     """
#     Simple method just to show how you can access session data
#     :return:
#     """
#     if session.get('user') is None:
#         raise Unauthorized()
#     return jsonify(session.get('user'))



@app.route('/user/<user_id>', methods=['GET'])
def who_am_i(user_id):
    """
    user_id is the user_id of the user we are trying to retrieve
    """
    if session.get('user') is None:
        raise Unauthorized()
    print (user_id)
    result = jsonify(dumps(list(mongo.db.users.find({'_id':user_id}))))

    return result





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

    user = mongo.db.users.find_one({'_id': body.get('username')})
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

    print (body.get('username'))
    print (body.get('password'))
    password_hash = bcrypt.generate_password_hash(body.get('password'))
    try:
        if mongo is not None:
            print ("dis dicky")
            print (mongo)
        else:
            print ("bitch")
        mongo.db.users.insert_one({'_id': body.get('username'), 'password_hash': password_hash, 'first_name': body.get('first_name'), 'last_name': body.get('last_name'), 'phone_number': body.get('phone_number')})
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
        print ("we dont a session user!")
        raise Unauthorized()

    # Check that the JSON request has the fields you expect
    body = request.get_json()
    if body.get('start_time') is None:
        raise BadRequest('missing start_time property')
    if body.get('finish_by') is None:
        raise BadRequest('missing finish_by property')
    
    # ... obviously you'll want to have many more fields

    # Create a dictionary that will be inserted into Mongo
    #job_record = {'start_time': body.get('start_time'), 'finish_by': body.get('finish_by'), "max_price": body.get('max_price'), "rooms_to_move":body.get('rooms_to_move'), "address":body.get("address"),"mover":body.get("mover"),"hauler":body.get("hauler"), "description":body.get("description") }
    #job_record.update({'user': session['user']['_id']['$oid']})

    # Insert into the mongo collection
    #res = mongo.db.jobs.insert_one(job_record)

    print ('mover below')
    print (body.get('mover'))
    numInside = mongo.db.jobs.find({"mover": body.get('mover'), "hauler":None}).count()
    print ("num inside below")
    print (numInside)
    if numInside !=0: #each mover can o
        raise BadRequest('You cant make more than one request!')
   

    mongo.db.jobs.insert_one({'start_time': body.get('start_time'), 'finish_by': body.get('finish_by'), "max_price": body.get('max_price'), "rooms_to_move":body.get('rooms_to_move'), "address":body.get("address"),"mover":body.get("mover"),"hauler":body.get("hauler"), "description":body.get("description") })
    
    return Response(status=201)

    #return Response(str(res.inserted_id), 200)


@app.route("/jobs", methods = ['GET']) #/jobs/<user_id>
def get_jobs():
    """
    Return the records in the job collection for which the hauler field is null
    """
    if not request.is_json:
        raise UnsupportedMediaType()
    if session.get('user') is None:
        raise Unauthorized()
    result = jsonify(dumps(list(mongo.db.jobs.find({'hauler': None}))))
    return result 


@app.route("/jobs/<user_id>", methods = ['GET']) #/jobs/<user_id>
def get_jobs2(user_id):
    """
    Return the most recent record in job collection for which mover field is user_id
    """
    if not request.is_json:
        raise UnsupportedMediaType()
    if session.get('user') is None:
        raise Unauthorized()
    
    # result = jsonify(dumps(list(mongo.db.jobs.find({"mover":user_id, "hauler" : {$nin : None}}).sort("_id", -1).limit(1))))

    # "$and": [{"field": var1}, {"field": {"$ne": var2}}

    result = jsonify(dumps(list(mongo.db.jobs.find({"mover":user_id}).sort("_id", -1).limit(1))))

    return result


# @app.route("/jobs/<user_id>", methods = ['GET']) #/jobs/<user_id>
# def get_jobs2(user_id):
#     """
#     Return the record in job collection for which mover field is user_id and hauler is not None
#     """
#     if not request.is_json:
#         raise UnsupportedMediaType()
#     if session.get('user') is None:
#         raise Unauthorized()
    
#     # result = jsonify(dumps(list(mongo.db.jobs.find({"mover":user_id, "hauler" : {$nin : None}}).sort("_id", -1).limit(1))))

#     # "$and": [{"field": var1}, {"field": {"$ne": var2}}

#     result = jsonify(dumps(list(mongo.db.jobs.find({"$and": [{"mover":user_id}, {"hauler":{"$ne":None}}]}).sort("_id", -1).limit(1))))

#     return result





    # db.jobs.find({"mover":"cameron", "hauler" : {$ne : null}}).sort({_id: -1}).limit(1)

    # db.jobs.find({'mover':"cameron"}).sort({_id: -1}).limit(1)



    # if not request.is_json:
    #     raise UnsupportedMediaType()
    # if session.get('user') is None:
    #     raise Unauthorized()
    # result = jsonify(dumps(list(mongo.db.jobs.find({'hauler': None}))))
    # return result 




    
    #return Response(status=200)

@app.route("/jobs", methods = ['PUT'])
def service_job():
    """
    Update the jobs collection to reflect that hauler serviced a job
    Body: {mover: x, hauler: y}
    """
    if not request.is_json:
        raise UnsupportedMediaType()
    body = request.get_json()
    mongo.db.jobs.update({'mover':body.get('mover'), 'hauler':None}, {"$set": {"hauler":body.get('hauler')}}, upsert=False)

    #collection.remove({"date": {"$gt": "2012-12-15"}})

    print (body)
    return Response(status=201)





# This allows you to run locally.
# When run in GCP, Gunicorn is used instead (see entrypoint in app.yaml) to
# Access the Flack app via WSGI
if __name__ == '__main__':
    app.run(host='127.0.0.1', port=8080, debug=True)
