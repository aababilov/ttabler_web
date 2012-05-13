# -*- coding: utf-8 -*-

'''
Created on Apr 15, 2012

@author: alessio
'''

import os
import signal
import subprocess
from datetime import datetime
import json

from .database import *
from ttabler_web.html2ttm import TtableHtmlParser, TtmPrinter
from ttabler_web.ttm2html import HtmlPrinter, TtmParser


WEEK_LENGTH = 6
MAX_PERIOD = 100
IGNORE_TIME = [u"лаб", u"NO_ROOM", u"каф", u"каф. нарк"]
DAY_NAMES = ["Пн", "Вт", "Ср", "Чт", "Пт", "Сб"]
WORKING_DIR = "/var/lib/ttabler-web"
CONFIG_DIR = "/etc/ttabler-web"
TEACHER_POST = [u"доц.", u"св.", u"асс.", u"ас.", u"проф."]


class ResourceDealer(object):
    def __init__(self, default_department):
        self.default_department = default_department

    def load_cts(self):
        """
        Load classes, teachers, and subjects
        """
        faculty_abbrev_by_id = dict(( (obj.id, obj.abbrev) for obj in Faculty.query.all() ))
        faculty_abbrev_by_dep_id = dict((
            (obj.id, faculty_abbrev_by_id.get(obj.faculty_id, ""))
            for obj in Department.query.all()
        ))
        self.faculty_abbrev_by_dep_id = faculty_abbrev_by_dep_id
        self.dep_id_by_faculty_abbrev = dict((
            (v, k)
            for k, v in self.faculty_abbrev_by_dep_id.iteritems() 
        ))

        self.teacher_by_id = dict(((obj.id, obj) for obj in Teacher.query.all()))
        self.subject_by_id = dict(((obj.id, obj) for obj in Subject.query.all()))

        # FIXME: beautiful titles
        self.class_id2ttl = dict((
            (obj.id, u"%s-%s" % (faculty_abbrev_by_dep_id.get(
                 obj.department_id, "??"), obj.name))
            for obj in Group.query.all()
        ))
        self.class_id2ttl.update(dict((
            (obj.id, obj.name)
            for obj in Stream.query.all()
        )))
        self.teacher_id2ttl = dict(((obj.id, obj.surname) for obj in self.teacher_by_id.itervalues()))
        
        self.class_by_name = dict(((v, k) for k, v in self.class_id2ttl.iteritems()))
        self.teacher_by_name = dict(((obj.surname, obj.id) for obj in self.teacher_by_id.itervalues()))
        self.subject_by_name = dict(((obj.name, obj.id) for obj in self.subject_by_id.itervalues()))

    def load_buildings(self):
        self.building_by_id = dict(((obj.id, obj) for obj in Building.query.all()))
        self.building_by_name = dict(((obj.name, obj) for obj in self.building_by_id.itervalues()))
        
    def load_rooms(self):
        self.load_buildings()
        self.room_by_id = dict(((obj.id, obj) for obj in Room.query.all()))
        room_id2ttl = {}
        for obj in self.room_by_id.itervalues():
            try:
                room_id2ttl[obj.id] = "%s %s" % (obj.name,
                    self.building_by_id[obj.building_id].name)
            except KeyError:
                pass
        self.room_id2ttl = room_id2ttl
        self.room_ttl2id = dict((
            (value, key)
            for key, value in self.room_id2ttl.iteritems()
        ))

    @staticmethod
    def teacher_surname(name):
        spl = name.split()
        if spl[0] in TEACHER_POST:
            return spl[1]
        elif spl[0] == u"teacher":
            return name
        return spl[0]

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
        tail_list = set()
        print "dep ", self.dep_id_by_faculty_abbrev
        for name in name_list:
            if name in self.class_by_name:
                continue
            spl = name.split(",")
            if len(spl) > 1:
                tail_list |= set(spl)
                obj = Stream(name=name)
            else:
                spl = name.split("-", 1)
                obj = Group(name=name if len(spl) <= 1 else spl[1],
                            department_id=self.default_department)
            db.session.add(obj)
        print tail_list
        if tail_list:
            self.create_classes(tail_list)

    def create_rooms(self, name_list):
        name_pair_list = []
        building_list = set()
        for name in name_list:
            if name in self.room_ttl2id:
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
            try:
                building_id = self.building_by_name[name_pair[1]].id
            except KeyError:
                pass
            else:
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


