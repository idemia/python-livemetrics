
import os
import unittest
import time
import threading
import http.server
import requests

from livemetrics.dashboard import dashboard

def _serve_dashboard():
    dashboard.main(['-i',os.path.join(os.path.dirname(__file__),'sample.yaml')])

from . import server
from . import client

#_______________________________________________________________________________
class TestDashboard(unittest.TestCase):
    
    def setUp(self):
        t = threading.Thread(target=_serve_dashboard, daemon=True)
        t.start()
        time.sleep(0.2)

        t = threading.Thread(target=server._serve, daemon=True)
        t.start()
        time.sleep(0.2)

        t = threading.Thread(target=client.inject, daemon=True)
        t.start()
        time.sleep(1.0)

    def test_all(self):
        # Send some events
        with requests.get('http://localhost:9000/') as r:
            self.assertEqual(200,r.status_code)

        payload = {'server': 'http://localhost:7070/monitoring/v1/is_healthy'}
        with requests.get('http://localhost:9000/all', params=payload) as r:
            self.assertEqual(200,r.status_code)

        payload = {'server': 'http://localhost:7070/monitoring/missing'}
        with requests.get('http://localhost:9000/all', params=payload) as r:
            self.assertEqual(500,r.status_code)

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
