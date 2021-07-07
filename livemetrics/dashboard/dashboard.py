
"""

This module provides a (very) minimal application to demonstrate the usage of metrics.

Install with::

    pip install livemetrics[dashboard]

Run with::

    livemetrics-dashboard -i myconf.yaml

And then access http://localhost:9000/ to visualize the dashboard.

The configuration file describes rows, and for each row the cells to display. Each cell is associated
to one value (or to the statistics of one value for histograms).

The configuration file is a Jinja2 template used to generate a YAML file.
All macros and filters of Jinja2 are available, making possible to define template or macros for
complex cases.

A simple example:

.. code-block:: jinja

    {% set server = "http://localhost:7070/monitoring/v1" %}
    ---
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
        color: green
      - label: Memory
        server: "{{server}}/metrics/gauges/memory/count"
        type: gauge
        unit: MB
        factor: "/1048576"
        max: 256
        gauge_color: blue
        color: "#C0D0F0"
      - type: empty
      - label: Time
        server: "{{server}}/metrics/histograms/time"
        type: histogram
        unit: ms
        factor: "*1000"
        color: "#ff000080"
        median_color: green
      - label: Test
        server: "{{server}}/metrics/meters/test/ok/rate1"
        type: gauge
        unit: "/h"
        factor: "*3600"
        gauge_color: green
        color: "#C0F0C0"
        max: 25000

The cells can be of the following types:

.. list-table::
    :widths: 10 40 50

    * - Type
      - Description
      - Options

    * - ``empty``
      - Display an empty cell
      - - N/A
    * - ``label``
      - Display a static text
      - - ``label``: The text to display
    * - ``status``
      - Display a boolean value as a colored icon
      - - ``label``: A text displayed below the icon
        - ``server``: The full URL used to get the boolean value
    * - ``value``
      - Display a numeric value as a text
      - - ``label``: A text displayed below the value
        - ``server``: The full URL used to get the value or a list of URL
        - ``unit``: A small text added after the value
        - ``factor``: A factor to apply to the value. It must start with ``*`` or ``/`` to indicate the operation to execute
        - ``precision``: the number of digit after the decimal separator in the output. Ex: ``1``, ``2``, etc.
        - ``color``: The text color
        - ``operator``: in case a list of URL is provided, the operation to perform on the list of values. One of ``sum``, ``average``, ``max`` or ``min``.
    * - ``gauge``
      - Display a numeric value as a gauge and a sparkline showing the recent evolution of the value
      - - ``label``: A text displayed below the value
        - ``server``: The full URL used to get the value or a list of URL
        - ``unit``: A small text added after the label
        - ``factor``: A factor to apply to the value. It must start with ``*`` or ``/`` to indicate the operation to execute
        - ``color``: The fill color of the sparkline
        - ``gauge_color``: The color of the gauge
        - ``max``: The maximum value of the gauge
        - ``operator``: in case a list of URL is provided, the operation to perform on the list of values. One of ``sum``, ``average``, ``max`` or ``min``.
    * - ``histogram``
      - Display statistics about a value as a whisker box
      - - ``label``: A text displayed below the value
        - ``server``: The full URL used to get the statistics. It must return a json dictionary
          with values for the keys ["0.05", "0.25", "0.75", "0.95", "0.5"]
        - ``unit``: A small text added as the legend of the diagram
        - ``factor``: A factor to apply to the value. It must start with ``*`` or ``/`` to indicate the operation to execute
        - ``color``: The fill color of the box
        - ``median_color``: The color of the line showing the median value

"""

import os
import logging
import argparse
import asyncio

import urllib.request
import pickle
import json
import yaml
import ssl
from urllib.parse import urlparse,parse_qs

from jinja2 import Template,Environment,FileSystemLoader,PrefixLoader,ChoiceLoader

import aiohttp
from aiohttp import web

routes = web.RouteTableDef()

CONF = None

def server_to_list(value):
    if isinstance(value,list):
        return '["' + '", "'.join(value) + '"]'
    return '"{}"'.format(value)

def load_conf(options):
    global CONF

    myself = {'self':     FileSystemLoader(os.path.dirname(__file__)) }
    loader = PrefixLoader(myself)

    env = Environment(loader=ChoiceLoader([FileSystemLoader([".",'/']), loader]))
    env.filters.update({'server_to_list': server_to_list})
    template = env.get_template(options.input.name)
    buf = template.render()

    CONF = yaml.load(buf,Loader=yaml.Loader)

    # generate ids
    i = 1
    for r in CONF['rows']:
        r['id'] = str("id%d"%i)
        i += 1
        for c in r['cells']:
            c['id'] = str("id%d"%i)
            i += 1
    logging.debug("CONF: " + str(CONF))

@routes.get('/')
async def home_page(request):
    global CONF
    myself = {'self':     FileSystemLoader(os.path.dirname(__file__)) }
    loader = PrefixLoader(myself)
    env = Environment(loader=loader)
    env.filters.update({'server_to_list': server_to_list})

    template = env.get_template('self/dashboard.html')
    nb = 0
    if CONF:
      for r in CONF['rows']:
          for c in r['cells']:
              if c['type'] in ['gauge','histogram']:
                  nb += 1
    timeout = max(4000, min(10000,300*nb))
    buf = template.render(config=CONF, timeout=timeout)
    # logging.debug(buf)
    return web.Response(status=200, text=buf, content_type='text/html')

@routes.get('/all')
async def all(request):
    q = request.query
    logging.debug("Query: %s", q)
    val = []
    co = None
    ct = None
    for server in [q.getone('server','')]+q.getall('server[]',[]):
        if not server: continue
        try:
            logging.debug(server)
            async with aiohttp.ClientSession() as session:
                async with session.get(server, timeout=2, ssl=False) as response:
                    val.append(await response.text())
                    co = response.status
                    if 'content-type' in response.headers:
                        ct = response.content_type
        except Exception as exc:
            logging.debug(str(exc))
            val.append(None)

    logging.debug(val)
    if len(val)==1:
        if val[0] is None:
            return web.Response(status=500, text='')
        return web.Response(status=co, text=val[0], content_type=ct)

    # array of values to return
    # Only json is supported
    return web.json_response(status=200, data=[v and json.loads(v) for v in val])

def get_app():
    app = web.Application()
    app.add_routes(routes)
    return app

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
    load_conf(options)

    app = get_app()
    web.run_app(app,host=options.ip, port=options.port, access_log=None)

if __name__=='__main__':
    main()
