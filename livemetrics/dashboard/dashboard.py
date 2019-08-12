
"""

This module provides a (very) minimal application to demonstrate the usage of metrics.

Install with::

    pip install livemetrics[dashboard]

Run with::

    livemetrics-dashboard -i myconf.yaml

And then access http://localhost:9000/ to visualize the dashboard.

The configuration file describes:

- The rows in the dashboard. One row corresponds to a set of meters/histograms/gauges from one server.
- For each row, a list of meters, a list of histograms, and a list of gauges.

The configuration can define variables and reuse them in the rest of the file using Jinja2 syntax (``{{var}}``).

For example:

.. code-block:: yaml

    ---
    vars:
      server: http://localhost:7070/monitoring/v1
    title: Sample
    rows:
    - label: First Line
      cells:
      - label: Line 1
        type: label
      - label: Health
        server: "{{server}}/is_healthy"
        type: status
      - label: CPU
        server: "{{server}}/metrics/gauges/cpu/count"
        type: value
        unit: "%"
        factor: "*100"
        color: "blue"
      - label: Memory
        server: "{{server}}/metrics/gauges/memory/count"
        type: gauge
        unit: MB
        factor: "/1048576"
        max: 100
        gauge_color: blue
        color: "#C0D0F0"
      - type: empty
      - label: Time
        server: "{{server}}/metrics/histograms/time"
        type: histogram
        unit: ms
        factor: "*1000"
        color: blue
      - label: Test
        server: "{{server}}/metrics/meters/test/ok/rate1"
        type: gauge
        unit: "/h"
        factor: "*3600"
        gauge_color: green
        color: "#C0F0C0"
        max: 25000

"""

# XXX: color of the whisker

import os
import logging
import argparse

import socketserver
import http.server
import urllib.request
import pickle
import json
import yaml
from urllib.parse import urlparse,parse_qs

from jinja2 import Template,Environment,FileSystemLoader,PrefixLoader

class DashBoardHTTPRequestHandler(http.server.SimpleHTTPRequestHandler):
    conf = None

    def __init__(self, request, client_address, server, options):
        if DashBoardHTTPRequestHandler.conf is None:
            DashBoardHTTPRequestHandler.conf = 1

            conf = yaml.load(options.input,Loader=yaml.Loader)

            # Extract vars and apply
            vars = conf.get('vars',{})
            env = Environment(loader=FileSystemLoader([".",'/']))
            template = env.get_template(options.input.name)
            buf = template.render(**vars)

            DashBoardHTTPRequestHandler.conf = yaml.load(buf,Loader=yaml.Loader)

            # generate ids
            i = 1
            for r in DashBoardHTTPRequestHandler.conf['rows']:
                for c in r['cells']:
                    c['id'] = str("id%d"%i)
                    i += 1

        super().__init__(request, client_address, server)

    def end_headers(self):
        self.send_header("Access-Control-Allow-Origin","*")
        return http.server.SimpleHTTPRequestHandler.end_headers(self)

    def do_GET(self):
        if self.path=='/':
            myself = {'self':     FileSystemLoader(os.path.dirname(__file__)) }
            loader = PrefixLoader(myself)
            env = Environment(loader=loader)

            template = env.get_template('self/dashboard.html')
            buf = template.render(config=self.conf)
            self.send_response(200)
            self.send_header("Content-Type","text/html ; encoding=UTF-8")
            self.send_header("Content-Length", str(len(buf)))
            self.end_headers()
            self.wfile.write(buf.encode('utf-8'))
            return
        elif self.path.startswith('/all'):
            pr = urlparse(self.path)
            params = parse_qs(pr.query)
            try:
                with urllib.request.urlopen(params['server'][0]) as obj:
                    buf = obj.read()
                    self.send_response(obj.getcode())
                    if 'content-type' in obj.info():
                        self.send_header("Content-Type",obj.info()['content-type'])
                    self.send_header("Content-Length", str(len(buf)))
                    self.end_headers()
                    self.wfile.write(buf)
                    return
            except:
                self.send_response(500)
                self.end_headers()
                return
        return super().do_GET()

    def log_message(self, format, *args):
        # override to include in the standard log file and to apply filtering
        logging.debug("%s - - [%s] %s" %
                         (self.client_address[0],
                          self.log_date_time_string(),
                          format%args))

class ThreadedHTTPServer(socketserver.ThreadingMixIn, http.server.HTTPServer):
    """Handle requests in a separate thread."""

def serve(options):
    server_address = (options.ip, options.port)
    httpd = http.server.HTTPServer(server_address, lambda r,a,s:  DashBoardHTTPRequestHandler(r,a,s,options))
    httpd.serve_forever()

#______________________________________________________________________________
def main(args=None):

    parser = argparse.ArgumentParser(description='Dashboard Sample')

    parser.add_argument("-i", "--input",required=True,dest='input',type=argparse.FileType(mode='r'),help="Configuration file")
    parser.add_argument("-I", "--listening-ip",default='0.0.0.0',dest='ip',help="Listening IP address (default: 0.0.0.0)")
    parser.add_argument("-P", "--listening-port",default=9000,dest='port',type=int,help="Listening port number (default: 9000)")
    parser.add_argument("-l", "--loglevel",default='INFO',dest='loglevel',help="Log level")
    parser.add_argument("-f", "--logfile",default=None,dest='logfile',help="Log file")

    options = parser.parse_args(args=args)

    logging.basicConfig(format='%(message)s',level=logging.getLevelName(options.loglevel))
    if options.logfile:
        fh = logging.handlers.TimedRotatingFileHandler(options.logfile,when='H',interval=8)
        fh.setLevel(logging.getLevelName(options.loglevel))
        formatter = logging.Formatter('%(asctime)-15s %(levelname)s - %(message)s')
        fh.setFormatter(formatter)
        logging.getLogger().addHandler(fh)

    logging.debug(options)

    serve(options)

if __name__=='__main__':
    main()
