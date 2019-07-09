
import unittest
import time
import random
import threading

import requests

import livemetrics
import livemetrics.publishers.flask

from flask import Flask
from flask import request

app = Flask(__name__)

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

@app.route('/test')
@LM.timer("decorator_async","ok","error")
@LM.timer("decorator_async_callable",ok,error)
@LM.timer("decorator_async_histo_only",None,None)
@LM.timer("decorator_async_callable_exc",exc,exc)
def get():
    time.sleep(random.random()/10.)
    LM.mark('test',"ok")
    LM.gauge('test',random.randrange(10,10000))
    LM.histogram("histo",random.random()*20)
    global COUNT
    COUNT += 1
    if COUNT % 3 ==0:
        raise Exception("false-alert")
    return "ok" #web.Response(status=random.choice([200,500]))

def shutdown_server():
    func = request.environ.get('werkzeug.server.shutdown')
    if func is None:
        raise RuntimeError('Not running with the Werkzeug Server')
    func()

@app.route('/shutdown', methods=['POST'])
def shutdown():
    shutdown_server()
    return 'Server shutting down...'

def _serve():
    global LM
    tests.publishers.PORT = '8767'
    global app
    app.register_blueprint(livemetrics.publishers.flask.blueprint(LM))
    app.run(host=tests.publishers.IP, port=int(tests.publishers.PORT))

#_______________________________________________________________________________
class TestFlask(tests.publishers.TestPublisher):
    
    def setUp(self):
        self.t = threading.Thread(target=_serve , daemon=False)
        self.t.start()
        time.sleep(0.2)
        self.LM = LM

    def tearDown(self):
        # Clean up to release the socket address for the other tests
        requests.post('http://'+tests.publishers.IP+':'+tests.publishers.PORT+'/shutdown')

            
# ______________________________________________________________________________
if __name__=='__main__':
    unittest.main(argv=['-v'])
