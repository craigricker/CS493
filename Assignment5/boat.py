from flask import Blueprint, request, Response, redirect, render_template
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

    },
    'type': {
        'type': 'string',
        'minlength': 3,
        'maxlength': 256,
        'regex': '[a-zA-Z][a-zA-Z ]+[a-zA-Z]$'
    },
}
boat_validator = Validator(boat_schema, purge_unknown=True)


@bp.route('', methods=['DELETE', 'PUT', 'PATCH'])
def illegal_set_manipulations():
    response = Response(
        json.dumps({"Error": "This is action is not supported."}),
        status = 405,
        mimetype = 'application/json'
    )
    return response





@bp.route('', methods=['POST'])
def boat_create():
    """
    Store a new boat, must havve a name, length and type
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

    print(request.headers.get("Accept"))
    print(request.headers.get("Accept") != "")
    if "application/json" not in request.accept_mimetypes \
            and request.headers.get("Accept") is not None\
            and request.headers.get("Accept") != "":
        response = Response(
            response=json.dumps({"Error": "This body type is not supported."}),
            status=406,
            mimetype='application/json'
        )
        return response

    content = request.get_json()

    # Ensure no other boat has the identical name
    query = client.query(kind="boat")
    query.add_filter("name", "=", content["name"])
    results = list(query.fetch())
    if len(results) > 0:
        response = Response(
            response= json.dumps({"Error": "Boat names must be unique."}),
            status=403,
            mimetype='application/json'
        )
        return response



    new_boat = datastore.entity.Entity(key=client.key("boat"))
    new_boat.update(boat_validator.document)
    client.put(new_boat)

    new_boat["id"] = new_boat.key.id
    new_boat["self"] = request.url_root + "boats/" + str(new_boat.key.id)

    response = Response(
        response=json.dumps(new_boat),
        status=201,
        mimetype='application/json'
    )
    return response


@bp.route('/<int:id>', methods=['GET'])
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





    boat_key = client.key("boat", int(id))
    boat = client.get(key=boat_key)

    # Check the boat exists
    if not boat:

        response = Response(
            response=json.dumps({"Error": "No boat with this boat_id exists"}),
            status=404,
            mimetype='application/json'
        )
        return response
    # data = dict(boat)
    boat["id"] = boat.key.id
    boat["self"] = request.url_root + "boats/" + str(boat.key.id)
    print(str(len(request.accept_mimetypes)) + " in the accept_mimtypes")
    print(request.accept_mimetypes)

    best = request.accept_mimetypes.best_match([
        "application/json", 'text/html'
    ])
    # print("best: " + str(best))
    if request.headers.get("Accept") is None or request.headers.get("Accept") == "":
        print("Accept isn't set")
        response = Response(
            response=json.dumps(boat),
            status=200,
            mimetype='application/json'
        )
    elif best == "text/html":
        print("HTML")
        return render_template(
            'boat.html',
            boat=boat
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





@bp.route('/<int:id>', methods=['PATCH', 'PUT'])
def boat_edit(id):
    """
    Update a given boat
    :param id: boat to update
    :return: 400 if into doesnt exist, 404 if boat doesn't exist, 200 if successful
    """
    # Not all data is required for PATCH
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



    if len(request.accept_mimetypes) != 0 and "application/json" not in request.accept_mimetypes:
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
        return response
    else:
        return redirect(boat["self"], code=303)




@bp.route('/<int:id>', methods=['DELETE'])
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

    # Throw 400 if data in body
    if request.data:
        failed = {"Error": "The request object does not follow specifications - see documentation."}
        response = Response(
            response=json.dumps(failed),
            status=400,
            mimetype='application/json'
        )
        return response


    client.delete(boat_key)

    response = Response(
        status=204,
        mimetype='application/json'
    )
    return response


