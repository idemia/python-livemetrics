
import threading
import unittest
import random
import time

import django
from django.http import HttpResponse
from django.urls import path
from django.core.management import call_command

import livemetrics
import livemetrics.publishers.django

import tests.publishers

LM = livemetrics.LiveMetrics('{"version":"1.0"}',"Test server",True, True)
# Sample of gauges
LM.gauge('fixed',10)
LM.gauge('test',10)
LM.gauge('call',lambda: random.randrange(100,1000))

#______________________________________________________________________________
def ok(ret):
    return str(ret.status)

def error(exc):
    return str(exc)

def exc(ret):
    raise Exception("Bad status")

COUNT = 0

@LM.timer("decorator_async","ok","error")
@LM.timer("decorator_async_callable",ok,error)
@LM.timer("decorator_async_histo_only",None,None)
@LM.timer("decorator_async_callable_exc",exc,exc)
def myview(request):
    time.sleep(random.random()/10.)
    global LM
    LM.mark('test',"ok")
    LM.gauge('test',random.randrange(10,10000))
    LM.histogram("histo",random.random()*20)
    global COUNT
    COUNT += 1
    if COUNT % 3 ==0:
        raise Exception("false-alert")
    return HttpResponse("OK")

urlpatterns = [
    path('test', myview, name='test'),
]

urlpatterns += livemetrics.publishers.django.urlpatterns(LM)

def _serve():
    from django.conf import settings

    global LM
    tests.publishers.PORT = '8768'

    if not settings.configured:
        # Configure test environment
        settings.configure(
            DATABASES={
                'default': {
                    'ENGINE': 'django.db.backends.sqlite3',
                    'NAME': ':memory:'
                }
            },
            INSTALLED_APPS=(
                'tests.publishers.test_django',
            ),
            ALLOWED_HOSTS = ['*'],
            ROOT_URLCONF='tests.publishers.test_django',
            MIDDLEWARE_CLASSES=(),
            TEMPLATES = [],
            LOGGING = {
                'version': 1,
                'disable_existing_loggers': True,
            },
        )

    django.setup()
    call_command('runserver',int(tests.publishers.PORT),use_reloader=False)

#_______________________________________________________________________________
class TestDjango(tests.publishers.TestPublisher):
    
    def setUp(self):
        global LM
        self.t = threading.Thread(target=_serve , daemon=True)
        self.t.start()
        time.sleep(0.2)
        self.LM = LM

# ______________________________________________________________________________
if __name__=='__main__':
    unittest.main(argv=['-v'])
