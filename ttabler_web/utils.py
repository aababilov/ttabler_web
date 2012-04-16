# -*- coding: utf-8 -*-

'''
Created on Apr 15, 2012

@author: alessio
'''

from .database import *
from ttabler_web.html2ttm import TtableHtmlParser


WEEK_LENGTH = 6
MAX_PERIOD = 100


class ResourceDealer(object):
    def __init__(self, default_department):
        self.default_department = default_department

    def load_cts(self):
        self.class_by_id = dict(((obj.id, obj) for obj in Group.query.all()))
        self.teacher_by_id = dict(((obj.id, obj) for obj in Teacher.query.all()))
        self.subject_by_id = dict(((obj.id, obj) for obj in Subject.query.all()))
        
        self.class_by_name = dict(((obj.name, obj.id) for obj in self.class_by_id.itervalues()))
        self.teacher_by_name = dict(((obj.surname, obj.id) for obj in self.teacher_by_id.itervalues()))
        self.subject_by_name = dict(((obj.name, obj.id) for obj in self.subject_by_id.itervalues()))

    def load_buildings(self):
        self.building_by_id = dict(((obj.id, obj.name) for obj in Building.query.all()))
        self.building_by_name = dict(((value, key) for key, value in self.building_by_id.iteritems()))
        
    def load_rooms(self):
        self.load_buildings()
        self.room_by_id = dict((
            (obj.id, "%s %s" % (obj.name, self.building_by_id.get(obj.building_id, None)))
            for obj in Room.query.all()
        ))
        self.room_by_name = dict((
            (value, key)
            for key, value in self.room_by_id.iteritems()
        ))

    def teacher_surname(self, name):
        surname = ""
        for i in name.split():
            if len(i) > len(surname):
                surname = i
        return surname

    def create_subjects(self, name_list):
        for name in name_list:
            if name in self.subject_by_name:
                continue
            obj = Subject(name=name)
            db.session.add(obj)

    def create_teachers(self, name_list):
        for name in name_list:
            surname = self.teacher_surname(name)
            if surname in self.teacher_by_name:
                continue
            obj = Teacher(surname=surname,
                          department_id=self.default_department)
            db.session.add(obj)

    def create_classes(self, name_list):
        for name in name_list:
            if name in self.class_by_name:
                continue
            obj = Group(name=name, department_id=self.default_department)
            db.session.add(obj)
            
    def create_rooms(self, name_list):
        name_pair_list = []
        building_list = set()
        for name in name_list:
            if name in self.room_by_name:
                continue
            name_pair = name.rsplit(" ", 1)
            if len(name_pair) < 2:
                continue
            building_list.add(name_pair[1])
            name_pair_list.append(name_pair)
        
        self.create_buildings(building_list)
        db.session.commit()
        self.load_buildings()
        for name_pair in name_pair_list:
            building_id = self.building_by_name.get(name_pair[1], None)
            if building_id:
                obj = Room(name=name_pair[0],
                           building_id=building_id)
                db.session.add(obj)
    
    def create_buildings(self, name_list):
        for name in name_list:
            if name in self.building_by_name:
                continue
            obj = Building(name=name)
            db.session.add(obj)

    def create_resources(self, resources):
        ctors = {"teacher": self.create_teachers,
                 "class": self.create_classes,
                 "subject": self.create_subjects,
                 "room": self.create_rooms,
                 "building": self.create_buildings}
        for key, value in resources.iteritems():
            ctors[key](value)
                

def curriculum_process(curriculum_id, curriculum_file, default_department, col_nums):
    dealer = ResourceDealer(default_department)
    dealer.load_cts()
    
    rsrc_names = {"teacher": set(), "class": set(), "subject": set()}
    compiled_cclum = []
    for line in curriculum_file:
        cc = line.split("\t")
        compiled_ccunits = {}
        for rsrc in "class", "teacher", "subject":
            if len(cc) > col_nums[rsrc]:
                name = cc[col_nums[rsrc]]
                rsrc_names[rsrc].add(name)
            else:
                name = None
            compiled_ccunits[rsrc] = name

        lk_count = {}
        for lk_id, col_lk in col_nums.iteritems():
            if len(cc) > col_lk:
                lk_count[lk_id] = int(cc[col_lk]),
        compiled_ccunits["count"] = lk_count
        compiled_cclum.append(compiled_ccunits)
    
    dealer.create_resources(rsrc_names)
    db.session.commit()
    dealer.load_cts()
    
    for compiled_ccunits in compiled_cclum:
        common_part = { "curriculum_id": curriculum_id }
        for rsrc in "class", "teacher", "subject":
            common_part[rsrc + "_id"] = getattr(
                dealer, rsrc + "_by_name")[compiled_ccunits[rsrc]]
        
        for lk_id, count in compiled_ccunits["count"].iteritems():
            ccunit = Ccunit(
                lkind_id=lk_id,
                count=count,
                **common_part)
            db.session.add(ccunit)                

    db.session.commit()


