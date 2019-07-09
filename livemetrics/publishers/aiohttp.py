
"""
This module provides :py:mod:`aiohttp` routes
exposing a :py:class:`livemetrics.LiveMetrics` object.

A minimal application would be:

.. code-block:: python

    import livemetrics
    import livemetrics.publishers.aiohttp
    
    from aiohttp import web
    routes = web.RouteTableDef()

    LM = livemetrics.LiveMetrics(version,about,is_healthy,is_ready)

    @routes.get("/sample")
    @LM.timer('sample','ok','error')
    async def sample(request):
        return web.Response(status=200)

    app = web.Application()
    app.add_routes(livemetrics.publishers.aiohttp.routes(LM))   # register the routes to publish the metrics
    app.add_routes(routes)                                      # register the routes of the application
    web.run_app(ap,host,port)                                   # run the application


"""

import json

import aiohttp
from aiohttp import web

class Handler:
    def __init__(self,LM):
        self.LM = LM

    async def about(self,request):
        data = self.LM.about
        return web.Response(status=200,
            headers={"Access-Control-Allow-Origin": "*"},
            text=data)

    async def is_healthy(self,request):
        status = self.LM.is_healthy()
        if status:
            return web.Response(status=200,
                headers={"Access-Control-Allow-Origin": "*"},
                text='OK')
        else:
            return web.Response(status=500,
                headers={"Access-Control-Allow-Origin": "*"},
                text='KO')

    async def is_ready(self,request):
        status = self.LM.is_ready()
        if status:
            return web.Response(status=200,
                headers={"Access-Control-Allow-Origin": "*"},
                text='OK')
        else:
            return web.Response(status=500,
                headers={"Access-Control-Allow-Origin": "*"},
                text='KO')

    async def version(self,request):
        data = self.LM.version
        return web.Response(status=200,
            content_type='application/json',
            headers={"Access-Control-Allow-Origin": "*"},
            body=data)

    async def get_meters3(self,request):
        event = request.match_info['event']
        result = request.match_info['result']
        metric = request.match_info['metric']
        data = self.LM.get_metrics(event,result,metric)
        data = json.dumps(data)
        return web.Response(status=200,
            content_type='application/json',
            headers={"Content-Length": str(len(data)), "Access-Control-Allow-Origin": "*"},
            body=data)

    async def get_meters2(self,request):
        event = request.match_info['event']
        result = request.match_info['result']
        data = self.LM.get_metrics(event,result)
        data = json.dumps(data)
        return web.Response(status=200,
            content_type='application/json',
            headers={"Content-Length": str(len(data)), "Access-Control-Allow-Origin": "*"},
            body=data)

    async def get_meters1(self,request):
        event = request.match_info['event']
        data = self.LM.get_metrics(event)
        data = json.dumps(data)
        return web.Response(status=200,
            content_type='application/json',
            headers={"Content-Length": str(len(data)), "Access-Control-Allow-Origin": "*"},
            body=data)

    async def get_meters0(self,request):
        data = self.LM.get_metrics()
        data = json.dumps(data)
        return web.Response(status=200,
            content_type='application/json',
            headers={"Content-Length": str(len(data)), "Access-Control-Allow-Origin": "*"},
            body=data)

    async def get_gauges2(self,request):
        object = request.match_info['object']
        metric = request.match_info['metric']
        data = self.LM.get_gauges(object,metric)
        data = json.dumps(data)
        return web.Response(status=200,
            content_type='application/json',
            headers={"Content-Length": str(len(data)), "Access-Control-Allow-Origin": "*"},
            body=data)

    async def get_gauges1(self,request):
        object = request.match_info['object']
        data = self.LM.get_gauges(object)
        data = json.dumps(data)
        return web.Response(status=200,
            content_type='application/json',
            headers={"Content-Length": str(len(data)), "Access-Control-Allow-Origin": "*"},
            body=data)

    async def get_gauges0(self,request):
        data = self.LM.get_gauges()
        data = json.dumps(data)
        return web.Response(status=200,
            content_type='application/json',
            headers={"Content-Length": str(len(data)), "Access-Control-Allow-Origin": "*"},
            body=data)

    def _get_histograms(self,request,event,metric):
        msg = None
        params = {}
        params.update(request.query)
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
            return web.Response(status=400,body=msg)

        # Make sure the types are correct
        params['percentiles'] = [float(x) for x in params['percentiles']]
        params['scale'] = int(params['scale'][0])

        try:
            data = self.LM.get_histograms(event,metric,**params)
        except Exception as exc:
            msg = str(exc)
            return web.Response(status=500,body=msg)
        data = json.dumps(data)
        return web.Response(status=200,
            content_type='application/json',
            headers={"Content-Length": str(len(data)), "Access-Control-Allow-Origin": "*"},
            body=data)

    async def get_histograms2(self,request):
        event = request.match_info['event']
        metric = request.match_info['metric']
        return self._get_histograms(request,event,metric)

    async def get_histograms1(self,request):
        event = request.match_info['event']
        return self._get_histograms(request,event,None)

    async def get_histograms0(self,request):
        return self._get_histograms(request,None,None)

def routes(LM):
    """
    Return a list of routes to be registered in the :py:mod:`aiohttp` application.

    *LM*: a :py:class:`livemetrics.LiveMetrics` object
    """
    handler = Handler(LM)
    return [
        web.get('/monitoring/v1/about', handler.about),
        web.get('/monitoring/v1/is_healthy', handler.is_healthy),
        web.get('/monitoring/v1/is_ready', handler.is_ready),
        web.get('/monitoring/v1/version', handler.version),

        web.get('/monitoring/v1/metrics/meters/{event}/{result}/{metric}', handler.get_meters3),
        web.get('/monitoring/v1/metrics/meters/{event}/{result}', handler.get_meters2),
        web.get('/monitoring/v1/metrics/meters/{event}', handler.get_meters1),
        web.get('/monitoring/v1/metrics/meters', handler.get_meters0),

        web.get('/monitoring/v1/metrics/gauges/{object}/{metric}', handler.get_gauges2),
        web.get('/monitoring/v1/metrics/gauges/{object}', handler.get_gauges1),
        web.get('/monitoring/v1/metrics/gauges', handler.get_gauges0),

        web.get('/monitoring/v1/metrics/histograms/{event}/{metric}', handler.get_histograms2),
        web.get('/monitoring/v1/metrics/histograms/{event}', handler.get_histograms1),
        web.get('/monitoring/v1/metrics/histograms', handler.get_histograms0),
    ]

