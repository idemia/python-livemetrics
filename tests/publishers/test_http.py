
import unittest
import time
import random
import threading
import json
import requests
import http.server

import livemetrics
import livemetrics.publishers.http

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

#______________________________________________________________________________
class TestHTTPRequestHandler(livemetrics.publishers.http.HTTPRequestHandler):

    @LM.timer("decorator_async","ok","error")
    @LM.timer("decorator_async_callable",ok,error)
    @LM.timer("decorator_async_histo_only",None,None)
    @LM.timer("decorator_async_callable_exc",exc,exc)
    def _doit(self):
        time.sleep(random.random()/10.)
        LM.mark('test',"ok")
        LM.gauge('test',random.randrange(10,10000))
        LM.histogram("histo",random.random()*20)
        global COUNT
        COUNT += 1
        if COUNT % 3 ==0:
            raise Exception("false-alert")

    def do_GET(self):
        if self.path=='/test':
            try:
                self._doit()
                self.send_response(200)
                self.end_headers()
            except:
                self.send_response(500)
                self.end_headers()
        else:
            return super().do_GET()

    def log_message(self, format, *args):
        pass
        
def _serve():
    global LM
    tests.publishers.PORT = '8765'
    server_address = (tests.publishers.IP, int(tests.publishers.PORT))
    httpd = http.server.HTTPServer(server_address, lambda r,a,s: TestHTTPRequestHandler(LM,r,a,s))
    global HTTPD
    HTTPD = httpd
    httpd.allow_reuse_address = True
    httpd.serve_forever()

#_______________________________________________________________________________
class TestHttp(tests.publishers.TestPublisher):
    
    def setUp(self):
        t = threading.Thread(target=_serve, daemon=False)
        t.start()
        time.sleep(0.2)
        self.LM = LM

    def tearDown(self):
        # Clean up to release the socket address for the other tests
        global HTTPD
        HTTPD.shutdown()

# ______________________________________________________________________________
if __name__=='__main__':
    unittest.main(argv=['-v'])
