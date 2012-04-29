#!/usr/bin/python2
# -*- coding: utf-8 -*-

import sys
import re
import argparse
from HTMLParser import HTMLParser


def to_utf8(s):
    if isinstance(s, unicode):
        return s.encode("utf-8")
    return s


def charcount(s, c):
    num = 0
    for c1 in s:
        if c == c1:
            num += 1
    return num


class Total(object):
    event_count = 0
    event_count_groups = 0
    event_count_by_group = {}
    lecturers = {}
    alone = set()


re_time = re.compile(r"\s*\d{1,2}[.:]\d{2}\s*")
re_empty = re.compile(r"^\s*$")
re_spaces = re.compile(r"[ \t\r\f\v]+")
re_all_spaces = re.compile(r"\s+")
re_room = re.compile(r"^(\d+)\s*([^ \t\r\f\v\n].*)$")
re_room_ext = re.compile(r"^\d+\s+(\S+\s+)*(\S+)$")


class RoomParser(object):
    def __init__(self):
        self.clear()

    def clear(self):
        self.buildings = {}
        self.room_size = {}

    def parse(self, filename):
        self.clear()
        with open(filename, "rt") as fobj:
            all_lines = fobj.read().split("\n")
        for line in all_lines:
            items = [i.strip() for i in line.split("\t") if i.strip()]
            if len(items) >= 2 and items[1].isdigit():
                self.room_size[items[0]] = items[1]
            else:
                bgr = line.strip()
                self.buildings.update(dict(((bld, bgr) for bld in line.split()))) 


class IgnoreTimeParser(object):
    def __init__(self):
        self.clear()
    
    def clear(self):
        self.ignore_time = set()

    def parse(self, filename):
        self.clear()
        with open(filename, "rt") as fobj:
            self.ignore_time = set(filter(lambda x: x, fobj.read().split("\n")))


class CurriculumTsvParser(object):
    def __init__(self):
        self.clear()
    
    def clear(self):
        self.curriculum = {}

    def parse(self, filename):
        self.clear()
        with open(filename, "rt") as fobj:
            for line in fobj.read().split("\n"):
                if not line:
                    continue
                cc = line.split("\t")
                if len(cc) >= 3:
                    self.curriculum[(cc[0], cc[2])] = cc[1]


class TtableHtmlParser(HTMLParser):

    def __init__(self, week_length, curriculum, ignore_time):
        HTMLParser.__init__(self)
        self.events = []
        self.resources = {"teacher": set(), "class": set(), "room": set(), "group": set()}
        self.curriculum = curriculum
        self.ignore_time = ignore_time
        self.week_length = week_length

    def clear(self):
        self.cell_text = ""
        self.in_cell = False
        self.in_header = False
        self.attrs = {}
        self.time_rowspan = 0
        self.cell_no = -2
        self.time_text = None
        self.week = 0
        self.day = -1
        self.pair = 0
        self.groups = []
        self.saved_text = {}
        self.cells = [[], []]

    def process_file(self, file_obj):
        self.clear()
        self.reset()
        self.feed(file_obj)

    def get_td_attr(self, attr, default=None):
        for (key, value) in self.attrs:
            if key == attr:
                return value
                break
        return default

    def get_td_attr_int(self, attr, default=0):
        try:
            return int(self.get_td_attr(attr, default))
        except:
            return default

    def add_one_event(self, subject, teacher, stream, room, day, period):
        self.events.append({
            "subject": subject,
            "teacher": teacher,
            "class": stream,
            "room": room,
            "time": (day, period)
        })

    def add_event(self, event_text, room_text, cell_no, colspan, week):
        if event_text is None:
            return
