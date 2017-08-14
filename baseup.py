from sqlalchemy import Column, ForeignKey, Integer, String
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from sqlalchemy import create_engine

Base = declarative_base()


class User(Base):
    __tablename__ = 'user'

    id = Column(Integer, primary_key=True)
    name = Column(String(250), nullable=False)
    email = Column(String(250), nullable=False)
    picture = Column(String(250))


class Cake(Base):
    __tablename__ = 'cake'

    id = Column(Integer, primary_key=True)
    name = Column(String(250), nullable=False)
    description = Column(String(250))
    course = Column(String(250))
    user_id = Column(Integer, ForeignKey('user.id'))
    user = relationship(User)

    @property
    def serialize(self):
        """Return object data in easily serializeable format"""
        return {
            'name': self.name,
            'id': self.id,
            'description': self.description,
            'course': self.course,
        }


class Element(Base):
    __tablename__ = 'elements'

    name = Column(String(80), nullable=False)
    id = Column(Integer, primary_key=True)
    price = Column(String(8))
    element_id = Column(Integer, ForeignKey('cake.id'))
    element = relationship(Cake)
    user_id = Column(Integer, ForeignKey('user.id'))
    user = relationship(User)

    @property
    def serialize(self):
        """Return object data in easily serializeable format"""
        return {
            'name': self.name,
            'id': self.id,
            'price': self.price,
            }


engine = create_engine('sqlite:///cakeswithusers.db')


Base.metadata.create_all(engine)
