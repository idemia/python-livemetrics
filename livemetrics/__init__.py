
"""
This module implements a utility to collect (efficiently) business
metrics showing the activity of an application.

For testing, we will reduce the tick interval

>>> import livemetrics.metrics
>>> livemetrics.metrics.Meter.TICK_INTERVAL = 0.1

First you need to create an object and to send an event:

>>> lm = LiveMetrics("version","about",lambda: True,lambda: True)
>>> lm.mark('start','ok')
>>> lm.mark('start','error')

This is enough to get a first set of metrics:

>>> import pprint
>>> pprint.pprint(lm.get_metrics()) #doctest: +ELLIPSIS
{'start': {'error': {'count': 1,
...
                     'rate1': 0.0,
                     'rate15': 0.0,
                     'rate5': 0.0},
           'ok': {'count': 1,
...
                  'rate1': 0.0,
                  'rate15': 0.0,
                  'rate5': 0.0}}}

We can now emit more events:

>>> import time
>>> time.sleep(0.02)
>>> lm.mark('start','ok')
>>> time.sleep(0.03)
>>> lm.mark('start','ok')
>>> lm.mark('start','error')
>>> time.sleep(0.2)
>>> round(lm.get_metrics()['start']['ok']['rate1'],2)
29.95
>>> round(lm.get_metrics()['start']['error']['rate1'],2)
19.97
>>> m = lm.get_metrics()
>>> m['start']['error']['rate1']<m['start']['error']['rate5']
True
>>> m['start']['error']['rate5']<m['start']['error']['rate15']
True
>>> m['start']['error']['rate1']<m['start']['ok']['rate1']
True
>>> m['start']['ok']['rate1']>29.0
True
>>> m['start']['error']['rate1']>19.0
True

For gauges, here is an example:

>>> lm = LiveMetrics("version","about", lambda: True, memory_and_cpu=False)
>>> lm.gauge('G',10)
>>> lm.gauge('G',15)
>>> lm.gauge('G',20)
>>> lm.gauge('G',12)

>>> print(lm.get_gauges())
{'G': {'min': 10, 'max': 20, 'count': 12}}

>>> print(lm.get_gauges('G'))
{'min': 10, 'max': 20, 'count': 12}

>>> print(lm.get_gauges('G','max'))
20

This module also provides a decorator to encapsulate a meter and a histogram.
Example:

>>> lm = LiveMetrics("version","about",lambda: True)
>>> @lm.timer('decorated','OK','EXC')
... def for_test(value,exc=False):
...     if exc: raise Exception("Exception")
...     time.sleep(0.1)
...     return value

Then, every time the function is called, new metrics are collected:

>>> for_test(1)
1
>>> for_test(2)
2
>>> for_test(3,True)
Traceback (most recent call last):
...
Exception: Exception

Metrics can be accessed using :py:meth:`LiveMetrics.get_metrics`:

>>> pprint.pprint(lm.get_metrics()) #doctest: +ELLIPSIS
{'decorated': {'EXC': {'count': 1,
...
                       'rate5': 0.0},
               'OK': {'count': 2,
...
                      'rate5': 10.0}}}

>>> pprint.pprint(lm.get_metrics('decorated')) #doctest: +ELLIPSIS
{'EXC': {'count': 1, 'mean': 0.0, 'rate1': 0.0, 'rate15': 0.0, 'rate5': 0.0},
 'OK': {'count': 2,
...
        'rate5': 10.0}}

>>> M = lm.get_metrics('decorated','OK')
>>> M['count']
2
>>> round(M['rate5'],1)
10.0

>>> lm.get_metrics('decorated','OK','count')
2

Event must be specified if result and metric are defined:
>>> lm.get_metrics(None,'OK','count')
Traceback (most recent call last):
...
SyntaxError: if metric/result is specified, event must also be specified
>>> lm.get_metrics('decorated',None,'count')
Traceback (most recent call last):
...
SyntaxError: if metric is specified, result must also be specified

Or :py:meth:`LiveMetrics.get_histograms`:

>>> H = lm.get_histograms()
>>> H['decorated']['count']
3
>>> round(H['decorated']['quantiles'][0.05],1)
0.1
>>> round(H['decorated']['stddev'],2)
0.05

>>> H = lm.get_histograms('decorated')
>>> H['count']
3
>>> round(H['quantiles'][0.05],1)
0.1
>>> round(H['stddev'],2)
0.05

>>> pprint.pprint(lm.get_histograms('decorated','count')) #doctest: +ELLIPSIS
3

>>> math.isclose(lm.get_histograms('decorated','quantiles')[0.05],0.05,rel_tol=0.01)
True

>>> pprint.pprint(lm.get_histograms('decorated','distribution',scale=1)) #doctest: +ELLIPSIS
[3]

"""