#        print "got `%s' `%s' week %d; %d - %d" % (event_text, room_text, week, cell_no, colspan)
        event = event_text.split("\n")
        subject = event[0].strip()
        if subject == u"ФВ" or not room_text:
            return
        event_groups = self.groups[(cell_no - colspan + 1) / 2:(cell_no + 2) / 2]
        stream = ",".join(event_groups)
        if room_text:
            room_text = re_all_spaces.sub(" ", room_text).strip()
            m = re_room.match(room_text)
            room = (m.group(1) + " " + m.group(2)) if m else room_text
        else:
            room = "NO_ROOM"
        if len(event) > 1:
            teacher = event[1].strip().replace("..", ".").strip(",")
        else:
            teacher = ""

        if week == 2:
            self.add_one_event(subject, teacher, stream, room,
                               self.day, self.pair)
            self.add_one_event(subject, teacher, stream, room,
                               self.day + self.week_length, self.pair)
        else:
            self.add_one_event(subject, teacher, stream, room,
                               self.day + week * self.week_length,
                               self.pair)

    def process_row(self):
        #print self.time_text
        #for row in self.cells:
        #    for cell in row:
        #        print "`%s' " % cell.replace("\n", " ") if cell is not None else "None ",
        #    print
        
        for cell_no in xrange(len(self.groups)):
            if not self.cells[0][cell_no * 2]:
                continue
            both_weeks = (self.time_rowspan == 1 or
                          (self.cells[0][cell_no * 2] == self.cells[1][cell_no * 2]
                           and self.cells[0][cell_no * 2 + 1] == self.cells[1][cell_no * 2 + 1]))
            if both_weeks:
                self.cells[1][cell_no * 2] = None
            self.add_event(
                self.cells[0][cell_no * 2],
                self.cells[0][cell_no * 2 + 1],
                cell_no * 2,
                self.colspans[0][cell_no * 2],
                2 if both_weeks else 0)
        for cell_no in xrange(len(self.groups)):
            if not self.cells[1][cell_no * 2]:
                continue
            self.add_event(
                self.cells[1][cell_no * 2],
                self.cells[1][cell_no * 2 + 1],
                cell_no * 2,
                self.colspans[1][cell_no * 2],
                1)

    def handle_starttag(self, tag, attrs):
    #    print "Encountered a start tag:", tag
        if tag == "td":
            self.in_cell = True
            self.cell_text = ""
            self.attrs = attrs
            if self.get_td_attr_int("rowspan", 1) > 2:
                self.day += 1
                self.pair = -1
                self.cell_no = -2
        elif tag == "p" and self.in_cell and not re_empty.match(self.cell_text):
            self.cell_text += "\n"
        elif tag == "thead":
            self.in_header = True
        elif tag == "div" and not self.in_cell:
            self.attrs = attrs
            if self.get_td_attr("type", "").upper() == "HEADER":
                self.in_header = True
            
        pass 
        
    def handle_endtag(self, tag):
     #   print "Encountered  an end tag:", tag
        if (tag == "thead" or tag == "div") and self.in_header:
            self.in_header = False
            self.groups = self.cell_text.split()
            self.resources["group"].update(self.groups)
        elif tag == "tr" and not self.in_header:
            self.cell_no = 0
            self.week += 1
            if self.week > 1 or self.time_rowspan == 1:
                self.process_row()
        elif tag == "td" and not self.in_header:
            self.in_cell = False
            self.cell_text = re_spaces.sub(" ", self.cell_text)
            if re_time.match(self.cell_text):
                self.time_rowspan = self.get_td_attr_int("rowspan", 1)
                self.week = 0
                self.cell_no = 0
                self.pair += 1
                self.day = max(self.day, 0)
                self.time_text = self.cell_text.strip()
                self.cells = [
                    [None for i in xrange(len(self.groups * 2))],
                    [None for i in xrange(len(self.groups * 2))]]
                self.colspans = [
                    [0 for i in xrange(len(self.groups * 2))],
                    [0 for i in xrange(len(self.groups * 2))]]
            elif self.cell_no != -2:
                if re_empty.match(self.cell_text):
                    self.cell_text = ""
                colspan = self.get_td_attr_int("colspan", 1)
                if self.week == 0:
                    self.cell_no += colspan
                    cell_no = self.cell_no - 1
                    self.colspans[0][cell_no] = colspan
                    self.cells[0][cell_no] = self.cell_text
                    if self.get_td_attr_int("rowspan", 1) > 1:
                        for i in xrange(cell_no - colspan + 1, cell_no):
                            self.cells[1][i] = ""
                        self.colspans[1][cell_no] = colspan
                        self.cells[1][cell_no] = self.cell_text
                else:
                    try:
                        while self.cells[1][self.cell_no] is not None:
                            self.cell_no += 1
                        self.cell_no += colspan
                        cell_no = self.cell_no - 1
                        self.cells[1][cell_no] = self.cell_text
                        self.colspans[1][cell_no] = colspan
                    except IndexError:
                        pass
        pass
    
    def handle_data(self, data):
        if self.in_cell or self.in_header:
            self.cell_text += data.replace("\n", " ")
        pass

    def accumulate_events(self):
        event_acc = {}
        for event in self.events:
            key = (event["room"], event["time"])
            if event["room"] in self.ignore_time:
                oth_event = None
            else:
                oth_event = event_acc.get(key, None)
            if oth_event:
                oth_event["class"] += "," + event["class"]
                event["class"] = None
            else:
                event_acc[key] = event
        self.events = [event for event in self.events if event["class"]]
        lecturers = {}
        for event in self.events:
            event["class"] = ",".join(sorted(event["class"].split(",")))
            self.resources["class"].add(event["class"])
            self.resources["room"].add(event["room"])
            teacher = event["teacher"]
            if teacher:
                lecturers[(event["subject"], event["class"])] = teacher

        for event in self.events:
            subject = event["subject"]
            teacher = self.curriculum.get((subject, event["class"]), None)
            if teacher:
                event["teacher"] = teacher
            elif not event["teacher"]:
                event["teacher"] = (
                    lecturers.get((subject, event["class"]), None)
                    or ("TEACHER OF %s" % subject))
            self.resources["teacher"].add(event["teacher"])


