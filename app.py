from flask import Flask, render_template, request
from flask import redirect, jsonify, url_for, flash
from sqlalchemy import create_engine, asc
from sqlalchemy.orm import sessionmaker
from baseup import Base, Cake, Element, User

from flask import session as login_session
import random
import string

from oauth2client.client import flow_from_clientsecrets
from oauth2client.client import FlowExchangeError
import httplib2
import json
from flask import make_response
import requests

app = Flask(__name__)

CLIENT_ID = json.loads(
    open('client_secrets.json', 'r').read())['web']['client_id']
# Connect to Database and create database session
engine = create_engine('sqlite:///cakeswithusers.db')
Base.metadata.bind = engine

DBSession = sessionmaker(bind=engine)
session = DBSession()


# Route for login page
@app.route('/login')
def showLogin():
    state = ''.join(
        random.choice(
            string.ascii_uppercase + string.digits) for x in xrange(32))
    login_session['state'] = state
    return render_template('login.html', STATE=state)


# Authorization
@app.route('/gconnect', methods=['POST'])
def gconnect():
    # Validate state token
    if request.args.get('state') != login_session['state']:
        response = make_response(json.dumps('Invalid state parameter.'), 401)
        response.headers['Content-Type'] = 'application/json'
        return response
    # Obtain authorization code
    code = request.data

    try:
        # Upgrade the authorization code into a credentials object
        oauth_flow = flow_from_clientsecrets('client_secrets.json', scope='')
        oauth_flow.redirect_uri = 'postmessage'
        credentials = oauth_flow.step2_exchange(code)
    except FlowExchangeError:
        response = make_response(
            json.dumps('Failed to upgrade the authorization code.'), 401)
        response.headers['Content-Type'] = 'application/json'
        return response

    # Check that the access token is valid.
    access_token = credentials.access_token
    url = ('https://www.googleapis.com/oauth2/v1/tokeninfo?access_token=%s'
           % access_token)
    h = httplib2.Http()
    result = json.loads(h.request(url, 'GET')[1])
    # If there was an error in the access token info, abort.
    if result.get('error') is not None:
        response = make_response(json.dumps(result.get('error')), 500)
        response.headers['Content-Type'] = 'application/json'
        return response

    # Verify that the access token is used for the intended user.
    gplus_id = credentials.id_token['sub']
    if result['user_id'] != gplus_id:
        response = make_response(
            json.dumps("Token's user ID doesn't match given user ID."), 401)
        response.headers['Content-Type'] = 'application/json'
        return response

    # Verify that the access token is valid for this app.
    if result['issued_to'] != CLIENT_ID:
        response = make_response(
            json.dumps("Token's client ID does not match app's."), 401)
        print "Token's client ID does not match app's."
        response.headers['Content-Type'] = 'application/json'
        return response

    stored_access_token = login_session.get('access_token')
    stored_gplus_id = login_session.get('gplus_id')
    if stored_access_token is not None and gplus_id == stored_gplus_id:
        response = make_response(
            json.dumps('Current user is already connected.'), 200)
        response.headers['Content-Type'] = 'application/json'
        return response

    # Store the access token in the session for later use.
    login_session['access_token'] = credentials.access_token
    login_session['gplus_id'] = gplus_id

    # Get user info
    userinfo_url = "https://www.googleapis.com/oauth2/v1/userinfo"
    params = {'access_token': credentials.access_token, 'alt': 'json'}
    answer = requests.get(userinfo_url, params=params)

    data = answer.json()

    login_session['username'] = data['name']
    login_session['picture'] = data['picture']
    login_session['email'] = data['email']

    # see if user exists, if it doesn't make a new one
    user_id = getUserID(data["email"])
    if not user_id:
        user_id = createUser(login_session)
    login_session['user_id'] = user_id

    output = ''
    output += '<h1>Welcome, '
    output += login_session['username']
    output += '!</h1>'
    output += '<img src="'
    output += login_session['picture']
    output += ' " style = "width: 300px; height: 300px;border-radius: 150px;'
    output += '-webkit-border-radius: 150px;-moz-border-radius: 150px;"> '
    flash("you are now logged in as %s" % login_session['username'])
    print "done!"
    return output


