
"""
This module provides a :py:mod:`flask` blueprint
exposing a :py:class:`livemetrics.LiveMetrics` object.

A minimal application would be:

.. code-block:: python

    import livemetrics
    import livemetrics.publishers.flask
    
    from flask import Flask
    app = Flask(__name__)

    LM = livemetrics.LiveMetrics(version,about,is_healthy,is_ready)

    @app.route("/sample")
    @LM.timer('sample','ok','error')
    def sample():
        return "Sample!"

    app.register_blueprint(livemetrics.publishers.flask.blueprint(LM))

"""

import json

from flask import Blueprint, make_response, request

class Handler:
    def __init__(self,LM):
        self.LM = LM

    def about(self):
        data = self.LM.about
        resp = make_response(data, 200)
        resp.headers['Access-Control-Allow-Origin'] = '*'
        return resp

    def is_healthy(self):
        status = self.LM.is_healthy()
        if status:
            resp = make_response("OK", 200)
            resp.headers['Access-Control-Allow-Origin'] = '*'
            return resp
        else:
            resp = make_response("KO", 500)
            resp.headers['Access-Control-Allow-Origin'] = '*'
            return resp

    def is_ready(self):
        status = self.LM.is_ready()
        if status:
            resp = make_response("OK", 200)
            resp.headers['Access-Control-Allow-Origin'] = '*'
            return resp
        else:
            resp = make_response("KO", 500)
            resp.headers['Access-Control-Allow-Origin'] = '*'
            return resp

    def version(self):
        data = self.LM.version
        resp = make_response(data, 200)
        resp.headers['Content-Type'] = 'application/json'
        resp.headers['Access-Control-Allow-Origin'] = '*'
        return resp

    def get_meters3(self,event,result,metric):
        data = self.LM.get_metrics(event,result,metric)
        data = json.dumps(data)
        resp = make_response(data, 200)
        resp.headers['Content-Length'] = str(len(data))
        resp.headers['Content-Type'] = 'application/json'
        resp.headers['Access-Control-Allow-Origin'] = '*'
        return resp

    def get_meters2(self,event,result):
        data = self.LM.get_metrics(event,result)
        data = json.dumps(data)
        resp = make_response(data, 200)
        resp.headers['Content-Length'] = str(len(data))
        resp.headers['Content-Type'] = 'application/json'
        resp.headers['Access-Control-Allow-Origin'] = '*'
        return resp

    def get_meters1(self,event):
        data = self.LM.get_metrics(event)
        data = json.dumps(data)
        resp = make_response(data, 200)
        resp.headers['Content-Length'] = str(len(data))
        resp.headers['Content-Type'] = 'application/json'
        resp.headers['Access-Control-Allow-Origin'] = '*'
        return resp

    def get_meters0(self):
        data = self.LM.get_metrics()
        data = json.dumps(data)
        resp = make_response(data, 200)
        resp.headers['Content-Length'] = str(len(data))
        resp.headers['Content-Type'] = 'application/json'
        resp.headers['Access-Control-Allow-Origin'] = '*'
        return resp

    def get_gauges2(self,object,metric):
        data = self.LM.get_gauges(object,metric)
        data = json.dumps(data)
        resp = make_response(data, 200)
        resp.headers['Content-Length'] = str(len(data))
        resp.headers['Content-Type'] = 'application/json'
        resp.headers['Access-Control-Allow-Origin'] = '*'
        return resp

    def get_gauges1(self,object):
        data = self.LM.get_gauges(object)
        data = json.dumps(data)
        resp = make_response(data, 200)
        resp.headers['Content-Length'] = str(len(data))
        resp.headers['Content-Type'] = 'application/json'
        resp.headers['Access-Control-Allow-Origin'] = '*'
        return resp

    def get_gauges0(self):
        data = self.LM.get_gauges()
        data = json.dumps(data)
        resp = make_response(data, 200)
        resp.headers['Content-Length'] = str(len(data))
        resp.headers['Content-Type'] = 'application/json'
        resp.headers['Access-Control-Allow-Origin'] = '*'
        return resp

    def _get_histograms(self,event,metric):
        msg = None
        params = {}
        params.update(request.args)
        if not isinstance(params.setdefault('percentiles',[0.05, 0.25, 0.5, 0.75, 0.95]),list):
            params['percentiles'] = [params['percentiles']]
        if not isinstance(params.setdefault('scale',[10]),list):
            params['scale'] = [params['scale']]

        if len(params)!=2:
            keys = ", ".join(sorted(list(set(params.keys()) - {'percentiles', 'scale'})))
            msg="Invalid query parameters: " + keys
        if not metric in [None,'count','min','max','mean','stddev','quantiles','distribution']:
            msg = "Unknown metric " + metric
        if msg:
            return make_response(msg, 400)

        # Make sure the types are correct
        params['percentiles'] = [float(x) for x in params['percentiles']]
        params['scale'] = int(params['scale'][0])

        try:
            data = self.LM.get_histograms(event,metric,**params)
        except Exception as exc:
            msg = str(exc)
            return make_response(msg, 500)
        data = json.dumps(data)
        resp = make_response(data, 200)
        resp.headers['Content-Length'] = str(len(data))
        resp.headers['Content-Type'] = 'application/json'
        resp.headers['Access-Control-Allow-Origin'] = '*'
        return resp

    def get_histograms2(self,event,metric):
        return self._get_histograms(event,metric)

    def get_histograms1(self,event):
        return self._get_histograms(event,None)

    def get_histograms0(self):
        return self._get_histograms(None,None)

def blueprint(LM):
    """
    Return a blueprint with the routes and view_func for the publication of the metrics.

    *LM*: a :py:class:`livemetrics.LiveMetrics` object
    """
    handler = Handler(LM)
    blueprint = Blueprint('livemetrics', __name__)
    blueprint.add_url_rule('/monitoring/v1/about',view_func=handler.about)
    blueprint.add_url_rule('/monitoring/v1/is_healthy',view_func=handler.is_healthy)
    blueprint.add_url_rule('/monitoring/v1/is_ready',view_func=handler.is_ready)
    blueprint.add_url_rule('/monitoring/v1/version',view_func=handler.version)

    blueprint.add_url_rule('/monitoring/v1/metrics/meters/<event>/<result>/<metric>',view_func=handler.get_meters3)
    blueprint.add_url_rule('/monitoring/v1/metrics/meters/<event>/<result>',view_func=handler.get_meters2)
    blueprint.add_url_rule('/monitoring/v1/metrics/meters/<event>',view_func=handler.get_meters1)
    blueprint.add_url_rule('/monitoring/v1/metrics/meters',view_func=handler.get_meters0)

    blueprint.add_url_rule('/monitoring/v1/metrics/gauges/<object>/<metric>',view_func=handler.get_gauges2)
    blueprint.add_url_rule('/monitoring/v1/metrics/gauges/<object>',view_func=handler.get_gauges1)
    blueprint.add_url_rule('/monitoring/v1/metrics/gauges',view_func=handler.get_gauges0)

    blueprint.add_url_rule('/monitoring/v1/metrics/histograms/<event>/<metric>',view_func=handler.get_histograms2)
    blueprint.add_url_rule('/monitoring/v1/metrics/histograms/<event>',view_func=handler.get_histograms1)
    blueprint.add_url_rule('/monitoring/v1/metrics/histograms',view_func=handler.get_histograms0)

    return blueprint

