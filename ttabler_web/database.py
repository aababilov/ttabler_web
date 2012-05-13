# -*- coding: utf-8 -*-

from flask import Flask
from flaskext.sqlalchemy import SQLAlchemy

from . import app
from sqlalchemy.orm.attributes import QueryableAttribute


db = SQLAlchemy(app)


class BaseEntity:
    @classmethod
    def ensure_fields(cls):
        if hasattr(cls, "fields"):
            return
        fields = []
        for key, value in cls.__dict__.iteritems():
            if isinstance(value, QueryableAttribute):
                fields.append(key)
        cls.fields = fields

    def __init__(self, **obj_json):
        self.ensure_fields()
        self.update(obj_json, prohibit=set())
        
    def update(self, obj_json, prohibit=set(("id", "rtype"))):
        for field in (set(self.fields) & set(obj_json.iterkeys())
                      - prohibit):
            setattr(self, field, obj_json[field])

    def to_json(self):
        self.ensure_fields()
        json = {}
        for field in self.fields:
            json[field] = getattr(self, field)
        return json


class Resource(BaseEntity, db.Model):
    __tablename__ = "resource"
    id = db.Column(db.Integer, primary_key=True)
    rtype = db.Column(db.String(8))
    
    def __init__(self, *args, **kwargs):
        super(Resource, self).__init__(*args, **kwargs)
        self.rtype = self.__class__.__name__


class Faculty(BaseEntity, db.Model):
    __tablename__ = "faculty"
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.Unicode(255), unique=True)
    abbrev = db.Column(db.Unicode(255), unique=True)


class Department(BaseEntity, db.Model):
    __tablename__ = "department"
    id = db.Column(db.Integer, primary_key=True)
    faculty_id = db.Column(db.Integer, nullable=False)
    name = db.Column(db.Unicode(255), unique=True)


class Teacher(Resource):
    __tablename__ = "teacher"
    id = db.Column(db.Integer, db.ForeignKey('resource.id'), primary_key=True)
    department_id = db.Column(db.Integer, nullable=False)
    name = db.Column(db.Unicode(255))
    surname = db.Column(db.Unicode(255))
    patronyme = db.Column(db.Unicode(255))


class Group(Resource):
    __tablename__ = "group"
    id = db.Column(db.Integer, db.ForeignKey('resource.id'), primary_key=True)
    department_id = db.Column(db.Integer, nullable=False)
    name = db.Column(db.Unicode(255))
    size = db.Column(db.Integer)


class Stream(Resource):
    __tablename__ = "stream"
    id = db.Column(db.Integer, db.ForeignKey('resource.id'), primary_key=True)
    name = db.Column(db.Unicode(255))


class Building(BaseEntity, db.Model):
    __tablename__ = "building"
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.Unicode(255))
    bld_group = db.Column(db.Integer)


class Room(Resource):
    __tablename__ = "room"
    id = db.Column(db.Integer, db.ForeignKey('resource.id'), primary_key=True)
    building_id = db.Column(db.Integer, nullable=False)
    name = db.Column(db.Unicode(255))
    size = db.Column(db.Integer)


class Subject(BaseEntity, db.Model):
    __tablename__ = "subject"
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.Unicode(255))


class Lkind(BaseEntity, db.Model):
    __tablename__ = "lkind"
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.Unicode(255))
    abbrev = db.Column(db.Unicode(255))


class Capability(BaseEntity, db.Model):
    __tablename__ = "capability"
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.Unicode(255))


class Curriculum(BaseEntity, db.Model):
    __tablename__ = "curriculum"
    id = db.Column(db.Integer, primary_key=True)
    number = db.Column(db.Integer)
    year = db.Column(db.Integer)
    comment = db.Column(db.Unicode(255))
    max_per_teacher = db.Column(db.Integer)
    max_per_student = db.Column(db.Integer)
    desires = db.Column(db.Text)

    
class Ccunit(BaseEntity, db.Model):
    __tablename__ = "ccunit"
    id = db.Column(db.Integer, primary_key=True)
    curriculum_id = db.Column(db.Integer, nullable=False)
    
    lkind_id = db.Column(db.Integer)
    class_id = db.Column(db.Integer)
    teacher_id = db.Column(db.Integer)
    subject_id = db.Column(db.Integer)
    
    count = db.Column(db.Integer)
    block_size = db.Column(db.Integer)
    prefer_day = db.Column(db.Integer)
    prefer_period = db.Column(db.Integer)
    prefer_room_id = db.Column(db.Integer)


class Ttable(BaseEntity, db.Model):
    __tablename__ = "ttable"
    id = db.Column(db.Integer, primary_key=True)
    curriculum_id = db.Column(db.Integer, nullable=False)
    comment = db.Column(db.Unicode(255))


class Ttunit(BaseEntity, db.Model):
    __tablename__ = "ttunit"
    id = db.Column(db.Integer, primary_key=True)
    ttable_id = db.Column(db.Integer, nullable=False)
    ccunit_id = db.Column(db.Integer, nullable=False)
    room_id = db.Column(db.Integer)
    day_per = db.Column(db.Integer)


class Period(BaseEntity, db.Model):
    __tablename__ = "period"
    id = db.Column(db.Integer, primary_key=True)
    hours = db.Column(db.Integer, nullable=False)
    minutes = db.Column(db.Integer, nullable=False)


db.create_all()
