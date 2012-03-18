#!/usr/bin/python2
# vim: tabstop=4 shiftwidth=4 softtabstop=4

import argparse
import logging
import sys



def main():
    arg_parser = argparse.ArgumentParser()
    arg_parser.add_argument("--no-reload", "-r", default=False, 
                            action="store_true", help="do not reload")
    arg_parser.add_argument("host:port", nargs="?", 
                            default="127.0.0.1:8080", help="host:port")
    args = arg_parser.parse_args()
        
    logging.basicConfig(level=logging.DEBUG)
    from ttabler_web import app
    listen = getattr(args, "host:port").split(':')
    app.debug = True
    app.run(host=listen[0], port=int(listen[1]), use_reloader=not args.no_reload)


if __name__ == "__main__":
    main()