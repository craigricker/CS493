# -*- coding: utf-8 -*-
# Copyright 2018 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import datetime
import boat
import load

from flask import Flask, render_template, request, json


# [START gae_python37_datastore_store_and_fetch_times]
from google.cloud import datastore



# [END gae_python37_datastore_store_and_fetch_times]
app = Flask(__name__)
app.register_blueprint(boat.bp)
app.register_blueprint(load.bp)
client = datastore.Client()


# [START gae_python37_datastore_store_and_fetch_times]

def store_time(dt):
    """
    Google provided function, store the time when site is visited
    :param dt: time when visited
    :return: none
    """
    entity = datastore.Entity(key=datastore_client.key('visit'))
    entity.update({
        'timestamp': dt
    })

    datastore_client.put(entity)


def fetch_times(limit):
    """
    Google provided function, get the previous times this person visited
    :param limit:
    :return:
    """
    query = datastore_client.query(kind='visit')
    query.order = ['-timestamp']

    times = query.fetch(limit=limit)

    return times


# [END gae_python37_datastore_store_and_fetch_times]


# [START gae_python37_datastore_render_times]
@app.route('/')
def root():
    """
    Google provided function, root directory
    Display the last ten times the page was visited
    :return:
    """
    # Store the current access time in Datastore.
    store_time(datetime.datetime.now())

    # Fetch the most recent 10 access times from Datastore.
    times = fetch_times(10)

    return render_template(
        'index.html', times=times)


# [END gae_python37_datastore_render_times]



def validate_slip_create(request):
    """
    Ensure a slip has required information to be stored
    :param request:
    :return:
    """
    return "number" not in request.json





@app.route('/slips', methods=['POST'])
def slip_create():
    """
    Create a new slip with given information, throw 400 if not all info provided
    :return:
    """
    # Validate input
    if validate_slip_create(request):
        failed = {"Error": "The request object is missing the required number"}
        response = app.response_class(
            response=json.dumps(failed),
            status=400,
            mimetype='application/json'
        )
        return response

    content = request.get_json()
    new_slip = datastore.entity.Entity(key=client.key("slip"))
    # A new slip defaults to no current boat
    new_slip.update({
        "number": content["number"],
        "current_boat": None,
    })
    client.put(new_slip)

    new_slip["id"] = new_slip.key.id
    new_slip["self"] = request.url_root + "slips/" + str(new_slip.key.id)

    response = app.response_class(
        response=json.dumps(new_slip),
        status=201,
        mimetype='application/json'
    )
    return response


@app.route('/slips/<id>', methods=['GET'])
def slip_show(id):
    """
    Return info associated with provided slip id
    :param id:
    :return: 200 if sucessful, 404 if resource doesn't exist
    """
    slip_key = client.key("slip", int(id))
    slip = client.get(key=slip_key)

    if slip:
        data = dict(slip)
        data["id"] = slip.key.id
        data["self"] = request.url_root + "slips/" + str(slip.key.id)

        response = app.response_class(
            response=json.dumps(data),
            status=200,
            mimetype='application/json'
        )
        return response
    else:
        response = app.response_class(
            response=json.dumps({"Error": "No slip with this slip_id exists"}),
            status=404,
            mimetype='application/json'
        )
        return response


@app.route('/slips', methods=['GET'])
def slip_index():
    """
    Return all slips stored in database
    :return:
    """
    query = datastore_client.query(kind="slip")
    slips = list(query.fetch())
    for slip in slips:
        slip["id"] = slip.key.id
        slip["self"] = request.url_root + "slips/" + str(slip.key.id)

    response = app.response_class(
        response=json.dumps(slips),
        status=200,
        mimetype='application/json'
    )
    return response


@app.route('/slips/<slip_id>/<boat_id>', methods=["PUT"])
def boat_arrives(slip_id, boat_id):
    """
    the 'boat arrives' means you store the boat id in the given
    slip.
    :param slip_id: slip to store boat id
    :param boat_id: boat that arrives at the slip
    :return: 404 if slip/boat doesn't exist, 403 if slip full, 204 if successful
    """
    # Get objects
    slip_key = client.key("slip", int(slip_id))
    slip = client.get(key=slip_key)
    boat_key = client.key("boat", int(boat_id))
    boat = client.get(key=boat_key)
    if not slip or not boat:
        response = app.response_class(
            response=json.dumps({"Error": "The specified boat and/or slip don’t exist"}),
            status=404,
            mimetype='application/json'
        )
        return response

    if slip["current_boat"]:
        response = app.response_class(
            response=json.dumps({"Error": "The slip is not empty"}),
            status=403,
            mimetype='application/json'
        )
        return response

    slip.update({
        "current_boat": boat.key.id
    })
    client.put(slip)
    response = app.response_class(
        status=204,
        mimetype='application/json'
    )
    return response


@app.route('/slips/<slip_id>', methods=["DELETE"])
def slip_delete(slip_id):
    """
    Delete slip with slip_id
    :param slip_id:
    :return:
    """
    slip_key = client.key("slip", int(slip_id))
    slip = client.get(key=slip_key)
    if not slip:
        failed = {"Error": "No slip with this slip_id exists"}
        response = app.response_class(
            response=json.dumps(failed),
            status=404,
            mimetype='application/json'
        )
        return response
    client.delete(slip_key)
    response = app.response_class(
        status=204,
        mimetype='application/json'
    )
    return response


@app.route('/slips/<slip_id>/<boat_id>', methods=["DELETE"])
def boat_departs(slip_id, boat_id):
    """
    boat departs slip - remove stored value
    :param slip_id:
    :return: 404 if failure, 204 if successful
    """
    # Get objects
    slip_key = client.key("slip", int(slip_id))
    slip = client.get(key=slip_key)
    boat_key = client.key("boat", int(boat_id))
    boat = client.get(key=boat_key)

    if not slip or not boat or "current_boat" not in slip or slip["current_boat"] != boat.key.id:
        response = app.response_class(
            response=json.dumps({"Error": "No boat with this boat_id is at the slip with this slip_id"}),
            status=404,
            mimetype='application/json'
        )
        return response

    slip.update({
        "current_boat": None
    })
    client.put(slip)
    response = app.response_class(
        status=204,
        mimetype='application/json'
    )
    return response




if __name__ == '__main__':
    # This is used when running locally only. When deploying to Google App
    # Engine, a webserver process such as Gunicorn will serve the app. This
    # can be configured by adding an `entrypoint` to app.yaml.

    # Flask's development server will automatically serve static files in
    # the "static" directory. See:
    # http://flask.pocoo.org/docs/1.0/quickstart/#static-files. Once deployed,
    # App Engine itself will serve those files as configured in app.yaml.
    app.run(host='127.0.0.1', port=8080, debug=True)
