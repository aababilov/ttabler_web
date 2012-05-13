# -*- coding: utf-8 -*-

'''
Created on Mar 18, 2012

@author: alessio
'''

import logging
import os
import cStringIO
import json

from flask import Flask, request, session, g, redirect, url_for, \
     abort, render_template, flash, Response
from werkzeug.exceptions import BadRequest, Unauthorized, NotFound

from . import app
from .database import *
from sqlalchemy.exc import *
from . import utils
from ttabler_web.utils import ResourceDealer


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
    obj = PersistentClass(**obj_json)
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
    obj = PersistentClass.query.filter_by(id=id).first()
    if not obj:
        return Response("Object with id=%d is not found\n" % id, status=404)
    obj_json = request.json
    obj.update(obj_json)
    db.session.merge(obj)
    db.session.commit()
    return to_json_response(obj.to_json())


def ajax_persistent_delete(PersistentClass, id):
    obj = PersistentClass.query.filter_by(id=id).first()
    if not obj:
        return Response("Object with id=%d is not found\n" % id, status=404)
    obj.delete_children()
    db.session.delete(obj)
    db.session.commit()
    return Response("Object with id=%d is deleted\n" % id, status=200)


def add_ajax_rules():
    simple_classes = (
        Faculty, Department, Group, Stream, Teacher,
        Building, Room, Capability,
        Subject, Lkind,
        Curriculum, Ccunit,
        Ttable, Ttunit,
        Period)
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


@app.route('/api/period', methods=['GET'])
def ajax_period_get():
    values = []
    query = Period.query.order_by(Period.id)
    for obj in query.all():
        values.append(obj.to_json())
    
    return to_json_response({"values": values})


@app.route('/period', methods=['GET'])
def page_period():
    return render_template("tables/period.html")


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
        return BadRequest(description="curriculum_id must be specified")
    return ajax_persistent_get(Ccunit, **filter_by)


def ccunit_combos():
    dealer = ResourceDealer(None)
    dealer.load_cts()
    return {
            "teacher": dealer.teacher_id2ttl,
            "subject": dict(((obj.id, obj.name)
                             for obj in dealer.subject_by_id.itervalues())),
            "lkind": dict(((obj.id, obj.abbrev) for obj in Lkind.query.all())),
            "class": dealer.class_id2ttl,
    }

    
@app.route('/ccunit', methods=['GET'])
def page_ccunit():
    try:
        curriculum_id = request.args["curriculum_id"]
    except:
        return Response("Not found", status=404)
    lkinds = [(lk.id, lk.abbrev) for lk in Lkind.query.all()]
    department_list = [(dep.id, dep.name) for dep in Department.query.all()]

    return render_template(
        "tables/ccunit.html",        
        curriculum_id=curriculum_id,
        col_options=zip(xrange(0, 10), xrange(1, 10)),
        lkinds=lkinds,
        department_list=department_list,
        combos=ccunit_combos())


@app.route('/curriculum_upload', methods=['POST'])
def curriculum_upload():
    curriculum_id = request.form["curriculum_id"]
    curriculum_file = request.files["curriculum_file"]

    default_department = int(request.form["default_department"])
    
    utils.curriculum_import(curriculum_id, curriculum_file,
                            default_department, request.form)
    
    return redirect("%s?curriculum_id=%s" % (url_for("page_ccunit"), curriculum_id))
    

@app.route('/api/ttable', methods=['GET'])
def ajax_ttable_get():
    filter_by = {}
    try:
        filter_by["curriculum_id"] = request.args["curriculum_id"]
    except KeyError:
        pass
    return ajax_persistent_get(Ttable, **filter_by)


@app.route('/ttable', methods=['GET'])
def page_ttable():
    try:
        curriculum_id = request.args["curriculum_id"]
    except:
        return Response("Not found", status=404)
    return render_template("tables/ttable.html", curriculum_id=curriculum_id)


@app.route('/api/ttunit', methods=['GET'])
def ajax_ttunit_get():
    filter_by = {}
    try:
        filter_by["ttable_id"] = request.args["ttable_id"]
    except KeyError:
        return BadRequest(description="ttable_id must be specified")
    return ajax_persistent_get(Ttunit, **filter_by)


@app.route('/ttunit', methods=['GET'])
def page_ttunit():
    try:
        ttable_id = request.args["ttable_id"]
    except:
        return Response("Not found", status=404)
    ttable = Ttable.query.filter_by(id=ttable_id).first_or_404()
    combos = ccunit_combos()
    dealer = utils.ResourceDealer(None)
    dealer.load_rooms()
    day_count = len(utils.DAY_NAMES)
    combos["day"] = dict((
        (i, unicode("%s-%d" % 
            (utils.DAY_NAMES[i % day_count], i / day_count + 1),
            "utf-8"))
        for i in xrange(2 * day_count)))
    combos["room"] = dealer.room_id2ttl
    combos["period"] = dict(((obj.id, "%s:%02s" % (obj.hours, obj.minutes))
                             for obj in Period.query))
    return render_template("tables/ttunit.html",
                           ttable_id=ttable_id,
                           curriculum_id=ttable.curriculum_id,
                           max_period=utils.MAX_PERIOD,
                           combos=combos)


@app.route('/ttable_upload', methods=['POST'])
def ttable_upload():
    ttable_id = request.form["ttable_id"]
    ttable_file = request.files["ttable_file"]

    utils.ttable_import(ttable_id, ttable_file)
    return redirect("%s?ttable_id=%s" % (url_for("page_ttunit"), ttable_id))


@app.route('/api/ttable_report')
def ttable_report():
    out_file = cStringIO.StringIO()
    utils.ttable_report(
        out_file,
        request.args["ttable_id"],
        request.args["rtype"],
        [int(i) for i in request.args["ids"].split(",")])
    ret = out_file.getvalue()
    out_file.close()
    return Response(ret)


@app.route('/api/ttm')
def export_ttm():
    out_file = cStringIO.StringIO()
    curriculum_id = request.args.get("curriculum_id", None)
    ttable_id = request.args.get("ttable_id", None)
    utils.export_ttm(out_file, curriculum_id, ttable_id)
    ret = out_file.getvalue()
    out_file.close()
    return Response(ret, headers={
        "Content-Type": "application/xml",
        "Content-Disposition": "attachment; filename=%s.xml" % 
          (("timetable-%s" % ttable_id) if ttable_id else
           "curriculum-%s" % curriculum_id)
    })


@app.route("/api/ttm/interrupt", methods=["POST"])
def ttm_interrupt():
    utils.ttm_interrupt()
    return Response("ok")

@app.route('/ttable_progress')
def page_ttable_progress():
    return render_template("tables/ttable_progress.html")


@app.route('/api/ttable_progress')
def ajax_get_ttable_progress():
    return to_json_response(utils.get_ttable_progress())


@app.route('/api/build_ttable')
def build_ttable():
    curriculum_id = request.args.get("curriculum_id", None)
    ttable_id = request.args.get("ttable_id", None)
    utils.build_ttable(curriculum_id, ttable_id)
    return redirect(url_for("page_ttable_progress"))


@app.route('/', methods=['GET'])
def wizard_handler():
    session.clear()
    return redirect(url_for('page_faculty'))