import os
import time
import collections
from functools import wraps
import asyncio

from livemetrics.metrics import *

__version__ = '0.4'
__author__ = "Olivier Heurtier"
__copyright__ = "IDEMIA"
__license__ = "CeCILL-C"

if os.name=='posix':
    def get_memory():
        # Retrieve memory usage from /proc/self/statm
        try:
            with open('/proc/self/statm','r') as f:
                return int(f.read().split(' ')[0]) *  os.sysconf('SC_PAGE_SIZE')
        except:
            return 0

    __CPU = None
    __CPU_RESULT = 0
    def get_cpu():
        # Retrieve CPU usage from /proc/self/stat
        global __CPU
        global __CPU_RESULT
        try:
            with open('/proc/self/stat','r') as f:
                # 14th value is the user time, 16th value is the user time for children
                # (note: 20th is the number of threads, could be useful)
                parts = f.read().split(' ')
                __NB_THREADS = int(parts[20-1])
                utime = (float(parts[14-1])+float(parts[16-1])) / os.sysconf('SC_CLK_TCK')
                now = time.time()
                if __CPU is None:
                    __CPU = (now,utime)
                    __CPU_RESULT = 0
                    return __CPU_RESULT

                # Getting 2 consecutive values very close can give bad value
                if now-__CPU[0] < 0.3:
                    return __CPU_RESULT
                result = (utime-__CPU[1])/(now-__CPU[0])
                __CPU = (now,utime)
                __CPU_RESULT = int(result*100)
                return __CPU_RESULT
        except:
            return 0

    def get_num_threads():
        try:
            with open('/proc/self/stat','r') as f:
                #  20th is the number of threads
                parts = f.read().split(' ')
                return int(parts[20-1])
        except:
            return 0