def curriculum_import(curriculum_id, curriculum_file, default_department, form):
    dealer = ResourceDealer(default_department)
    dealer.load_cts()

    compiled_cclum = []
    file_content = curriculum_file.read()
    lkinds = [lk.id for lk in Lkind.query.all()]
    if "<ttm" in file_content:
        parser = TtmParser()
        parser.parseString(file_content)
        iter_events = list(parser.iter_events())
        rsrc_names = {
            "class": set((ev["class"] for ev in iter_events)),
            "teacher": set((ResourceDealer.teacher_surname(ev["teacher"])
                            for ev in iter_events)),
            "subject": set((ev["subject"] for ev in iter_events)),
        }
        counts = {}
        for ev in iter_events:
            key = (ResourceDealer.teacher_surname(ev["teacher"]),
                   ev["class"], ev["subject"])
            counts[key] = counts.get(key, 0) + 1
        for key, count in counts.iteritems():
            compiled_cclum.append({
                "teacher": key[0],
                "class": key[1],
                "subject": key[2],
                "count": {lkinds[0]: count},
            })
    else:
        col_nums = {}
        for rsrc in "class", "teacher", "subject":
            col_nums[rsrc] = int(form["col_" + rsrc])
        for lk in lkinds:
            try:
                col_nums[lk] = int(form["col_lkind_%s" % lk])
            except (KeyError, ValueError):
                pass

        rsrc_names = {"teacher": set(), "class": set(), "subject": set()}
        for line in file_content.split("\n"):
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


class TtableDealer(object):

    def load_curriculum(self, curriculum_id):
        ccunit_by_id = {}
        for unit in Ccunit.query.filter_by(curriculum_id=curriculum_id):
            ccunit_by_id[unit.id] = unit
        self.ccunit_by_id = ccunit_by_id
        self.curriculum_id = curriculum_id
 
    def load_ttable(self, ttable_id):
        ttable = Ttable.query.filter_by(id=ttable_id).first_or_404()
        self.ttable = ttable
        self.ttable_id = ttable_id
        self.load_curriculum(ttable.curriculum_id)
 
    def normalize(self, ttable_id):
        self.load_ttable(ttable_id)
        ccunit_by_id = self.ccunit_by_id
        ttunit_by_ccunit_id = dict(((i, []) for i in ccunit_by_id.iterkeys()))
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
                ttunit_list.sort(key=lambda unit: (unit.room_id, unit.day_per))                
                for unit in ttunit_list[:extra_units]:
                    db.session.delete(unit)
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
        self.ttunit_by_ccunit_id = ttunit_by_ccunit_id
        
    def iter_ttable_events(self, ttable_id, rsrc_dealer):
        self.load_ttable(ttable_id)
        ccunit_by_id = self.ccunit_by_id
        for ttunit in Ttunit.query.filter_by(ttable_id=ttable_id):
            try:
                ccunit = ccunit_by_id[ttunit.ccunit_id]
            except:
                continue
            day_per = ttunit.day_per or 0
            yield {
                "room": rsrc_dealer.room_id2ttl.get(ttunit.room_id, ""),
                "time": (day_per / MAX_PERIOD,
                         day_per % MAX_PERIOD),
                "class": rsrc_dealer.class_id2ttl[ccunit.class_id],
                "teacher": rsrc_dealer.teacher_id2ttl[ccunit.teacher_id],
                "subject": rsrc_dealer.subject_by_id[ccunit.subject_id].name,
            }

    def iter_curriculum_events(self, curriculum_id, rsrc_dealer):
        self.curriculum_id = curriculum_id
        for ccunit in Ccunit.query.filter_by(curriculum_id=curriculum_id):
            for i in xrange(ccunit.count):
                yield {
                    "class": rsrc_dealer.class_id2ttl[ccunit.class_id],
                    "teacher": rsrc_dealer.teacher_id2ttl[ccunit.teacher_id],
                    "subject": rsrc_dealer.subject_by_id[ccunit.subject_id].name,
                }


