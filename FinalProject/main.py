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
from requests_oauthlib import OAuth2Session
from google.oauth2 import id_token
from google.auth import crypt
from google.auth import jwt
from google.auth.transport import requests
from google.cloud import logging
# import os
# os.environ['OAUTHLIB_INSECURE_TRANSPORT'] = '1'



from google.cloud import datastore




app = Flask(__name__)
app.register_blueprint(boat.bp)
app.register_blueprint(load.bp)
client = datastore.Client()


# These should be copied from an OAuth2 Credential section at
# https://console.cloud.google.com/apis/credentials
client_id = r'1015356522518-kb3fbcmv2h8karkq496f3fph9cn4cf4s.apps.googleusercontent.com'
client_secret = r'hIKV1KNbl8E19hqTdC-Mise7'

# This is the page that you will use to decode and collect the info from
# the Google authentication flow
redirect_uri = 'https://rickercr-finalproject.appspot.com/oauth'
# redirect_uri = 'http://localhost:8080/oauth'

# These let us get basic info to identify a user and not much else
# they are part of the Google People API
scope = ['https://www.googleapis.com/auth/userinfo.email',
             'https://www.googleapis.com/auth/userinfo.profile', 'openid']
oauth = OAuth2Session(client_id, redirect_uri=redirect_uri,
                          scope=scope)


# This link will redirect users to begin the OAuth flow with Google
@app.route('/')
def index():
    authorization_url, state = oauth.authorization_url(
        'https://accounts.google.com/o/oauth2/auth',
        # access_type and prompt are Google specific extra
        # parameters.
        access_type="offline", prompt="select_account")
    return render_template(
        'index.html',
        oathUrl=authorization_url
    )

@app.route('/about', methods=['GET'])
def about():
    return render_template(
        'about.html'
    )


# This is where users will be redirected back to and where you can collect
# the JWT for use in future requests
@app.route('/oauth')
def oauthroute():
    print("The client secret is {}".format(client_secret))
    print("authorization response is {}".format(request.url))
    token = oauth.fetch_token(
        'https://accounts.google.com/o/oauth2/token',
        authorization_response=request.url,
        client_secret=client_secret)
    req = requests.Request()

    id_info = id_token.verify_oauth2_token(
    token['id_token'], req, client_id)

    return render_template(
        'information.html',
        jwt=token["id_token"]
    )


def verify():
    req = requests.Request()
    print(request.args)
    # print(request.headers.get("Authorization"))
    print(req)
    try:
        jwt = request.headers.get("Authorization").split()[-1]
        id_info = id_token.verify_oauth2_token(
        jwt, req, client_id)
        return id_info
    except:
        return False



if __name__ == '__main__':
    # This is used when running locally only. When deploying to Google App
    # Engine, a webserver process such as Gunicorn will serve the app. This
    # can be configured by adding an `entrypoint` to app.yaml.

    # Flask's development server will automatically serve static files in
    # the "static" directory. See:
    # http://flask.pocoo.org/docs/1.0/quickstart/#static-files. Once deployed,
    # App Engine itself will serve those files as configured in app.yaml.
    app.run(host='127.0.0.1', port=8080, debug=True)
