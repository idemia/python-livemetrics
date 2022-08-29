
import os
import unittest
import time
import threading
import asyncio
import http.server
import requests
import aiohttp

from livemetrics.dashboard import dashboard

async def runner():
    app = dashboard.get_app()
    runner = aiohttp.web.AppRunner(app)
    await runner.setup()

    site = aiohttp.web.TCPSite(runner, '0.0.0.0', 9000,reuse_address=True)
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

from . import server
from . import client

#_______________________________________________________________________________
class TestDashboard(unittest.TestCase):
    
    def setUp(self):
        self.t = threading.Thread(target=run_server,args=(runner(),) , daemon=True)
        self.t.start()
        time.sleep(1.0)

        t = threading.Thread(target=server._serve, daemon=True)
        t.start()
        time.sleep(1.0)

        t = threading.Thread(target=client.inject, daemon=True)
        t.start()
        time.sleep(1.0)

    def tearDown(self):
        # Clean up to release the socket address for the other tests
        global LOOP
        LOOP.stop()

    def test_all(self):
        # Send some events
        with requests.get('http://localhost:9000/') as r:
            self.assertEqual(200,r.status_code)

        payload = {'server': 'http://localhost:7070/monitoring/v1/is_healthy'}
        with requests.get('http://localhost:9000/all', params=payload) as r:
            self.assertEqual(200,r.status_code)

        payload = {'server': 'http://localhost:7070/monitoring/missing'}
        with requests.get('http://localhost:9000/all', params=payload) as r:
            self.assertEqual(404,r.status_code)

        payload = {'server': 'http://localhost:7070/monitoring/v1/metrics/meters/test/ok'}
        with requests.get('http://localhost:9000/all', params=payload) as r:
            self.assertEqual(200,r.status_code)
            self.assertGreater(r.json()['count'],2)

        payload = {'server': 'http://localhost:7070/monitoring/v1/metrics/histograms'}
        with requests.get('http://localhost:9000/all', params=payload) as r:
            self.assertEqual(200,r.status_code)
            self.assertGreater(r.json()['values']['count'],2)

        payload = {'server': 'http://localhost:7070/monitoring/v1/metrics/gauges'}
        with requests.get('http://localhost:9000/all', params=payload) as r:
            self.assertEqual(200,r.status_code)
            self.assertGreater(r.json()['random']['count'],0)

# ______________________________________________________________________________
if __name__=='__main__':
    unittest.main(argv=['-v'])
