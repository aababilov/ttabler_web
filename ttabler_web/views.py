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
    db.session.merge(obj)
    db.session.commit()
    return to_json_response(obj.to_json())


def ajax_persistent_delete(PersistentClass, id):
    i = PersistentClass.query.filter_by(id=id).delete()
    if i < 1:
        return Response("Object with id=%d is not found\n" % id, status=404)
    db.session.commit()
    return Response("Object with id=%d is deleted\n" % id, status=200)


def add_ajax_rules():
    simple_classes = (
        Faculty, Department, Group, Teacher,
        Building, Room, Capability,
        Subject, Lkind,
        Curriculum, Ccunit)
    for cls in simple_classes:
        cls_name = cls.__tablename__
        app.add_url_rule("/api/%s/<int:id>" % cls_name, 
                         "ajax_%s_update" % cls_name,                      
                         lambda id, cls=cls: ajax_persistent_update(cls, id),
                         methods=["PUT"])
        app.add_url_rule("/api/%s/<int:id>" % cls_name,
                         "ajax_%s_delete" % cls_name,
                         lambda id, cls=cls: ajax_persistent_delete(cls, id),
                         methods=['DELETE'])
        app.add_url_rule("/api/%s" % cls_name,
                         "ajax_%s_create" % cls_name,
                         lambda cls=cls: ajax_persistent_create(cls),
                         methods=['POST'])

add_ajax_rules()

@app.route('/api/faculty', methods=['GET'])
def ajax_faculty_get():
    return ajax_persistent_get(Faculty)


@app.route('/faculty', methods=['GET'])
def page_faculty():
    return render_template("tables/faculty.html")


@app.route('/api/department', methods=['GET'])
def ajax_department_get():
    filter_by = {}
    try:
        filter_by["faculty_id"] = request.args["faculty_id"]
    except KeyError:
        pass
    return ajax_persistent_get(Department, **filter_by)


@app.route('/department', methods=['GET'])
def page_department():
    try:
        faculty_id = request.args["faculty_id"]
    except:
        return Response("Not found", status=404)
    return render_template("tables/department.html", faculty_id=faculty_id)


@app.route('/api/group', methods=['GET'])
def ajax_group_get():
    filter_by = {}
    try:
        filter_by["department_id"] = request.args["department_id"]
    except KeyError:
        pass
    return ajax_persistent_get(Group, **filter_by)


@app.route('/group', methods=['GET'])
def page_group():
    try:
        department_id = request.args["department_id"]
    except:
        return Response("Not found", status=404)
    return render_template("tables/group.html", department_id=department_id)


@app.route('/api/teacher', methods=['GET'])
def ajax_teacher_get():
    filter_by = {}
    try:
        filter_by["department_id"] = request.args["department_id"]
    except KeyError:
        pass
    return ajax_persistent_get(Teacher, **filter_by)


@app.route('/teacher', methods=['GET'])
def page_teacher():
    try:
        department_id = request.args["department_id"]
    except:
        return Response("Not found", status=404)
    return render_template("tables/teacher.html", department_id=department_id)


@app.route('/api/building', methods=['GET'])
def ajax_building_get():
    return ajax_persistent_get(Building)


@app.route('/building', methods=['GET'])
def page_building():
    return render_template("tables/building.html")


@app.route('/api/room', methods=['GET'])
def ajax_room_get():
    filter_by = {}
    try:
        filter_by["building_id"] = request.args["building_id"]
    except KeyError:
        pass
    return ajax_persistent_get(Room, **filter_by)


@app.route('/room', methods=['GET'])
def page_room():
    try:
        building_id = request.args["building_id"]
    except:
        return Response("Not found", status=404)
    return render_template("tables/room.html", building_id=building_id)


@app.route('/api/capability', methods=['GET'])
def ajax_capability_get():
    return ajax_persistent_get(Capability)


@app.route('/capability', methods=['GET'])
def page_capability():
    return render_template("tables/capability.html")


@app.route('/api/subject', methods=['GET'])
def ajax_subject_get():
    return ajax_persistent_get(Subject)


@app.route('/subject', methods=['GET'])
def page_subject():
    return render_template("tables/subject.html")


@app.route('/api/lkind', methods=['GET'])
def ajax_lkind_get():
    return ajax_persistent_get(Lkind)


@app.route('/lkind', methods=['GET'])
def page_lkind():
    return render_template("tables/lkind.html")


@app.route('/api/curriculum', methods=['GET'])
def ajax_curriculum_get():
    return ajax_persistent_get(Curriculum)


@app.route('/curriculum', methods=['GET'])
def page_curriculum():
    return render_template("tables/curriculum.html")


@app.route('/api/ccunit', methods=['GET'])
def ajax_ccunit_get():
    filter_by = {}
    try:
        filter_by["curriculum_id"] = request.args["curriculum_id"]
    except KeyError:
        pass
    return ajax_persistent_get(Ccunit, **filter_by)


def map_by_lambda(cls, lam=lambda obj: obj.name):
    map = {}
    query = cls.query
    for obj in query.all():
        map[obj.id] = lam(obj) 
    return map


@app.route('/ccunit', methods=['GET'])
def page_ccunit():
    try:
        curriculum_id = request.args["curriculum_id"]
    except:
        return Response("Not found", status=404)
    return render_template(
        "tables/ccunit.html", curriculum_id=curriculum_id,
        combos={
            "teacher": map_by_lambda(
                Teacher, 
                lambda obj: "%s %s %s" % (
                    obj.surname, obj.name, obj.patronyme)),
            "subject": map_by_lambda(Subject),
            "lkind": map_by_lambda(Lkind, lambda obj: obj.abbrev),
            "class": map_by_lambda(Group, lambda obj: obj.name)})


@app.route('/', methods=['GET'])
def wizard_handler():
    session.clear()
    return redirect(url_for('page_faculty'))
