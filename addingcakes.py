from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from baseup import Cake, Base, Element, User

engine = create_engine('sqlite:///cakeswithusers.db')
# Bind the engine to the metadata of the Base class so that the
# declaratives can be accessed through a DBSession instance
Base.metadata.bind = engine

DBSession = sessionmaker(bind=engine)
# A DBSession() instance establishes all conversations with the database
# and represents a "staging zone" for all the objects loaded into the
# database session object. Any change made against the objects in the
# session won't be persisted into the database until you call
# session.commit(). If you're not happy about the changes, you can
# revert all of them back to the last commit by calling
# session.rollback()
session = DBSession()

# Create dummy user
User1 = User(name="Kristina", email="kulchihinakristi@gmail.com",
             picture='http://xn----8sbiecm6bhdx8i.xn--p1ai/sites/default/files/images/uchitelu/risunok_tort.jpg')
session.add(User1)
session.commit()


#Cake Chocolate
cake1 = Cake(name = "Zaher", description = "Cholocate biscuit with kompate dried apricots", course = "Cholocate")

session.add(cake1)
session.commit()


element1 = Element(name = "Chocolate", price = "$1", element = cake1)

session.add(element1)
session.commit()

element2 = Element(name = "flour", price = "$0.50", element = cake1)

session.add(element2)
session.commit()

element3 = Element(name = "Sugar", price = "$0.45", element = cake1)

session.add(element3)
session.commit()

element4 = Element(name = "cream", price = "$1", element = cake1)

session.add(element4)
session.commit()

element5 = Element(name = "butter", price = "$2", element = cake1)

session.add(element5)
session.commit()

element6 = Element(name = "Eggs", price = "$1", element = cake1)

session.add(element6)
session.commit()

element7 = Element(name = "jam", price = "$0.30", element = cake1)

session.add(element7)
session.commit()

print "added Zaher"