class TtmPrinter(object):
    
    def __init__(self, out_file, modules, week_length, events,
                 resources, buildings, room_size, ignore_time):
        self.out_file = out_file
        self.modules = modules
        self.week_length = week_length
        self.events = [dict(((k, to_utf8(v)) for k, v in ev.iteritems()))
                       for ev in events]
        self.resources = dict(((k, [to_utf8(i) for i in v])
                               for k, v in resources.iteritems()))
        self.buildings = dict(((to_utf8(k), v)
                               for k, v in buildings.iteritems()))
        self.room_size = dict(((to_utf8(k), v)
                               for k, v in room_size.iteritems()))
        self.ignore_time = [to_utf8(i) for i in ignore_time]

    def print_resource_type(self, res_type):
        print >>self.out_file, "\t\t\t<resourcetype type=\"%s\">" % res_type
        if res_type == "time":
            print >>self.out_file, "\t\t\t\t<matrix width=\"%d\" height=\"%d\"/>" % (self.week_length * 2, 6)
        else:
            if res_type == "class":
                conflicts = self.find_class_conflicts()
            else:
                conflicts = []
            for res in sorted(self.resources[res_type]):
                print >>self.out_file, "\t\t\t\t<resource name=\"%s\">" % res
                if res_type == "class":
                    if "," in res:
                        for conf in res.split(","):
                            print >>self.out_file, "\t\t\t\t\t<restriction type=\"realres\">%s</restriction>" % conf
                        for conf in res.split(",") + list(conflicts.get(res, [])):
                            print >>self.out_file, "\t\t\t\t\t<restriction type=\"conflicts-with\">%s</restriction>" % conf
                    print >>self.out_file, "\t\t\t\t\t<restriction type=\"size\">%d</restriction>" % (1 + charcount(res, ","))

                if res in self.ignore_time:
                    print >>self.out_file, "\t\t\t\t\t<restriction type=\"ignore-time\"/>"
                if res_type == "room":
                    size = self.room_size.get(res, None)
                    if size:
                        print >>self.out_file, "\t\t\t\t\t<restriction type=\"size\">%s</restriction>" % size
                    m = re_room_ext.match(res)
                    if m:
                        bld = self.buildings.get(m.group(2), None)
                        if bld:
                            print >>self.out_file, "\t\t\t\t\t<restriction type=\"building\">%s</restriction>" % bld
                print >>self.out_file, "\t\t\t\t</resource>"
        print >>self.out_file, "\t\t\t</resourcetype>\n"

    def print_resources(self):
        print >>self.out_file, "\t<resources>"
        print >>self.out_file, "\t\t<constant>"
        for res_type in "teacher", "class":
            self.print_resource_type(res_type)
        print >>self.out_file, "\t\t</constant>\n"

        print >>self.out_file, "\t\t<variable>"
        for res_type in "room", "time":
            self.print_resource_type(res_type)
        print >>self.out_file, "\t\t</variable>\n"
        print >>self.out_file, "\t</resources>\n"

    def print_events(self):
        print >>self.out_file, "\t<events>"
        for event in sorted(self.events,
                            key=lambda e: (e["subject"], e.get("time", None))):
            print >> self.out_file, (
                "\t\t<event name=\"{subject}\" repeats=\"1\">\n"
                "\t\t\t<resource type=\"teacher\" name=\"{teacher}\"/>\n"
                "\t\t\t<resource type=\"class\" name=\"{class}\"/>".format(**event))
            try:
                room = event["room"]
            except KeyError:
                pass
            else:
                if room:
                    print >> self.out_file, (
                        "\t\t\t<resource type=\"room\" name=\"%s\"/>" % room)
            if "time" in event:
                print >> self.out_file, (
                    "\t\t\t<resource type=\"time\" "
                    "name=\"{time[0]} {time[1]}\"/>".format(**event))
            print >> self.out_file, "\t\t</event>"
        print >>self.out_file, "\t</events>\n"

    def start_ttm(self):
        print >>self.out_file, """<?xml version="1.0" encoding="utf-8"?>
<ttm version="0.2.0" fitness="100000">
"""
        print >>self.out_file, self.modules

    def end_ttm(self):
        print >>self.out_file, "</ttm>"

    def find_class_conflicts(self):
        streams = {}
        for res in self.resources["class"]:
            if "," not in res:
                continue
            for gr in res.split(","):
                try:
                    streams[gr].add(res)
                except:
                    streams[gr] = set([res])

        conflicts = {}
        for res in self.resources["class"]:
            if "," not in res:
                continue
            conflicts[res] = set()
            for gr in res.split(","):
                conflicts[res].update(streams[gr])
            conflicts[res].discard(res)
        return conflicts

    def print_ttm(self):        
        self.start_ttm()                
        self.print_resources()
        self.print_events()
        self.end_ttm()
            
    def print_ccl(self):
        event_count = {}
        for event in self.events:
            key = (event["subject"], event["teacher"], event["class"])
            event_count[key] = event_count.get(key, 0) + 1
        for key in sorted(event_count.iterkeys(), key=lambda e: e[1]):
            print >>self.out_file, "%s\t%s\t%s\t%s" % (
                key[0], key[1], key[2], event_count[key])

    def print_room(self):
        room_size = {}
        for event in self.events:
            room_size[event["room"]] = max(
                1 + charcount(event["class"], ","),
                room_size.get(event["room"], 0))
        for roo in sorted(room_size):
            print "%s\t%d" % (roo, room_size[roo])
        

