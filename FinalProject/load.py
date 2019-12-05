from flask import Blueprint, request, Response
from google.cloud import datastore
import json
from cerberus import Validator

datastore_client = datastore.Client()
client = datastore.Client()

bp = Blueprint('load', __name__, url_prefix='/loads')

load_schema = {
    'name': {
        'type': 'string',
        'minlength': 3,
        'maxlength': 256,
        'regex': '[a-zA-Z][a-zA-Z ]+[a-zA-Z]$'

    },
    'content': {
        'type': 'integer',
        'min': 1,
        'max': 20000

    },
    'description': {
        'type': 'string',
        'minlength': 3,
        'maxlength': 256,
        'regex': '[a-zA-Z][a-zA-Z ]+[a-zA-Z]$'
    },
}
load_validator = Validator(load_schema, purge_unknown=True)


@bp.route('', methods=['POST'])
def load_create():
    """
    Store a new load, must havve a name, length and type
    :return: 400 if not all info provided, 201 if successful
    """
    # Ensure boat has all required information, return error otherwise
    load_validator.require_all = True

    if request.get_json() is None\
            or not request.data \
            or not load_validator.validate(request.get_json()):

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
    new_load = datastore.entity.Entity(key=client.key("load"))
    new_load.update({
        "weight": content["weight"],
        "content": content["content"],
        "description": content["description"],
        "carrier": None,
    })
    client.put(new_load)

    new_load["id"] = new_load.key.id
    new_load["self"] = request.url_root + "loads/" + str(new_load.key.id)

    response = Response(
        response=json.dumps(new_load),
        status=201,
        mimetype='application/json'
    )
    return response


@bp.route('/<id>', methods=['GET'])
def load_show(id):
    """
    Show the load with the coresponding ID
    :param id: load to return info on
    :return: 200 if successful, 404 otherwise
    """
    best = request.accept_mimetypes.best_match([
        "application/json", 'text/html'
    ])
    if id is None or request.data:
        failed = {"Error": "The request object does not follow specifications - see documentation."}
        return Response(
            response=json.dumps(failed),
            status=400,
            mimetype='application/json'
        )
    elif best != "application/json":
        response = Response(
            response=json.dumps({"Error": "This body type is not supported."}),
            status=406,
            mimetype='application/json'
        )
    # Get the load from datastore
    load_key = client.key("load", int(id))
    load = client.get(key=load_key)

    # Check the load exists
    if load:
        data = dict(load)
        data["id"] = load.key.id
        data["self"] = request.url_root + "loads/" + str(load.key.id)
        if data["carrier"]:
            data["carrier"]["self"] = request.url_root + "boats/" + str(data["carrier"]["id"])

        response = Response(
            response=json.dumps(data),
            status=200,
            mimetype='application/json'
        )
        return response
    else:
        response = Response(
            response=json.dumps({"Error": "No load with this load_id exists"}),
            status=404,
            mimetype='application/json'
        )
        return response


@bp.route('/<id>', methods=['PATCH', 'PUT'])
def load_edit(id):
    """
    Update a given load
    :param id: load to update
    :return: 400 if into doesnt exist, 404 if load doesn't exist, 200 if successful
    """
    # Return error if not all information present
    # Return error if not all information present
    if request.method == "PATCH":
        load_validator.require_all = False
    else:
        load_validator.require_all = True

    if request.get_json() is None\
            or not request.data \
            or not load_validator.validate(request.get_json())\
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

    load_key = client.key("load", int(id))
    load = client.get(key=load_key)
    # Return error if load doesn't exist
    if not load:
        failed = {"Error": "No load with this load_id exists"}
        response = Response(
            response=json.dumps(failed),
            status=404,
            mimetype='application/json'
        )
        return response

    content = request.get_json()
    load.update({
        "name": content["name"],
        "length": content["length"],
        "type": content["type"]
    })
    client.put(load)

    load["id"] = load.key.id
    load["self"] = request.url_root + "loads/" + str(load.key.id)

    # Return the updated boat if PATCH
    if request.method == "PATCH":
        response = Response(
            response=json.dumps(load),
            status=200,
            mimetype='application/json'
        )
    else:
        response = Response(
            status=303,
            mimetype='application/json',
        )
        response.headers.set("Location", load["self"])

    return response


@bp.route('/<id>', methods=['DELETE'])
def load_delete(id):
    """
    Delete the load with given id
    :param id:
    :return: 404 if load doesn't exist, 204 on successful deletion
    """
    load_key = client.key("load", int(id))
    load = client.get(key=load_key)
    if not load:
        failed = {"Error": "No load with this load_id exists"}
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
    client.delete(load_key)

    # Remove load from the boat if it was on one
    if load["carrier"]:
        boat_key = client.key("boat", load["carrier"]["id"])
        boat = client.get(key=boat_key)

        # for load in boat["loads"]:
        loads = [x for x in boat["loads"] if x["id"] != int(id)]
        boat.update({"loads": loads})
        client.put(boat)

    response = Response(
        status=204,
        mimetype='application/json'
    )
    return response


@bp.route('', methods=['GET'])
def load_index():
    """
    Return all loads stored
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

    query = client.query(kind="load")
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
        e["self"] = request.url_root + "loads/" + str(e.key.id)
        if e["carrier"]:
            e["carrier"]["self"] = request.url_root + "boats/" + str(e["carrier"]["id"])
    output = {"loads": results}
    if next_url:
        output["next"] = next_url
    return Response(
        response=json.dumps(output),
        status=200,
        mimetype='application/json'
    )
