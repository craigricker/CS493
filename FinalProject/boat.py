from flask import Blueprint, request, Response
from google.cloud import datastore
import json
from cerberus import Validator

datastore_client = datastore.Client()
client = datastore.Client()

bp = Blueprint('boat', __name__, url_prefix='/boats')

boat_schema = {
    'name': {
        'type': 'string',
        'minlength': 3,
        'maxlength': 256,
        'regex': '[a-zA-Z][a-zA-Z ]+[a-zA-Z]$'

    },
    'length': {
        'type': 'integer',
        'min': 1,
        'max': 20000

    },
    'type': {
        'type': 'string',
        'minlength': 3,
        'maxlength': 256,
        'regex': '[a-zA-Z][a-zA-Z ]+[a-zA-Z]$'
    },
}
boat_validator = Validator(boat_schema, purge_unknown=True)


def validate_boat_create(request):
    """
    Ensure the boat has required information
    :param request:
    :return:
    """
    return "name" not in request.json or \
           "length" not in request.json or \
           "type" not in request.json


@bp.route('', methods=['POST'])
def boat_create():
    """
    Store a new boat, must have a name, length and type
    :return: 400 if not all info provided, 201 if successful
    """
    # Ensure boat has all required information, return error otherwise
    boat_validator.require_all = True

    if request.get_json() is None\
            or not request.data \
            or not boat_validator.validate(request.get_json()):

        failed = {"Error": "The request object does not follow specifications - see documentation."}
        response = Response(
            response=json.dumps(failed),
            status=400,
            mimetype='application/json'
        )
        return response
    elif "application/json" not in request.accept_mimetypes \
            and request.headers.get("Accept") is not None\
            and request.headers.get("Accept") != "":
        response = Response(
            response=json.dumps({"Error": "This body type is not supported."}),
            status=406,
            mimetype='application/json'
        )
        return response

    content = request.get_json()
    new_boat = datastore.entity.Entity(key=client.key("boat"))
    new_boat.update({
        "name": content["name"],
        "length": content["length"],
        "type": content["type"],
        "loads": [],
    })
    client.put(new_boat)

    new_boat["id"] = new_boat.key.id
    new_boat["self"] = request.url_root + "boats/" + str(new_boat.key.id)

    response = Response(
        response=json.dumps(new_boat),
        status=201,
        mimetype='application/json'
    )
    return response


@bp.route('/<id>', methods=['GET'])
def boat_show(id):
    """
    Show the boat with the coresponding ID
    :param id: boat to return info on
    :return: 200 if successful, 404 otherwise
    """

    if id is None or request.data:
        failed = {"Error": "The request object does not follow specifications - see documentation."}
        response = Response(
            response=json.dumps(failed),
            status=400,
            mimetype='application/json'
        )
        return response

    # Get the boat from datastore
    boat_key = client.key("boat", int(id))
    boat = client.get(key=boat_key)

    # Check the boat exists
    if boat:
        # data = dict(boat)
        boat["id"] = boat.key.id
        boat["self"] = request.url_root + "boats/" + str(boat.key.id)

        for load in boat["loads"]:
            load["self"] = request.url_root + "loads/" + str(load["id"])
    else:
        response = Response(
            response=json.dumps({"Error": "No boat with this boat_id exists"}),
            status=404,
            mimetype='application/json'
        )
        return response

    best = request.accept_mimetypes.best_match([
        "application/json", 'text/html'
    ])

    if request.headers.get("Accept") is None or request.headers.get("Accept") == "":
        response = Response(
            response=json.dumps(boat),
            status=200,
            mimetype='application/json'
        )
    elif best == "application/json":
        response = Response(
            response=json.dumps(boat),
            status=200,
            mimetype='application/json'
        )
    else:
        response = Response(
            response=json.dumps({"Error": "This body type is not supported."}),
            status=406,
            mimetype='application/json'
        )

    return response


