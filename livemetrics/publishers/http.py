
"""
This module provides a :py:class:`http.server.BaseHTTPRequestHandler` subclass
exposing a :py:class:`livemetrics.LiveMetrics` object.

A minimal application would be:

.. code-block:: python

    import livemetrics
    import livemetrics.publishers.http

    import http.server

    LM = livemetrics.LiveMetrics(version,about,is_healthy,is_ready)

    class Sample(livemetrics.publishers.http.HTTPRequestHandler):

        @LM.timer("sample","ok","error")
        def do_GET(self):
            if self.path=='/sample':
                self.send_response(200)
                self.end_headers()
            else:
                return super().do_GET()

    httpd = http.server.HTTPServer((host,port), lambda r,a,s: Sample(LM,r,a,s))
    httpd.serve_forever()

"""

import json
import http.server
import posixpath
from urllib.parse import unquote
from urllib.parse import urlparse,parse_qs

#______________________________________________________________________________
class HTTPRequestHandler(http.server.BaseHTTPRequestHandler):
    """
    Subclass this class in your application to inherit the handling of GET requests
    exposing a :py:class:`livemetrics.LiveMetrics` object.
    """

    def __init__(self,LM,request,client_address,server):
        self.LM = LM
        return super().__init__(request,client_address,server)

    def do_GET(self):
        if self.path=='/monitoring/v1/about':
            data = self.LM.about
            self.send_response(200)
            self.send_header("Content-Type","text/plain")
            self.send_header("Access-Control-Allow-Origin","*")
            self.send_header("Content-Length", str(len(data)))
            self.end_headers()
            self.wfile.write(data.encode('ascii'))
        elif self.path=='/monitoring/v1/is_healthy':
            status = self.LM.is_healthy()
            if status:
                data = 'OK'
                self.send_response(200)
                self.send_header("Content-Type","text/plain")
                self.send_header("Access-Control-Allow-Origin","*")
                self.send_header("Content-Length", str(len(data)))
                self.end_headers()
                self.wfile.write(data.encode('ascii'))
            else:
                data = 'KO'
                self.send_response(500)
                self.send_header("Content-Type","text/plain")
                self.send_header("Access-Control-Allow-Origin","*")
                self.send_header("Content-Length", str(len(data)))
                self.end_headers()
                self.wfile.write(data.encode('ascii'))
        elif self.path=='/monitoring/v1/is_ready':
            status = self.LM.is_ready()
            if status:
                data = 'OK'
                self.send_response(200)
                self.send_header("Content-Type","text/plain")
                self.send_header("Access-Control-Allow-Origin","*")
                self.send_header("Content-Length", str(len(data)))
                self.end_headers()
                self.wfile.write(data.encode('ascii'))
            else:
                data = 'KO'
                self.send_response(500)
                self.send_header("Content-Type","text/plain")
                self.send_header("Access-Control-Allow-Origin","*")
                self.send_header("Content-Length", str(len(data)))
                self.end_headers()
                self.wfile.write(data.encode('ascii'))
        elif self.path=='/monitoring/v1/version':
            data = self.LM.version
            self.send_response(200)
            self.send_header("Content-Type","application/json")
            self.send_header("Access-Control-Allow-Origin","*")
            self.send_header("Content-Length", str(len(data)))
            self.end_headers()
            self.wfile.write(data.encode('ascii'))
        elif self.path.startswith('/monitoring/v1/metrics/meters'):
            # Parse path {event}/{result}/{metric}
            path = posixpath.normpath(unquote(self.path)).split('/')
            path.extend([None,None,None])
            event,result,metric = path[5:8]
            self.send_response(200)
            self.send_header("Content-Type","application/json")
            self.send_header("Access-Control-Allow-Origin","*")
            data = self.LM.get_metrics(event,result,metric)
            data = json.dumps(data)
            self.send_header("Content-Length", str(len(data)))
            self.end_headers()
            self.wfile.write(data.encode('ascii'))
        elif self.path.startswith('/monitoring/v1/metrics/gauges'):
            # Parse path {object}/{metric}
            path = posixpath.normpath(unquote(self.path)).split('/')
            path.extend([None,None])
            name,metric = path[5:7]
            self.send_response(200)
            self.send_header("Content-Type","application/json")
            self.send_header("Access-Control-Allow-Origin","*")
            data = self.LM.get_gauges(name,metric)
            data = json.dumps(data)
            self.send_header("Content-Length", str(len(data)))
            self.end_headers()
            self.wfile.write(data.encode('ascii'))
        elif self.path.startswith('/monitoring/v1/metrics/histograms'):
            pr = urlparse(self.path)
            # Parse path {event}/{metric}
            path = posixpath.normpath(unquote(pr.path)).split('/')
            path.extend([None,None])
            event,metric = path[5:7]
            # analyze query parameters
            params = parse_qs(pr.query)
            if 'percentiles' not in params:
                # Define default value
                params['percentiles'] = [0.05, 0.25, 0.5, 0.75, 0.95]
            if 'scale' not in params:
                # Define default value
                params['scale'] = [10]
            msg = None
            if len(params)!=2:
                keys = ", ".join(sorted(list(set(params.keys()) - {'percentiles', 'scale'})))
                msg="Invalid query parameters: " + keys
            if not metric in [None,'count','min','max','mean','stddev','quantiles','distribution']:
                msg = "Unknown metric " + metric
            if msg:
                self.send_response(400)
                self.send_header("Access-Control-Allow-Origin","*")
                self.send_header("Content-Length", str(len(msg)))
                self.end_headers()
                self.wfile.write(msg.encode('ascii'))
                return
            # Make sure the types are correct
            params['percentiles'] = [float(x) for x in params['percentiles']]
            params['scale'] = int(params['scale'][0])
            try:
                data = self.LM.get_histograms(event,metric,**params)
            except Exception as exc:
                msg = str(exc)
                self.send_response(500)
                self.send_header("Access-Control-Allow-Origin","*")
                self.send_header("Content-Length", str(len(msg)))
                self.end_headers()
                self.wfile.write(msg.encode('ascii'))
                return
            data = json.dumps(data)
            self.send_response(200)
            self.send_header("Content-Type","application/json")
            self.send_header("Access-Control-Allow-Origin","*")
            self.send_header("Content-Length", str(len(data)))
            self.end_headers()
            self.wfile.write(data.encode('ascii'))
        else:
            self.send_response(404)
            self.send_header("Access-Control-Allow-Origin","*")
            self.end_headers()