# User Helper Functions
def createUser(login_session):
    newUser = User(name=login_session['username'], email=login_session[
                   'email'], picture=login_session['picture'])
    session.add(newUser)
    session.commit()
    user = session.query(User).filter_by(email=login_session['email']).one()
    return user.id


def getUserInfo(user_id):
    user = session.query(User).filter_by(id=user_id).one()
    return user


def getUserID(email):
    try:
        user = session.query(User).filter_by(email=email).one()
        return user.id
    except BaseException:
        return None


# Disconnecting user
@app.route('/gdisconnect')
def gdisconnect():
    # Only disconnect a connected user.
    access_token = login_session.get('access_token')
    if access_token is None:
        response = make_response(
            json.dumps('Current user not connected.'), 401)
        response.headers['Content-Type'] = 'application/json'
        return response
    url = 'https://accounts.google.com/o/oauth2/revoke?token=%s' % access_token
    h = httplib2.Http()
    result = h.request(url, 'GET')[0]
    if result['status'] == '200':
        del login_session['access_token']
        del login_session['gplus_id']
        del login_session['username']
        del login_session['email']
        del login_session['picture']
        response = make_response(json.dumps('Successfully disconnected.'), 200)
        response.headers['Content-Type'] = 'application/json'
        return response
    else:
        response = make_response(
            json.dumps('Failed to revoke token for given user.', 400))
        response.headers['Content-Type'] = 'application/json'
        return response


# Show all cakes
@app.route('/')
@app.route('/cake/')
def showCakes():
    cakes = session.query(Cake).order_by(asc(Cake.name))
    return render_template('main.html', cakes=cakes)


# Create a new Cake
@app.route('/cake/new/', methods=['GET', 'POST'])
def newCake():
    if 'username' not in login_session:
        return redirect('/login')
    if request.method == 'POST':
        newCake = Cake(
            name=request.form['name'], description=request.form['description'],
            course=request.form['course'], user_id=login_session['user_id'])
        session.add(newCake)
        flash('New Cake %s Successfully Created' % newCake.name)
        session.commit()
        return redirect(url_for('showCakes'))
    else:
        return render_template('ncake.html')


# Edit a Cake
@app.route('/cake/<int:cake_id>/edit/', methods=['GET', 'POST'])
def editCake(cake_id):
    if 'username' not in login_session:
        return redirect('/login')
    editedCake = session.query(Cake).filter_by(id=cake_id).one()
    if editedCake.user_id != login_session['user_id']:
        return "<script>function myFunction() {alert(\
            'You are not authorized to edit this cake.\
            Please create your own cake in order to edit.');\
            }</script><body onload='myFunction()''>"
    if request.method == 'POST':
        if request.form['course']:
            editedCake.course = request.form['course']
        if request.form['description']:
            editedCake.description = request.form['description']
        if request.form['name']:
            editedCake.name = request.form['name']
        flash('Cake Successfully Edited %s' % editedCake.name)
        return redirect(url_for('showCakes'))
    else:
        return render_template('ecake.html', cake=editedCake)


# Delete a Cake
@app.route('/cake/<int:cake_id>/delete/', methods=['GET', 'POST'])
def deleteCake(cake_id):
    if 'username' not in login_session:
        return redirect('/login')
    cakeToDelete = session.query(Cake).filter_by(id=cake_id).one()
    if cakeToDelete.user_id != login_session['user_id']:
        return "<script>function myFunction() {alert(\
            'You are not authorized to delete this cake.\
            Please create your own cake in order to delete.');\
            }</script><body onload='myFunction()''>"
    if request.method == 'POST':
        session.delete(cakeToDelete)
        flash('%s Successfully Deleted' % cakeToDelete.name)
        session.commit()
        return redirect(url_for('showCakes', cake_id=cake_id))
    else:
        return render_template('dcake.html', cake=cakeToDelete)