@bp.route('/<id>', methods=['PATCH', 'PUT'])
def boat_edit(id):
    """
    Update a given boat
    :param id: boat to update
    :return: 400 if into doesnt exist, 404 if boat doesn't exist, 200 if successful
    """
    # Return error if not all information present
    if request.method == "PATCH":
        boat_validator.require_all = False
    else:
        boat_validator.require_all = True

    if request.get_json() is None\
            or not request.data \
            or not boat_validator.validate(request.get_json())\
            or not request.content_type == 'application/json':

        failed = {"Error": "The request object does not follow specifications - see documentation."}
        response = Response(
            response=json.dumps(failed),
            status=400,
            mimetype='application/json'
        )
        return response



    elif len(request.accept_mimetypes) != 0 and "application/json" not in request.accept_mimetypes:
        response = Response(
            response=json.dumps({"Error": "This body type is not supported."}),
            status=406,
            mimetype='application/json'
        )
        return response

    # Ensure no other boat has the identical name
    if "name" in request.json:
        query = client.query(kind="boat")
        query.add_filter("name", "=", request.get_json()["name"])
        results = query.fetch()
        results = list(results)
        if len(results) > 0 and results[0].key.id != int(id):
            response = Response(
                response= json.dumps({"Error": "Boat names must be unique."}),
                status=403,
                mimetype='application/json'
            )
            return response

    boat_key = client.key("boat", int(id))
    boat = client.get(key=boat_key)
    # Return error if boat doesn't exist
    if not boat:
        failed = {"Error": "No boat with this boat_id exists"}
        response = Response(
            response=json.dumps(failed),
            status=404,
            mimetype='application/json'
        )
        return response

    boat.update(boat_validator.document)
    client.put(boat)

    boat["id"] = boat.key.id
    boat["self"] = request.url_root + "boats/" + str(boat.key.id)

    # Return the updated boat if PATCH
    if request.method == "PATCH":
        response = Response(
            response=json.dumps(boat),
            status=200,
            mimetype='application/json'
        )
    else:
        response = Response(
            status=303,
            mimetype='application/json',
        )
        response.headers.set("Location", boat["self"])

    return response


@bp.route('/<id>', methods=['DELETE'])
def boat_delete(id):
    """
    Delete the boat with given id
    :param id:
    :return: 404 if boat doesn't exist, 204 on successful deletion
    """
    boat_key = client.key("boat", int(id))
    boat = client.get(key=boat_key)
    if not boat:
        failed = {"Error": "No boat with this boat_id exists"}
        response = Response(
            response=json.dumps(failed),
            status=404,
            mimetype='application/json'
        )
        return response
    elif request.data:
        failed = {"Error": "The request object does not follow specifications - see documentation."}
        response = Response(
            response=json.dumps(failed),
            status=400,
            mimetype='application/json'
        )
        return response

    client.delete(boat_key)

    # Remove association with all loads
    for load in boat["loads"]:
        load_key = client.key("load", load["id"])
        load = client.get(key=load_key)
        # load = client.get(key=str(load["id"]))
        load.update({"carrier": None})
        client.put(load)

    response = Response(
        status=204,
        mimetype='application/json'
    )
    return response


@bp.route('', methods=['GET'])
def boat_index():
    """
    Return all boats stored
    :return:
    """

    if len(request.accept_mimetypes) != 0 and "application/json" not in request.accept_mimetypes:
        response = Response(
            response=json.dumps({"Error": "This body type is not supported."}),
            status=406,
            mimetype='application/json'
        )
        return response
    elif request.data:
        failed = {"Error": "The request object does not follow specifications - see documentation."}
        response = Response(
            response=json.dumps(failed),
            status=400,
            mimetype='application/json'
        )
        return response


    query = client.query(kind="boat")
    q_limit = int(request.args.get('limit', '3'))
    q_offset = int(request.args.get('offset', '0'))
    l_iterator = query.fetch(limit=q_limit, offset=q_offset)
    pages = l_iterator.pages
    results = list(next(pages))
    if l_iterator.next_page_token:
        next_offset = q_offset + q_limit
        next_url = request.base_url + "?limit=" + str(q_limit) + "&offset=" + str(next_offset)
    else:
        next_url = None
    for e in results:
        e["id"] = e.key.id
        e["self"] = request.url_root + "boats/" + str(e.key.id)
        for load in e["loads"]:
            load["self"] = request.url_root + "loads/" + str(load["id"])
    output = {"boats": results}
    if next_url:
        output["next"] = next_url

    count_query = client.query()

    response = Response(
        status=200,
        response=json.dumps(output),
        mimetype='application/json'
    )
    return response


