
"""
This module provides :py:mod:`Django` views
exposing a :py:class:`livemetrics.LiveMetrics` object.

A minimal application would be:

.. code-block:: python

    import livemetrics
    import livemetrics.publishers.django
    
    import django
    from django.http import HttpResponse
    from django.urls import path

    # Declare a global LiveMetrics object in one of your modules
    LM = livemetrics.LiveMetrics(version,about,is_healthy,is_ready)

    @LM.timer('sample','ok','error')
    def sample_view(request):
        return HttpResponse("sample")

In your :file:`urls.py`, register your views with:

.. code-block:: python

    urlpatterns = [
        path('sample', sample_view, name='sample'),
    ]

    urlpatterns += livemetrics.publishers.django.urlpatterns(LM)

"""

import json

from django.http import HttpResponse
from django.views import View
from django.urls import path

class About(View):
    LM = None
    def get(self,request):
        return HttpResponse(self.LM.about)

class IsHealthy(View):
    LM = None
    def get(self,request):
        status = self.LM.is_healthy()
        if status:
            resp = HttpResponse('OK')
            resp["Access-Control-Allow-Origin"] = "*"
            return resp
        else:
            resp = HttpResponse('KO', status=500)
            resp["Access-Control-Allow-Origin"] = "*"
            return resp

class IsReady(View):
    LM = None
    def get(self,request):
        status = self.LM.is_ready()
        if status:
            resp = HttpResponse('OK')
            resp["Access-Control-Allow-Origin"] = "*"
            return resp
        else:
            resp = HttpResponse('KO', status=500)
            resp["Access-Control-Allow-Origin"] = "*"
            return resp

class Version(View):
    LM = None
    def get(self,request):
        resp = HttpResponse(self.LM.version,content_type='application/json')
        resp["Access-Control-Allow-Origin"] = "*"
        return resp

class Meters3(View):
    LM =  None
    def get(self,request,event,result,metric):
        data = self.LM.get_metrics(event,result,metric)
        data = json.dumps(data)
        resp = HttpResponse(data,content_type='application/json')
        resp["Access-Control-Allow-Origin"] = "*"
        return resp

class Meters2(View):
    LM =  None
    def get(self,request,event,result):
        data = self.LM.get_metrics(event,result)
        data = json.dumps(data)
        resp = HttpResponse(data,content_type='application/json')
        resp["Access-Control-Allow-Origin"] = "*"
        return resp

class Meters1(View):
    LM =  None
    def get(self,request,event):
        data = self.LM.get_metrics(event)
        data = json.dumps(data)
        resp = HttpResponse(data,content_type='application/json')
        resp["Access-Control-Allow-Origin"] = "*"
        return resp

class Meters0(View):
    LM =  None
    def get(self,request):
        data = self.LM.get_metrics()
        data = json.dumps(data)
        resp = HttpResponse(data,content_type='application/json')
        resp["Access-Control-Allow-Origin"] = "*"
        return resp

class Gauges2(View):
    LM =  None
    def get(self,request,object,metric):
        data = self.LM.get_gauges(object,metric)
        data = json.dumps(data)
        resp = HttpResponse(data,content_type='application/json')
        resp["Access-Control-Allow-Origin"] = "*"
        return resp

class Gauges1(View):
    LM =  None
    def get(self,request,object):
        data = self.LM.get_gauges(object)
        data = json.dumps(data)
        resp = HttpResponse(data,content_type='application/json')
        resp["Access-Control-Allow-Origin"] = "*"
        return resp

class Gauges0(View):
    LM =  None
    def get(self,request):
        data = self.LM.get_gauges()
        data = json.dumps(data)
        resp = HttpResponse(data,content_type='application/json')
        resp["Access-Control-Allow-Origin"] = "*"
        return resp

def _get_histograms(LM,request,event,metric):
    msg = None
    params = {}
    params.update(request.GET)
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
        return HttpResponse(msg, status=400)

    # Make sure the types are correct
    params['percentiles'] = [float(x) for x in params['percentiles']]
    params['scale'] = int(params['scale'][0])

    try:
        data = LM.get_histograms(event,metric,**params)
    except Exception as exc:
        msg = str(exc)
        return HttpResponse(msg, status=500)
    data = json.dumps(data)
    resp = HttpResponse(data,content_type='application/json')
    resp["Access-Control-Allow-Origin"] = "*"
    return resp

class Histograms2(View):
    LM =  None
    def get(self,request,event,metric):
        return _get_histograms(self.LM,request,event,metric)

class Histograms1(View):
    LM =  None
    def get(self,request,event):
        return _get_histograms(self.LM,request,event,None)

class Histograms0(View):
    LM =  None
    def get(self,request):
        return _get_histograms(self.LM,request,None,None)

def urlpatterns(LM):
    """
    Return a list of Django paths to be registered in the application.

    *LM*: a :py:class:`livemetrics.LiveMetrics` object
    """
    urlpatterns = [
        path('monitoring/v1/about', About.as_view(LM=LM),name='monitoring-about'),
        path('monitoring/v1/is_healthy', IsHealthy.as_view(LM=LM),name='monitoring-is_healthy'),
        path('monitoring/v1/is_ready', IsReady.as_view(LM=LM),name='monitoring-is_ready'),
        path('monitoring/v1/version', Version.as_view(LM=LM),name='monitoring-version'),

        path('monitoring/v1/metrics/meters/<event>/<result>/<metric>', Meters3.as_view(LM=LM),name='monitoring-meters3'),
        path('monitoring/v1/metrics/meters/<event>/<result>', Meters2.as_view(LM=LM),name='monitoring-meters2'),
        path('monitoring/v1/metrics/meters/<event>', Meters1.as_view(LM=LM),name='monitoring-meters1'),
        path('monitoring/v1/metrics/meters', Meters0.as_view(LM=LM),name='monitoring-meters0'),

        path('monitoring/v1/metrics/gauges/<object>/<metric>', Gauges2.as_view(LM=LM),name='monitoring-gauges2'),
        path('monitoring/v1/metrics/gauges/<object>', Gauges1.as_view(LM=LM),name='monitoring-gauges1'),
        path('monitoring/v1/metrics/gauges', Gauges0.as_view(LM=LM),name='monitoring-gauges0'),

        path('monitoring/v1/metrics/histograms/<event>/<metric>', Histograms2.as_view(LM=LM),name='monitoring-histograms2'),
        path('monitoring/v1/metrics/histograms/<event>', Histograms1.as_view(LM=LM),name='monitoring-histograms1'),
        path('monitoring/v1/metrics/histograms', Histograms0.as_view(LM=LM),name='monitoring-histograms0'),
    ]
    return urlpatterns