# Show elements in cake
@app.route('/cake/<int:cake_id>/')
@app.route('/cake/<int:cake_id>/elements/')
def showElements(cake_id):
    cake = session.query(Cake).filter_by(id=cake_id).one()
    elements = session.query(Element).filter_by(cake_id=cake_id).all()
    return render_template('elements.html', elements=elements, cake=cake)


# Create a new Element
@app.route('/cake/<int:cake_id>/elements/new/', methods=['GET', 'POST'])
def newElement(cake_id):
    if 'username' not in login_session:
        return redirect('/login')
    cake = session.query(Cake).filter_by(id=cake_id).one()
    if login_session['user_id'] != cake.user_id:
        return "<script>function myFunction() {alert(\
            'You are not authorized to add elements to this cake.\
            Please create your own cake in order to elements.');\
            }</script><body onload='myFunction()''>"
    if request.method == 'POST':
        newElement = Element(name=request.form['name'], price=request.form[
            'price'], cake_id=cake_id, user_id=cake.user_id)
        session.add(newElement)
        session.commit()
        flash('New Element %s Successfully Created' % (newElement.name))
        return redirect(url_for('showElements', cake_id=cake_id))
    else:
        return render_template('nelement.html', cake_id=cake_id, cake=cake)


# Edit a Element
@app.route('/cake/<int:cake_id>/elements/<int:element_id>/edit', methods=[
    'GET', 'POST'])
def editElement(cake_id, element_id):
    if 'username' not in login_session:
        return redirect('/login')
    editedElement = session.query(Element).filter_by(id=element_id).one()
    cake = session.query(Cake).filter_by(id=cake_id).one()
    if login_session['user_id'] != cake.user_id:
        return "<script>function myFunction() {alert(\
            'You are not authorized to edit elements to this cake.\
            Please create your own cake in order to edit elements.');\
            }</script><body onload='myFunction()''>"
    if request.method == 'POST':
        if request.form['name']:
            editedElement.name = request.form['name']
        if request.form['price']:
            editedElement.price = request.form['price']
        session.add(editedElement)
        session.commit()
        flash('Element Successfully Edited')
        return redirect(url_for('showElements', cake_id=cake_id))
    else:
        return render_template(
            'eelement.html', cake_id=cake_id,
            element_id=element_id, element=editedElement, cake=cake)


# Delete a Element
@app.route('/cake/<int:cake_id>/elements/<int:element_id>/delete', methods=[
    'GET', 'POST'])
def deleteElement(cake_id, element_id):
    if 'username' not in login_session:
        return redirect('/login')
    cake = session.query(Cake).filter_by(id=cake_id).one()
    elementToDelete = session.query(Element).filter_by(id=element_id).one()
    if login_session['user_id'] != cake.user_id:
        return "<script>function myFunction() {alert(\
        'You are not authorized to delete elements to this cake.\
        Please create your own cake in order to delete elements.');\
        }</script><body onload='myFunction()''>"
    if request.method == 'POST':
        session.delete(elementToDelete)
        session.commit()
        flash('Element Successfully Deleted')
        return redirect(url_for('showElements', cake_id=cake_id))
    else:
        return render_template(
            'delement.html', element=elementToDelete, cake=cake)


# JSON APIs to view Cake Information
@app.route('/cake/<int:cake_id>/elements/JSON')
def cakeElementsJSON(cake_id):
    cake = session.query(Cake).filter_by(id=cake_id).one()
    elements = session.query(Element).filter_by(cake_id=cake_id).all()
    return jsonify(Element=[i.serialize for i in elements])


@app.route('/cake/<int:cake_id>/elements/<int:element_id>/JSON')
def elementJSON(cake_id, element_id):
    elementVar = session.query(Element).filter_by(id=element_id).one()
    return jsonify(elementVar=elementVar.serialize)


@app.route('/cake/JSON')
def cakesJSON():
    cakes = session.query(Cake).all()
    return jsonify(cakes=[i.serialize for i in cakes])


if __name__ == '__main__':
    app.secret_key = 'super_secret_key'
    app.debug = True
    app.run(host='0.0.0.0', port=5000)