class TtableNormalizer(object):
    def __init__(self, ttable_id):
        self.ttable_id = ttable_id
        
    def normalize(self):
        ttable_id = self.ttable_id
        ttable = Ttable.query.filter_by(id=ttable_id).first_or_404()
        ccunit_by_id = {}
        for unit in Ccunit.query.filter_by(curriculum_id=ttable.curriculum_id):
            ccunit_by_id[unit.id] = unit
        ttunit_by_ccunit_id = dict(((id, []) for id in ccunit_by_id.iterkeys()))
        for unit in Ttunit.query.filter_by(ttable_id=ttable_id):
            ttunit_by_ccunit_id.setdefault(unit.ccunit_id, []).append(unit)
        for ccunit_id, ttunit_list in ttunit_by_ccunit_id.iteritems():
            try:
                ccunit = ccunit_by_id[ccunit_id]
                count = ccunit.count 
            except KeyError:
                count = 0
            
            extra_units = len(ttunit_list) - count
            if extra_units > 0:
                ttunit_list.sort(key=lambda unit: (unit.room_id, unit.time))                
                for unit in ttunit_list[:extra_units]:
                    db.session.remove(unit)
                db.session.commit()
                ttunit_list[:] = ttunit_list[extra_units:]
                continue
            while extra_units < 0:
                ttunit = Ttunit(ttable_id=ttable_id,
                                ccunit_id=ccunit_id,
                                room_id=None, time=0)
                db.session.add(ttunit)
                ttunit_list.append(ttunit)
                extra_units += 1
        db.session.commit()
        ttunit_by_ccunit_id = dict(
            ((key, value)
             for key, value in ttunit_by_ccunit_id.iteritems()
             if key in ccunit_by_id))
        ttunit_by_id = {}
        for ttunit_list in ttunit_by_ccunit_id.itervalues():
            for unit in ttunit_list:
                ttunit_by_id[unit.id] = unit
                
        self.ttunit_by_id = ttunit_by_id
        self.ccunit_by_id = ccunit_by_id
        self.ttunit_by_ccunit_id = ttunit_by_ccunit_id
        self.ttable = ttable
        self.curriculum_id = ttable.curriculum_id



def ttable_process(ttable_id, ttable_file):
    rsrc_dealer = ResourceDealer(default_department=None)
    rsrc_dealer.load_cts()
    rsrc_dealer.load_rooms()
    ttbl_norm = TtableNormalizer(ttable_id)
    ttbl_norm.normalize()
    #curriculum = {(subject, group): teacher}
    curriculum = {}
    faculty_by_id = dict(( (obj.id, obj) for obj in Faculty.query.all() ))
    faculty_name_by_dep_id = dict((
        (obj.id, faculty_by_id.get(obj.faculty_id, ""))
        for obj in Department.query.all()
    ))
    for unit in ttbl_norm.ccunit_by_id.itervalues():
        if unit.class_id and unit.teacher_id and unit.subject_id:
            curriculum[(rsrc_dealer.subject_by_id[unit.subject_id].name,
                        rsrc_dealer.class_by_id[unit.class_id].name)] = (
                        rsrc_dealer.teacher_by_id[unit.teacher_id].surname)

    ignore_time = [u"лаб", u"NO_ROOM", u"каф", u"каф. нарк"]
    html_parser = TtableHtmlParser(WEEK_LENGTH, curriculum, ignore_time)

    html_parser.process_file(unicode(ttable_file.read(), "utf-8"))
    html_parser.accumulate_events()

    rsrc_dealer.create_rooms(html_parser.resources["room"])
    db.session.commit()
    rsrc_dealer.load_rooms()
    
    ccunit_by_subid = dict((
        ((unit.subject_id, unit.teacher_id, unit.class_id), unit)
        for unit in ttbl_norm.ccunit_by_id.itervalues()
    ))
    ttunit_by_ccunit_id = ttbl_norm.ttunit_by_ccunit_id
    for (sub, tea, cla, roo, day, per) in html_parser.events:
        try:
            ccunit = ccunit_by_subid[(rsrc_dealer.subject_by_name[sub],
                                      rsrc_dealer.teacher_by_name[tea],
                                      rsrc_dealer.class_by_name[cla])]
        except KeyError as ex:
            print str(ex)
            continue
        ttunit_list = ttunit_by_ccunit_id[ccunit.id]
        room_id = rsrc_dealer.room_by_name.get(roo, None)
        day_per = day * MAX_PERIOD + per
        best_eq = -1
        best_ttunit = None
        for ttunit in ttunit_list:
            eq = 0
            if ttunit.room_id == room_id:
                eq += 2
            if ttunit.day_per == day_per:
                eq += 1
            if eq > best_eq:
                best_ttunit = ttunit
        if best_eq != 3 and best_ttunit:
            best_ttunit.room_id = room_id
            best_ttunit.day_per = day_per
            db.session.merge(best_ttunit)
    
    db.session.commit()
