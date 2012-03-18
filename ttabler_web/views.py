'''
Created on Mar 18, 2012

@author: alessio
'''

import logging
import os

import json

from flask import Flask, request, session, g, redirect, url_for, \
     abort, render_template, flash, Response

from . import app
from .database import *
from sqlalchemy.exc import *

def to_json_response(obj):
    return Response(json.dumps(obj) + "\n", 
                    mimetype="application/json", 
                    headers={"Pragma": "no-cache", "Expires": "0"})


def ajax_persistent_get(PersistentClass, **filter_by):
    values = []
    query = PersistentClass.query
    if filter_by:
        query = query.filter_by(**filter_by)
    for obj in query.all():
        values.append(obj.to_json())
    return to_json_response({"values": values})


def ajax_persistent_create(PersistentClass):
    obj_json = request.json
    obj = PersistentClass(obj_json)
    db.session.add(obj)
    try:
        db.session.commit()
    except IntegrityError as intErr:
        print intErr
        return Response("Integrity error\n", status=400)
    except Exception as ex:
        return Response("Exception: %s\n" % ex, status=400)
    return to_json_response(obj.to_json())


def ajax_persistent_update(PersistentClass, id):
    if PersistentClass.query.filter_by(id=id).count() == 0:
        return Response("Object with id=%d is not found\n" % id, status=404)
    obj_json = request.json
    obj = PersistentClass(obj_json)
    obj.id = id
    print db.session.__dict__
    db.session.merge(obj)
    db.session.commit()
    return to_json_response(obj.to_json())


def ajax_persistent_delete(PersistentClass, id):
    i = PersistentClass.query.filter_by(id=id).delete()
    if i < 1:
        return Response("Object with id=%d is not found\n" % id, status=404)
    db.session.commit()
    return Response("Object with id=%d is deleted\n" % id, status=200)


@app.route('/api/faculty', methods=['GET'])
def ajax_faculty_get():
    return ajax_persistent_get(Faculty)


@app.route('/api/faculty', methods=['POST'])
def ajax_faculty_create():
    return ajax_persistent_create(Faculty)


@app.route('/api/faculty/<int:id>', methods=['PUT'])
def ajax_faculty_update(id):
    return ajax_persistent_update(Faculty, id)


@app.route('/api/faculty/<int:id>', methods=['DELETE'])
def ajax_faculty_delete(id):
    return ajax_persistent_delete(Faculty, id)


@app.route('/faculty', methods=['GET'])
def page_faculty():
    return render_template("tables/faculty.html")


@app.route('/api/department', methods=['GET'])
def ajax_department_get():
    filter_by = {}
    try:
        filter_by["faculty_id"] = request.args["faculty_id"]
    except:
        pass
    return ajax_persistent_get(Department, **filter_by)


@app.route('/api/department', methods=['POST'])
def ajax_department_create():
    return ajax_persistent_create(Department)


@app.route('/api/department/<int:id>', methods=['PUT'])
def ajax_department_update(id):
    return ajax_persistent_update(Department, id)


@app.route('/api/department/<int:id>', methods=['DELETE'])
def ajax_department_delete(id):
    return ajax_persistent_delete(Department, id)


@app.route('/department', methods=['GET'])
def page_department():
    try:
        faculty_id = request.args["faculty_id"]
    except:
        return Response("Not found", status=404)
    return render_template("tables/department.html", faculty_id=faculty_id)


@app.route('/', methods=['GET'])
def wizard_handler():
    session.clear()
    return redirect(url_for('page_faculty'))
