import datetime

from flask import Flask, render_template, flash, redirect, request
from app.forms import BasicForm

import os
SECRET_KEY = os.urandom(32)

app = Flask(__name__)

app.config['SECRET_KEY'] = SECRET_KEY

@app.route('/')
def root():
    # For the sake of example, use static information to inflate the template.
    # This will be replaced with real information in later steps.
    form = BasicForm()
    return render_template('form.html',title="Basic Information", form=form )

@app.route('/index')
def index():
    return render_template('index.html', title='Data Display')

@app.route('/submit', methods=['GET', 'POST'])
def login():
    form = BasicForm()
    flash('Your name is {}, and your favourite color is {}! I hope this is basic enough information to get full credit'.format(
        form.name.data, form.color.data))
    return redirect('/index')

if __name__ == '__main__':
    # This is used when running locally only. When deploying to Google App
    # Engine, a webserver process such as Gunicorn will serve the app. This
    # can be configured by adding an `entrypoint` to app.yaml.
    # Flask's development server will automatically serve static files in
    # the "static" directory. See:
    # http://flask.pocoo.org/docs/1.0/quickstart/#static-files. Once deployed,
    # App Engine itself will serve those files as configured in app.yaml.
    app.run(host='127.0.0.1', port=8080, debug=True)

