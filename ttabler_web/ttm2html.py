#!/usr/bin/python2
# -*- coding: utf-8 -*-

import sys
import re
import argparse
import xml.dom.minidom


def to_utf8(s):
    if isinstance(s, unicode):
        return s.encode("utf-8")
    return s


class TtmParser(object):
    def parse(self, f):
        self.dom = xml.dom.minidom.parse(f)

    def process_resources(self, res0):
        time_dim = None
        lead_rtype = None
        for rtype in self.dom.getElementsByTagName("resourcetype"):
            rtype_name = rtype.getAttribute("type")
            if rtype_name == "time":
                matrix = rtype.getElementsByTagName("matrix")[0]
                time_dim = (int(matrix.getAttribute("width")),
                            int(matrix.getAttribute("height")))
                continue
            elif rtype_name not in ("class", "teacher"):
                continue
            for res in rtype.getElementsByTagName("resource"):
                if to_utf8(res.getAttribute("name")) == res0:
                    lead_rtype = rtype_name
                    break
            if lead_rtype is not None and time_dim:
                break
        self.time_dim = time_dim
        self.lead_rtype = lead_rtype

    def iter_events(self):
        time_dim = self.time_dim 
        for event_node in (self.dom.getElementsByTagName("events")[0].
                           getElementsByTagName("event")):
            event = {}
            for res_node in event_node.getElementsByTagName("resource"):
                event[to_utf8(res_node.getAttribute("type"))
                      ] = res_node.getAttribute("name")
            event["subject"] = event_node.getAttribute("name")
            time = event["time"].split()
            event["time"] = (int(time[0]), int(time[1]))
            yield event


class HtmlPrinter(object):
    @staticmethod    
    def split_res(res):
        return res.split(",")


    @staticmethod
    def print_ccunit(ccunit, row2, colspan, no_slave):
        span =  2 * colspan - 1 if ccunit else 2 * colspan
        report = "\t\t\t\t<td"
        if row2:
            report += " rowspan=2"
        report += " colspan=%d align=center>" % span
        if ccunit:
            report += "<p>%s</p>" % ccunit[2]
            if not no_slave:
                report += "<p>%s</p>" % ccunit[0]
            report += "\n" "\t\t\t\t</td>\n" "\t\t\t\t<td"
            if row2:
                report += " rowspan=2";
            report += " align=center>%s" % ccunit[1]
        else:
            report += "&nbsp;"
        return report + "\n" "\t\t\t\t</td>\n"

    def print_html(self, out_file, lead_rtype, lead_reses, 
                   iter_events, day_names, period_names, no_slave):
        lead_reses = [to_utf8(s) for s in lead_reses]
        time_dim = (len(day_names) * 2, len(period_names))
        tbl_ext = [{} for i in xrange(time_dim[0] * time_dim[1])]
        slave_rtype = "class" if lead_rtype == "teacher" else "teacher"
        period_a_week = time_dim[0] * time_dim[1] / 2
        period_used = [False for i in xrange(period_a_week)]
    
        for event in iter_events:
            event = dict(((k, to_utf8(v)) for k, v in event.iteritems()))
            time = event["time"]
            time = time[0] * time_dim[1] + time[1]
            room = event["room"]
            subject = event["subject"]
            for res in self.split_res(event[lead_rtype]):
                if res not in lead_reses:
                    continue
                tbl_ext[time][res] = (event[slave_rtype], room, subject)
                period_used[time % period_a_week] = True
    
        print >>out_file, (
            "<html>\n"
            "<head>\n"
            "<meta HTTP-EQUIV=\"CONTENT-TYPE\" CONTENT=\"text/html; charset=utf-8\">\n"
            "         <style>\n"
            "    p { \n"
            "      margin:0cm; \n"
            "    }\n"
            "    td { \n"
            "      margin:0cm; \n"
            "    }\n"
            "  </style>\n"
            "</head>\n"
            "<body>\n"		
            "\t<table border=1 cellpadding=\"10\"\n"		
            "\t       style=\"border-collapse:collapse;border:solid\">\n"		
            "\t\t<col width=\"0*\">\n"
            "\t\t<col width=\"0*\">\n"),
        max_human = len(lead_reses)
        col_pair = ("\t\t<col width=\"%d%%\">\n"
                   "\t\t<col width=\"0*\">\n" %
                   (1 if max_human > 99 else 99 / max_human))
        for i in xrange(max_human):
            print >>out_file, col_pair,
        print >>out_file, ("\t\t<thead>\n"
                           "\t\t\t<tr>\n"
                           "\t\t\t\t<th colspan=\"2\">&nbsp;\n"
                           "\t\t\t\t</th>\n"),
        for res in lead_reses:
            print >>out_file, (
                "\t\t\t\t<th colspan=2 align=center>%s\n"
                "\t\t\t\t</th>\n" % res),
        print >>out_file, ("\t\t\t</tr>\n"
            "\t\t</thead>\n"
            "\t\t<tbody>\n"),
    
        prev_day = -1
        SKIP_IT = object()
        len_res = len(lead_reses)
    
        row_color = ["", " bgcolor=\"#d9d9d9\""]
        row_even = 0
        for time in xrange(period_a_week):
            if not period_used[time]:
                continue
            day = time / time_dim[1]
            pair = time % time_dim[1]
    
            print >>out_file, "\t\t\t<tr%s>\n" % row_color[row_even],
            if prev_day != day:
                prev_day = day
                span = 0
                day_shift = day * time_dim[1]
                for per in xrange(time_dim[1]):
                    if period_used[day_shift + per]:
                        span += 2
                print >>out_file, (
                    "\t\t\t\t<td rowspan=\"%d\" align=\"center\"  bgcolor=\"#ffffff\">%s\n"
                    "\t\t\t\t</td>\n"
                    % (span, day_names[day])),
            print >>out_file, (
                "\t\t\t\t<td rowspan=2 align=center>%s\n\t\t\t\t</td>\n"
                % period_names[pair]),
    
            res_no = 0
            while res_no < len_res:
                res = lead_reses[res_no]
                ccunit = tbl_ext[time].get(res, None)
                last_no = res_no
                while (last_no < len_res and
                       ccunit == tbl_ext[time].get(lead_reses[last_no], None)):
                    last_no += 1
                skip_lower = True
                for i in xrange(res_no, last_no):
                    if tbl_ext[time + period_a_week].get(lead_reses[i], None) != ccunit:
                        skip_lower = False
                        break
                if skip_lower:
                    for i in xrange(res_no, last_no):
                        tbl_ext[time + period_a_week][lead_reses[i]] = SKIP_IT
                
                print >>out_file, self.print_ccunit(ccunit, skip_lower, last_no - res_no, no_slave)
                res_no = last_no
    
            print >>out_file, "\t\t\t</tr>\n""\t\t\t<tr%s>\n" % row_color[row_even],
            res_no = 0
            while res_no < len_res:
                res = lead_reses[res_no]
                ccunit = tbl_ext[time + period_a_week].get(res, None)
                if ccunit == SKIP_IT:
                    res_no += 1
                    continue
                last_no = res_no
                while (last_no < len_res and
                       ccunit == tbl_ext[time + period_a_week].get(lead_reses[last_no], None)):
                    last_no += 1
                
                print >>out_file, self.print_ccunit(ccunit, False, last_no - res_no, no_slave)
                res_no = last_no
                
            print >>out_file, "\t\t\t</tr>\n",
            row_even = (row_even + 1) % 2
    
        print >>out_file, "\t</table>\n</body>\n</html>\n"