def ttable_import(ttable_id, ttable_file):
    rsrc_dealer = ResourceDealer(default_department=None)
    rsrc_dealer.load_cts()
    rsrc_dealer.load_rooms()
    ttbl_dealer = TtableDealer()
    ttbl_dealer.normalize(ttable_id)
    #curriculum = {(subject, group): teacher}
    curriculum = {}
    for unit in ttbl_dealer.ccunit_by_id.itervalues():
        if unit.class_id and unit.teacher_id and unit.subject_id:
            curriculum[(rsrc_dealer.subject_by_id[unit.subject_id].name,
                        rsrc_dealer.class_id2ttl[unit.class_id])] = (
                        rsrc_dealer.teacher_by_id[unit.teacher_id].surname)

    file_content = ttable_file.read()
    if "<html" in file_content:
        parser = TtableHtmlParser(WEEK_LENGTH, curriculum, IGNORE_TIME)
        parser.process_file(unicode(file_content, "utf-8"))
        parser.accumulate_events()
        rsrc_dealer.create_rooms(parser.resources["room"])
        iter_events = parser.events
    else:
        parser = TtmParser()
        parser.parseString(file_content)
        iter_events = list(parser.iter_events())
        rsrc_dealer.create_rooms(set((ev["room"] for ev in iter_events)))

    db.session.commit()
    rsrc_dealer.load_rooms()
    
    ccunit_by_chldid = dict((
        ((unit.subject_id, unit.teacher_id, unit.class_id), unit)
        for unit in ttbl_dealer.ccunit_by_id.itervalues()
    ))
    ttunit_by_ccunit_id = ttbl_dealer.ttunit_by_ccunit_id
    stored = set()
    for event in iter_events:
        try:
            ccunit = ccunit_by_chldid[(
                rsrc_dealer.subject_by_name[event["subject"]],
                rsrc_dealer.teacher_by_name[ResourceDealer.teacher_surname(event["teacher"])],
                rsrc_dealer.class_by_name[event["class"]])]
        except KeyError as ex:
            print "cannot find key %s " % ex
            continue
        ttunit_list = ttunit_by_ccunit_id[ccunit.id]
        room_id = rsrc_dealer.room_ttl2id.get(event["room"], None)
        (day, per) = event["time"]
        day_per = day * MAX_PERIOD + per
        free_ttunit = None
        for ttunit in ttunit_list:
            if ttunit.id in stored:
                continue
            free_ttunit = ttunit
            if ttunit.day_per == day_per:
                break
        if free_ttunit:
            stored.add(free_ttunit.id)
            free_ttunit.room_id = room_id
            free_ttunit.day_per = day_per
            db.session.merge(free_ttunit)

    db.session.commit()


def ttable_report(out_file, ttable_id, lead_rtype, ids):
    rsrc_dealer = ResourceDealer(default_department=None)
    rsrc_dealer.load_cts()
    rsrc_dealer.load_rooms()
    ttbl_dealer = TtableDealer()

    if lead_rtype == "class":
        lead_reses = []
        for i in ids:
            for name in rsrc_dealer.class_id2ttl[i].split(","):
                if name not in lead_reses:
                    lead_reses.append(name)
    else:
        lead_reses = [rsrc_dealer.teacher_id2ttl[i] for i in ids]
    period_names = ["%d:%d" % (obj.hours, obj.minutes) 
                    for obj in  Period.query.order_by(Period.id)]

    html_printer = HtmlPrinter()
    html_printer.print_html(
        out_file, 
        lead_rtype, lead_reses,
        ttbl_dealer.iter_ttable_events(ttable_id, rsrc_dealer),
        DAY_NAMES, period_names, no_slave=False)