#______________________________________________________________________________
class LiveMetrics(object):
    """
    An object to be used as a singleton to aggregate all live metrics of an application.

    """

    def __init__(self,version,about,is_healthy,is_ready=None,memory_and_cpu=True):
        """
        Contructor.

        *version*: a string giving the version of the application

        *about*: a string describing the application

        *is_healthy*: a function called to know if the application is healthy or not.
        Function must have no parameter and return a boolean.

        *is_ready*: a function called to know if the application is ready to process requests or not.
        Function must have no parameter and return a boolean.
        If None is provided, *is_healthy* is used.
        
        *memory_and_cpu*: a flag to activate gauges to report the memory (``memory``),
        number of threads (``num_threads``) and CPU usage (``cpu``) on Linux only. Default is True.
        
        """
        self.version = version
        self.about = about
        self.is_healthy = is_healthy
        if not callable(self.is_healthy):
            self.is_healthy = lambda: is_healthy

        self.is_ready = is_ready
        if self.is_ready is None:
            self.is_ready = self.is_healthy
        if not callable(self.is_ready):
            self.is_ready = lambda: is_ready

        # Init the structure to receive the metrics
        self._meters = collections.defaultdict( lambda: collections.defaultdict(Meter) )
        self._gauges = collections.defaultdict( Gauge )
        self._histograms = collections.defaultdict( Histogram )

        if memory_and_cpu and os.name=='posix':
            self.gauge('memory',get_memory)
            self.gauge('cpu',get_cpu)
            self.gauge('num_threads',get_num_threads)

    def mark(self,event,result):
        """
        Mark the execution of an event **event** with the **result**.
        """
        self._meters[event][result].mark()

    def gauge(self,name,value):
        """
        Register a new gauge for this **name**. If **value** is a callable,
        it will be called everytime the gauge value is accessed.
        """
        self._gauges[name].mark(value)

    def histogram(self,name,value):
        """
        Register a new value in a histogram.
        """
        self._histograms[name].update(value)

    def timer(self,event,ok,error):
        """
        Decorator to automate meter and histogram on one event.

        *event*: the name of the event

        *ok*: value when the function decorated terminates successfully

        *error*: value when the function decorated terminates with an exception

        For each call of the decorated function, a call to :py:meth:`mark` is done for
        the *event* and result (*ok* or *error*), and a call to :py:meth:`histogram` is
        made to measure the processing time.

        *ok* and *error* can be callables that return a string compatible with json dictionary key

        .. warning::

            If applied on an async function decorated with aiohttp :py:meth:`web.RouteTableDef`, it must be
            placed between the aiohttp annotation and the async function. Otherwise the aiohttp route
            will be decorated and not the actual function.
        """

        def _f(f,event=event,ok=ok,error=error):
            @wraps(f)
            async def __asyncf(*args,**kw):
                S = time.time()
                try:
                    ret = await f(*args,**kw)
                    try:
                        if callable(ok):
                            self.mark(event,ok(ret))
                        elif ok is not None:
                            self.mark(event,ok)
                    except:
                        pass
                    E = time.time()
                    self.histogram(event,E-S)
                    return ret
                except Exception as exc:
                    try:
                        if callable(error):
                            self.mark(event,error(exc))
                        elif error is not None:
                            self.mark(event,error)
                    except:
                        pass   
                    E = time.time()
                    self.histogram(event,E-S)
                    raise

            @wraps(f)
            def __f(*args,**kw):
                S = time.time()
                try:
                    ret = f(*args,**kw)
                    try:
                        if callable(ok):
                            self.mark(event,ok(ret))
                        elif ok is not None:
                            self.mark(event,ok)
                    except:
                        pass
                    E = time.time()
                    self.histogram(event,E-S)
                    return ret
                except Exception as exc:
                    try:
                        if callable(error):
                            self.mark(event,error(exc))
                        elif error is not None:
                            self.mark(event,error)
                    except:
                        pass   
                    E = time.time()
                    self.histogram(event,E-S)
                    raise
            if asyncio.iscoroutinefunction(f):
                return __asyncf
            else:
                return __f
        return _f

    #
    # Access to the metrics
    #
    def get_metrics(self,event=None,result=None,metric=None):
        """
        Return a structure of dictionaries with the requested metrics.

        *event*: the name of the event

        *result*: the result of the event, as used in the call to :py:meth:`mark`

        *metric*: the name of the metric, one of ``mean``, ``count``, ``rate1``, ``rate5``, ``rate15``.

        If *metric* is not provided, all metrics are returned.

        If *result* is not provided, all results are returned.

        If *event* is not provided, all events are returned.
        """
        if event:
            # if event has not yet marked anything, it is not an error
            # we may request metrics, they will be null
            if event in self._meters:
                meters_dict = self._meters[event]
            else:
                # Build a temporary empty object (do not fail - maybe the meter will exist later)
                meters_dict = collections.defaultdict(Meter)
            if result:
                if metric:
                    return getattr(meters_dict[result],metric)
                else:
                    return meters_dict[result].to_dict()
            else:
                if metric:
                    raise SyntaxError('if metric is specified, result must also be specified')
                return { k:v.to_dict() for k,v in meters_dict.items() }
        else:
            if metric or result:
                raise SyntaxError('if metric/result is specified, event must also be specified')
            return {K:{ k:v.to_dict() for k,v in V.items()} for K,V in self._meters.items()}

    def get_gauges(self,name=None,metric=None):
        """
        Return a structure of dictionaries with the gauge metrics.

        *name*: the name of the gauge

        *metric*: the name of the metric, one of ``min``, ``max``, ``count``

        If *metric* is not provided, all metrics are returned.

        If *name* is not provided, all gauges are returned.
        """
        if name:
            if name in self._gauges:
                gauge = self._gauges[name]
            else:
                # Build a temporary empty object (do not fail - maybe the gauge will exist later)
                gauge = Gauge(0)
            if metric:
                return getattr(gauge,metric)
            return gauge.to_dict()
        else:
            return { k:v.to_dict() for k,v in self._gauges.items() }

    def get_histograms(self,event=None,metric=None,percentiles=[0.05, 0.25, 0.50, 0.75, 0.95],scale=10):
        """
        Return a structure of dictionaries with the histograms metrics.

        *event*: the name of the event

        *metric*: the name of the metric, one of ``count``, ``min``, ``max``, ``mean``, ``stddev``, ``quantiles``, ``distribution``

        *percentiles*: the list of percentiles for which the quantiles are returned

        *scale*: the resolution (number of values) of the returned distribution

        If *metric* is not provided, all metrics are returned.

        If *event* is not provided, all histograms are returned.
        """
        if event:
            if event in self._histograms:
                his = self._histograms[event]
            else:
                # Build a temporary empty object (do not fail - maybe the histogram will exist later)
                his = Histogram()
            data = {}
            if not metric:
                data.update(his.to_dict())
                snapshot = his.snapshot
                data['quantiles'] = {p:snapshot.get_value(p) for p in percentiles}
                data['distribution'] = snapshot.get_distribution(scale)
                return data
            elif metric=='quantiles':
                snapshot = his.snapshot
                data = {p:snapshot.get_value(p) for p in percentiles}
            elif metric=='distribution':
                snapshot = his.snapshot
                data = snapshot.get_distribution(scale)
            else:
                data = his.to_dict()[metric]
        else:
            D = {}
            for event in self._histograms.keys():
                his = self._histograms[event]
                data = {}
                data.update(his.to_dict())
                snapshot = his.snapshot
                data['quantiles'] = {p:snapshot.get_value(p) for p in percentiles}
                data['distribution'] = snapshot.get_distribution(scale)
                D[event] = data
            data = D
        return data