def main():
    arg_parser = argparse.ArgumentParser()
    arg_parser.add_argument("-o", "--output", default="-", help="output file")
    arg_parser.add_argument("input", nargs="+", default=None, help="input files")
    arg_parser.add_argument("-m", "--modules", default="modules.xml", help="modules file")
    arg_parser.add_argument("--ignore_time", default="ignore.txt", help="ignore sametime file")
    arg_parser.add_argument("--curriculum", default=None, help="curriculum file")
    arg_parser.add_argument("--rooms", default=None, help="rooms description")
    arg_parser.add_argument("-f", "--format", default="ttm", help="output format (ttm, ccl)")
    args = arg_parser.parse_args()
    
    it_parser = IgnoreTimeParser()
    cclum_parser = CurriculumTsvParser()
    room_parser = RoomParser()
    
    if args.curriculum:
        cclum_parser.parse(args.curriculum)
    if args.ignore_time:
        it_parser.parse(args.ignore_time)
    if args.rooms:
        room_parser.parse(args.rooms)
    
    html_parser = TtableHtmlParser(6, cclum_parser.curriculum, it_parser.ignore_time)
    for filename in args.input:
        with open(filename) as f:
            try:
                html_parser.process_file(unicode(f.read(), "utf-8"))
            except Exception as ex:
                print ex

    html_parser.accumulate_events()

    out_file = (sys.stdout
                if args.output == "-"
                else open(args.output, "wt"))

    try:
        with open(args.modules, "rt") as f:
            modules = f.read()
    except:
        modules = ""
    printer = TtmPrinter(out_file, modules,
                         html_parser.week_length, html_parser.events, html_parser.resources,
                         room_parser.buildings, room_parser.room_size,
                         it_parser.ignore_time)

    fmt = args.format
    if fmt == "ttm":
        printer.print_ttm()
    elif fmt == "ccl":
        printer.print_ccl()
    elif fmt == "room":
        printer.print_room()
    else:
        print >>sys.stderr, "Invalid format %s" % fmt
    if out_file != sys.stdout:
        out_file.close()

    print >>sys.stderr, "event_count %d" % len(html_parser.events)
    for res_type in html_parser.resources:
        print  >>sys.stderr, "%s - %d" % (res_type, len(html_parser.resources[res_type]))


if __name__ == "__main__":
    main()