def export_ttm(out_file, curriculum_id=None, ttable_id=None):
    rsrc_dealer = ResourceDealer(default_department=None)
    rsrc_dealer.load_cts()
    rsrc_dealer.load_rooms()
    ttbl_dealer = TtableDealer()

    events = list(
        ttbl_dealer.iter_ttable_events(ttable_id, rsrc_dealer)
        if ttable_id else
        ttbl_dealer.iter_curriculum_events(curriculum_id, rsrc_dealer))
    resources = {}
    for res in "teacher", "class":
        resources[res] = set(ev[res] for ev in events)
    if ttable_id:
        resources["room"] = set(ev["room"] for ev in events)
    else:
        resources["room"] = set(rsrc_dealer.room_id2ttl.itervalues())

    curriculum = Curriculum.query.filter_by(
        id=ttbl_dealer.curriculum_id).first_or_404()
#    start_module("available", True, 100);
#    print_blob_available(curric->avail_time.value(),
#                 "\t\t\t<option name=\"not-available\">",
#                 "</option>");
#    end_module()
    desires = {
        "placecapability": 75,
        "placesize": 75,
        "holes class": 100,
        "holes teacher": 6,
        "maxperday class": 100,
        "maxperday teacher": 6,
        "preferredroom": 6,
        "preferredtime": 6,
        "freemorning class": 3,
        "freemorning teacher": 1,
        "walk": 3,
        "perday class": 1,
    }
    try:
        desires.update(json.loads(curriculum.desires))
    except:
        pass
    desires.update({
        "sametime": 200, 
        "timeplace": 250, 
        "sametimeas": 75,
        "consecutive": 200, 
    })
    modules = [
        ("sametime", True),
        ("sametimeas", True),
        ("timeplace", True),
        ("consecutive", True,
         [("days-per-week", WEEK_LENGTH)]),
        ("placecapability", True),
        ("placesize", True),
        ("holes class", True),
        ("holes teacher", False),
        ("maxperday teacher", False, 
         [("maxperday", curriculum.max_per_teacher or 5)]),
        ("maxperday class", True,
         [("maxperday", curriculum.max_per_student or 5)]),
        ("preferredroom", False),
        ("preferredtime", False),
        ("freemorning class", False),
        ("freemorning teacher", False),
        ("walk class", False),
        ("walk teacher", False),
        #("perday class", False),
        #("perday teacher", False),
        ("minrooms", False),
    ]
    module_str = "\t<modules>\n"
    for mod in modules:
        name = mod[0]
        try:            
            w = int(desires[name])
        except:
            w = 1
        man = mod[1]
        w = max(75, min(w, 1000)) if man else max(1, min(w, 75))
        desires[name] = w
        spl = name.split()
        name = spl[0]
        options = mod[2] if len(mod) >= 3 else []
        if len(spl) >= 2:
            options.append(("resourcetype", spl[1]))
        module_str += (
            "\t\t<module name=\"%s\" weight=\"%d\" mandatory=\"%s\">\n" %
            (name, w, "yes" if man else "no"))
        for opt in options:
            module_str += (
                "\t\t\t<option name=\"%s\">%s</option>\n" %
                (opt[0], opt[1]))
        module_str += "\t\t</module>\n\n"
    module_str += "\t</modules>\n"
    room_by_id = rsrc_dealer.room_by_id
    printer = TtmPrinter(out_file, module_str, WEEK_LENGTH,
        events, resources, 
        dict(( (obj.name, obj.bld_group or 0)
               for obj in rsrc_dealer.building_by_id.itervalues()
        )),
        dict(( (ttl, room_by_id[i].size or 0)
               for i, ttl in rsrc_dealer.room_id2ttl.iteritems()
        )), IGNORE_TIME)
    printer.print_ttm()
    curriculum.desires = json.dumps(desires)
    db.session.merge(curriculum)
    db.session.commit()
    return ttbl_dealer.curriculum_id


