from flask import Flask
from flaskext.sqlalchemy import SQLAlchemy

from . import app
from sqlalchemy.orm.attributes import QueryableAttribute

app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:////tmp/test.db'
db = SQLAlchemy(app)


class BaseEntity:
    @classmethod
    def ensure_fields(cls):
        print cls.__dict__
        if hasattr(cls, "fields"):
            return
        fields = []
        for key, value in cls.__dict__.iteritems():
            if isinstance(value, QueryableAttribute):
                fields.append(key)
        cls.fields = fields

    def __init__(self, obj_json):
        self.ensure_fields()
        for field in self.fields:
            if field in obj_json:
                setattr(self, field, obj_json[field])

    def to_json(self):
        self.ensure_fields()
        json = {}
        for field in self.fields:
            json[field] = getattr(self, field)
        return json


class Faculty(BaseEntity, db.Model):
    __tablename__ = "faculty"
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(255), unique=True)
    abbrev = db.Column(db.String(255), unique=True)


class Department(BaseEntity, db.Model):
    __tablename__ = "department"
    id = db.Column(db.Integer, primary_key=True)
    faculty_id = db.Column(db.Integer, nullable=False)
    name = db.Column(db.String(255), unique=True)


db.create_all()