@bp.route('/<b_id>/loads/<l_id>', methods=['PUT'])
def add_load(b_id, l_id):
    if len(request.accept_mimetypes) != 0 and "application/json" not in request.accept_mimetypes:
        response = Response(
            response=json.dumps({"Error": "This body type is not supported."}),
            status=406,
            mimetype='application/json'
        )
        return response
    elif request.data:
        failed = {"Error": "The request object does not follow specifications - see documentation."}
        response = Response(
            response=json.dumps(failed),
            status=400,
            mimetype='application/json'
        )
        return response


    boat_key = client.key("boat", int(b_id))
    boat = client.get(key=boat_key)
    load_key = client.key("load", int(l_id))
    load = client.get(key=load_key)
    if not boat or not load:
        failed = {"Error": "One of these resources does not exist"}
        response = Response(
            response=json.dumps(failed),
            status=404,
            mimetype='application/json'
        )
        return response

    # If the load is already on a boat, don't change
    if load["carrier"]:
        response = Response(
            response=json.dumps({"Error": "The load is already on a boat"}),
            status=403,
            mimetype='application/json'
        )
        return response

    # Save boat to the load
    load.update({
        "carrier": {
            "id": boat.key.id,
            "name": boat["name"],
        }
    })
    client.put(load)

    # Add load to the boat
    boat["loads"].append({
        "id": load.key.id,
    })
    client.put(boat)
    response = Response(
        status=204,
        mimetype='application/json'
    )
    return response


@bp.route('/<b_id>/loads/<l_id>', methods=['DELETE'])
def remove_load(b_id, l_id):
    if len(request.accept_mimetypes) != 0 and "application/json" not in request.accept_mimetypes:
        response = Response(
            response=json.dumps({"Error": "This body type is not supported."}),
            status=406,
            mimetype='application/json'
        )
        return response
    elif request.data:
        failed = {"Error": "The request object does not follow specifications - see documentation."}
        response = Response(
            response=json.dumps(failed),
            status=400,
            mimetype='application/json'
        )
        return response
    boat_key = client.key("boat", int(b_id))
    boat = client.get(key=boat_key)
    load_key = client.key("load", int(l_id))
    load = client.get(key=load_key)
    if not boat or not load:
        failed = {"Error": "One of these resources does not exist"}
        response = Response(
            response=json.dumps(failed),
            status=404,
            mimetype='application/json'
        )
        return response


    if not load["carrier"] or load["carrier"]["id"] != int(b_id):
        response = Response(
            response=json.dumps({"Error": "The load it not on that boat"}),
            status=403,
            mimetype='application/json'
        )
        return response

    # Save boat to the load
    load.update({
        "carrier": None
    })
    client.put(load)

    # Add load to the boat
    boat["loads"].remove({
        "id": load.key.id
    })
    client.put(boat)
    response = Response(
        status=204,
        mimetype='application/json'
    )
    return response


@bp.route('/<b_id>/loads/', methods=['GET'])
def get_boats_loads(b_id):
    if len(request.accept_mimetypes) != 0 and "application/json" not in request.accept_mimetypes:
        response = Response(
            response=json.dumps({"Error": "This body type is not supported."}),
            status=406,
            mimetype='application/json'
        )
        return response
    elif request.data:
        failed = {"Error": "The request object does not follow specifications - see documentation."}
        response = Response(
            response=json.dumps(failed),
            status=400,
            mimetype='application/json'
        )
        return response

    boat_key = client.key("boat", int(b_id))
    boat = client.get(key=boat_key)
    if not boat:
        response = Response(
            response=json.dumps({"Error": "No boat with this boat_id exists"}),
            status=404,
            mimetype='application/json'
        )
        return response

    # Loop through and add value
    for load in boat["loads"]:
        load["self"] = request.url_root + "loads/" + str(load["id"])


    response = Response(
        response=json.dumps(boat["loads"]),
        status=200,
        mimetype='application/json'
    )
    return response


@bp.route('', methods=['DELETE', 'PUT', 'PATCH'])
def illegal_set_manipulations():
    response = Response(
        json.dumps({"Error": "This is action is not supported."}),
        status = 405,
        mimetype = 'application/json'
    )
    return response