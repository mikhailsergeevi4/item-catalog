from flask import Flask, render_template, request, redirect,jsonify, url_for, flash
app = Flask(__name__)

from sqlalchemy import create_engine, asc
from sqlalchemy.orm import sessionmaker
from baseup import Base, Cake, Element, User

from flask import session as login_session
import random, string

from oauth2client.client import flow_from_clientsecrets
from oauth2client.client import FlowExchangeError
import httplib2
import json
from flask import make_response
import requests


CLIENT_ID = json.loads(
    open('client_secrets.json', 'r').read())['web']['client_id']
#Connect to Database and create database session
engine = create_engine('sqlite:///cakeswithusers.db')
Base.metadata.bind = engine

DBSession = sessionmaker(bind=engine)
session = DBSession()


@app.route('/')
@app.route('/cake/')
def showCakes():
  cakes = session.query(Cake).order_by(asc(Cake.name))
#  if 'username' not in login_session:
#      return render_template('publicrestaurants.html', restaurants = restaurants)
#  else:
  return render_template('main.html', cakes = cakes)

#Create a new restaurant
@app.route('/cake/new/', methods=['GET','POST'])
def newCake():
#    if 'username' not in login_session:
#        return redirect('/login')
    if request.method == 'POST':
      newCake = Cake(name = request.form['name'], description=request.form['description'], course=request.form['course'])
      session.add(newCake)
      flash('New Cake %s Successfully Created' % newCake.name)
      session.commit()
      return redirect(url_for('showCakes'))
    else:
      return render_template('ncake.html')

#Edit a restaurant
@app.route('/cake/<int:cake_id>/edit/', methods = ['GET', 'POST'])
def editCake(cake_id):
#  if 'username' not in login_session:
#        return redirect('/login')
#  if editedRestaurant.user_id != login_session['user_id']:
#        return "<script>function myFunction() {alert('You are not authorized to edit this restaurant. Please create your own restaurant in order to edit.');}</script><body onload='myFunction()''>"
  editedCake = session.query(Cake).filter_by(id = cake_id).one()
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
    return render_template('ecake.html', cake = editedCake)


#Delete a restaurant
@app.route('/cake/<int:cake_id>/delete/', methods = ['GET','POST'])
def deleteCake(cake_id):
#   if 'username' not in login_session:
#        return redirect('/login')
#   if restaurantToDelete.user_id != login_session['user_id']:
#        return "<script>function myFunction() {alert('You are not authorized to delete this restaurant. Please create your own restaurant in order to delete.');}</script><body onload='myFunction()''>"
   cakeToDelete = session.query(Cake).filter_by(id = cake_id).one()
   if request.method == 'POST':
    session.delete(cakeToDelete)
    flash('%s Successfully Deleted' % cakeToDelete.name)
    session.commit()
    return redirect(url_for('showCakes', cake_id = cake_id))
   else:
    return render_template('dcake.html', cake = cakeToDelete)

#Show a restaurant menu
@app.route('/cake/<int:cake_id>/')
@app.route('/cake/<int:cake_id>/elements/')
def showElements(cake_id):
    cake = session.query(Cake).filter_by(id=cake_id).one()
#    creator = getUserInfo(restaurant.user_id)
    elements = session.query(Element).filter_by(cake_id=cake_id).all()
#    if 'username' not in login_session or creator.id != login_session['user_id']:
#        return render_template('publicmenu.html', items=items, restaurant=restaurant, creator=creator)
#    else:
    return render_template('elements.html', elements=elements, cake=cake)

#Create a new menu item
@app.route('/cake/<int:cake_id>/elements/new/',methods=['GET','POST'])
def newElement(cake_id):
#  if 'username' not in login_session:
#      return redirect('/login')
  cake = session.query(Cake).filter_by(id = cake_id).one()
#  if login_session['user_id'] != restaurant.user_id:
#        return "<script>function myFunction() {alert('You are not authorized to add menu items to this restaurant. Please create your own restaurant in order to add items.');}</script><body onload='myFunction()''>"
  if request.method == 'POST':
      newElement = Element(name=request.form['name'], price=request.form[
                           'price'], cake_id=cake_id)
      session.add(newElement)
      session.commit()
      flash('New Element %s Item Successfully Created' % (newElement.name))
      return redirect(url_for('showElements', cake_id = cake_id))
  else:
      return render_template('nelement.html', cake_id = cake_id, cake = cake)

#Edit a menu item
@app.route('/cake/<int:cake_id>/elements/<int:element_id>/edit', methods=['GET','POST'])
def editElement(cake_id, element_id):
#    if 'username' not in login_session:
#        return redirect('/login')
    editedElement = session.query(Element).filter_by(id = element_id).one()
    cake = session.query(Cake).filter_by(id = cake_id).one()
#    if login_session['user_id'] != restaurant.user_id:
#        return "<script>function myFunction() {alert('You are not authorized to edit menu items to this restaurant. Please create your own restaurant in order to edit items.');}</script><body onload='myFunction()''>"
    if request.method == 'POST':
        if request.form['name']:
            editedElement.name = request.form['name']

        if request.form['price']:
            editedElement.price = request.form['price']

        session.add(editedElement)
        session.commit()
        flash('Element Successfully Edited')
        return redirect(url_for('showElements', cake_id = cake_id))
    else:
        return render_template('eelement.html', cake_id = cake_id, element_id = element_id, element = editedElement)


#Delete a menu item
@app.route('/cake/<int:cake_id>/elements/<int:element_id>/delete', methods = ['GET','POST'])
def deleteElement(cake_id, element_id):
#    if 'username' not in login_session:
#        return redirect('/login')
    cake = session.query(Cake).filter_by(id = cake_id).one()
    elementToDelete = session.query(Element).filter_by(id = element_id).one()
#    if login_session['user_id'] != restaurant.user_id:
#        return "<script>function myFunction() {alert('You are not authorized to delete menu items to this restaurant. Please create your own restaurant in order to delete items.');}</script><body onload='myFunction()''>"
    if request.method == 'POST':
        session.delete(elementToDelete)
        session.commit()
        flash('Element Successfully Deleted')
        return redirect(url_for('showElements', cake_id = cake_id))
    else:
        return render_template('delement.html', element = elementToDelete)



if __name__ == '__main__':
  app.secret_key = 'super_secret_key'
  app.debug = True
  app.run(host = '0.0.0.0', port = 5000)