def main():
    arg_parser = argparse.ArgumentParser()
    arg_parser.add_argument("-o", "--output", default="-", help="output file")
    arg_parser.add_argument("input", nargs=1, help="input files")
    arg_parser.add_argument("resources", nargs="+", help="leading resources")
    arg_parser.add_argument("--no-slave", "-s", action="store_true", help="do not print non-leading resources")
    args = arg_parser.parse_args()

    day_names = ["Пн", "Вт", "Ср", "Чт", "Пт", "Сб", "Вс"]
    period_names = [
        "8:30",
        "10:25",
        "12:35",
        "14:30",
        "16:25",
        "18:25",
        "20:30",
    ]
    out_file = sys.stdout if args.output == "-" else open(args.output, "wt")
    lead_reses = args.resources
    no_slave = args.no_slave

    ttm_parser = TtmParser()
    ttm_parser.parse(args.input[0])
    ttm_parser.process_resources(lead_reses[0])
    
    time_dim = ttm_parser.time_dim
    lead_rtype = ttm_parser.lead_rtype
    
    if not time_dim:
        print >>sys.stderr, "time is not defined"
        sys.exit(2)
    if not lead_rtype:
        print >>sys.stderr, "cannot determine leading resource type"
        sys.exit(2)
    if time_dim[1] > len(period_names):
        print >>sys.stderr, "too many periods: %d" % time_dim[1]
        sys.exit(2)
    if time_dim[0] > len(day_names) * 2:
        print >>sys.stderr, "too many days: %d" % time_dim[0]
        sys.exit(2)
    
    html_printer = HtmlPrinter()
    period_names = period_names[:time_dim[1]]
    day_names = day_names[:time_dim[0] / 2]
    html_printer.print_html(
        out_file, 
        lead_rtype, lead_reses,
        ttm_parser.iter_events(),
        day_names, period_names, no_slave)

    if out_file != sys.stdout:
        out_file.close()
        
        
if __name__ == "__main__":
    main()