def build_ttable(curriculum_id=None, ttable_id=None):
    pid = os.fork()
    if pid == 0:
        _child_build_ttable(curriculum_id, ttable_id)
    else:
        os.waitpid(pid, 0)


last_filename = "%s/last" % WORKING_DIR


def get_curr_id():
    try:
        with open(last_filename, "rt") as f:
            curr_id = int(f.readline())
    except:
        curr_id = 0
    return curr_id


def _child_build_ttable(curriculum_id, ttable_id):
    options_basename = "options.properties"
    ttabler_file = "ttabler"
    curr_id = get_curr_id() + 1
    with open(last_filename, "wt") as f:
        f.write("%d\n" % curr_id)
    base_dir = "%s/%08d" % (WORKING_DIR, curr_id)
    task_filename = "%s/timetable.task.xml" % base_dir
    log_dirname = "%s/log" % base_dir
    options_filename = "%s/%s" % (base_dir, options_basename)
    os.makedirs(log_dirname)
    with open(task_filename, "wt") as out_file:
        curriculum_id = export_ttm(out_file, curriculum_id, ttable_id)
    with open("%s/%s" % (CONFIG_DIR, options_basename), "rt") as f:
        options = f.read()
    with open(options_filename, "wt") as f:
        f.write(options)
        f.write("\n"
                "ttabler.output_dir:%s\n"
                "ttabler.task_file:%s\n"
                "ttabler.log_dir:%s\n" %
                (base_dir, task_filename, log_dirname))

    proc = subprocess.Popen(
        [ttabler_file, "-i", options_filename],
        close_fds=True)
    save_info(base_dir, {
        "pid": proc.pid,
        "curriculum_id": curriculum_id,
        "comment": u"сгенерировано %s для ведомости %s%s" % 
        (datetime.now().strftime("%Y-%m-%d %H:%M"),
         curriculum_id,
         u" по расписанию " + ttable_id
         if ttable_id else u"")
    })
    os._exit(0)


def get_ttable_progress():
    curr_id = get_curr_id()
    base_dir = "%s/%08d" % (WORKING_DIR, curr_id)
    statistics_filename = "%s/statistics.txt" % base_dir
    values = []
    try:
        with open(statistics_filename, "rt") as f:
            for line in f:
                if line.startswith("#"):
                    continue            
                try:
                    arr = line.split()
                    values.append({
                        "generation": int(arr[0]),
                        "individuals": int(arr[4]),
                        "fitness": float(arr[6]),
                        "time": int(arr[7]),
                    })
                except Exception as e:
                    pass
    except:
        pass
    ttable_id = backend_check_and_load(base_dir)        
    return {
        "values": values, "ttable_id": ttable_id,
        "comment": load_info(base_dir).get("comment", ""),
    }


def load_info(base_dir):
    info_filename = "%s/info.json" % base_dir
    try:
        with open(info_filename, "r") as f:
            return json.load(f)
    except:
        return {}


def save_info(base_dir, info):
    info_filename = "%s/info.json" % base_dir
    try:
        with open(info_filename, "w") as f:
            json.dump(info, f)
    except:
        pass


def backend_check_and_load(base_dir):
    result_filename = "%s/result.xml" % base_dir
    if not os.path.exists(result_filename):
        return None
    info = load_info(base_dir)
    if not info:
        return None
    try:
        return int(info["ttable_id"])
    except KeyError:
        pass
    ttable = Ttable(curriculum_id=info["curriculum_id"],
                    comment=info["comment"])
    db.session.add(ttable)
    db.session.commit()
    with open(result_filename, "rt") as f:
        ttable_import(ttable.id, f)
    info["ttable_id"] = ttable.id
    save_info(base_dir, info)
    return ttable.id


def ttm_interrupt():
    curr_id = get_curr_id()
    base_dir = "%s/%08d" % (WORKING_DIR, curr_id)
    info = load_info(base_dir)
    if not info:
        return
    os.kill(info["pid"], signal.SIGINT)
