
import unittest
import time
import random
import threading
import json
import requests
import asyncio

import aiohttp
from aiohttp import web
routes = web.RouteTableDef()

import livemetrics
import livemetrics.publishers.aiohttp

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

@routes.get('/test')
@LM.timer("decorator_async","ok","error")
@LM.timer("decorator_async_callable",ok,error)
@LM.timer("decorator_async_histo_only",None,None)
@LM.timer("decorator_async_callable_exc",exc,exc)
async def get(request):
    time.sleep(random.random()/10.)
    LM.mark('test',"ok")
    LM.gauge('test',random.randrange(10,10000))
    LM.histogram("histo",random.random()*20)
    global COUNT
    COUNT += 1
    if COUNT % 3 ==0:
        raise Exception("false-alert")
    return web.Response(status=random.choice([200,500]))

async def runner():
    app = web.Application()
    app.add_routes(livemetrics.publishers.aiohttp.routes(LM))
    app.add_routes(routes)
    runner = web.AppRunner(app)
    await runner.setup()

    tests.publishers.PORT = '8766'
    site = web.TCPSite(runner, tests.publishers.IP, int(tests.publishers.PORT),reuse_address=True)
    await site.start()

def run_server(handler):
    global LOOP
    loop = asyncio.new_event_loop()
    LOOP = loop
    asyncio.set_event_loop(loop)
    loop.run_until_complete(handler)

    try:
        loop.run_forever()
    finally:
        loop.run_until_complete(loop.shutdown_asyncgens())
        loop.close()

#_______________________________________________________________________________
class TestAioHttp(tests.publishers.TestPublisher):
    
    def setUp(self):
        self.t = threading.Thread(target=run_server,args=(runner(),) , daemon=False)
        self.t.start()
        time.sleep(0.2)
        self.LM = LM

    def tearDown(self):
        # Clean up to release the socket address for the other tests
        global LOOP
        LOOP.stop()
            
# ______________________________________________________________________________
if __name__=='__main__':
    unittest.main(argv=['-v'])
