
import os
import time
import unittest
import requests

IP = '127.0.0.1'
PORT = '8765'

#_______________________________________________________________________________
class TestPublisher(unittest.TestCase):
    
    def test_a(self):
        # Send some events
        requests.get('http://'+IP+':'+PORT+'/test')
        requests.get('http://'+IP+':'+PORT+'/test')
        requests.get('http://'+IP+':'+PORT+'/test')
        requests.get('http://'+IP+':'+PORT+'/test')
        requests.get('http://'+IP+':'+PORT+'/test')

        # Get the application status
        with requests.get('http://'+IP+':'+PORT+'/monitoring/v1/about') as r:
            self.assertEqual(b'Test server',r.content)
        with requests.get('http://'+IP+':'+PORT+'/monitoring/v1/version') as r:
            self.assertEqual('1.0',r.json()['version'])
        with requests.get('http://'+IP+':'+PORT+'/monitoring/v1/is_healthy') as r:
            self.assertEqual(200,r.status_code)
        with requests.get('http://'+IP+':'+PORT+'/monitoring/v1/is_ready') as r:
            self.assertEqual(200,r.status_code)

        # Meters
        with requests.get('http://'+IP+':'+PORT+'/monitoring/v1/metrics/meters') as r:
            self.assertEqual(5,r.json()['test']['ok']['count'])
        with requests.get('http://'+IP+':'+PORT+'/monitoring/v1/metrics/meters/test') as r:
            self.assertEqual(5,r.json()['ok']['count'])
        with requests.get('http://'+IP+':'+PORT+'/monitoring/v1/metrics/meters/test/ok') as r:
            self.assertEqual(5,r.json()['count'])
        with requests.get('http://'+IP+':'+PORT+'/monitoring/v1/metrics/meters/test/ok/count') as r:
            self.assertEqual(5,r.json())
        # Missing meter
        with requests.get('http://'+IP+':'+PORT+'/monitoring/v1/metrics/meters/missing/ok/count') as r:
            self.assertEqual(0,r.json())
    
        # Gauges
        with requests.get('http://'+IP+':'+PORT+'/monitoring/v1/metrics/gauges') as r:
            self.assertEqual(10,r.json()['fixed']['count'])
        with requests.get('http://'+IP+':'+PORT+'/monitoring/v1/metrics/gauges/fixed') as r:
            self.assertEqual(10,r.json()['count'])
        with requests.get('http://'+IP+':'+PORT+'/monitoring/v1/metrics/gauges/fixed/count') as r:
            self.assertEqual(10,r.json())
        # Missing gauge
        with requests.get('http://'+IP+':'+PORT+'/monitoring/v1/metrics/gauges/missing/count') as r:
            self.assertEqual(0,r.json())
    
        # Histograms
        with requests.get('http://'+IP+':'+PORT+'/monitoring/v1/metrics/histograms') as r:
            self.assertGreater(20,r.json()['histo']['quantiles']['0.5'])
        with requests.get('http://'+IP+':'+PORT+'/monitoring/v1/metrics/histograms/histo') as r:
            self.assertGreater(20,r.json()['quantiles']['0.5'])
        with requests.get('http://'+IP+':'+PORT+'/monitoring/v1/metrics/histograms/histo/quantiles?percentiles=0.5') as r:
            self.assertGreater(20,r.json()['0.5'])
        with requests.get('http://'+IP+':'+PORT+'/monitoring/v1/metrics/histograms/histo/distribution?scale=1') as r:
            self.assertGreater(r.json()[0],3)
        with requests.get('http://'+IP+':'+PORT+'/monitoring/v1/metrics/histograms/histo/count') as r:
            self.assertEqual(5,r.json())
        with requests.get('http://'+IP+':'+PORT+'/monitoring/v1/metrics/histograms/histo/count?bad_param=2') as r:
            self.assertEqual(400,r.status_code)
            self.assertEqual(b"Invalid query parameters: bad_param",r.content)
        # Missing histogram
        with requests.get('http://'+IP+':'+PORT+'/monitoring/v1/metrics/histograms/missing/count') as r:
            self.assertEqual(0,r.json())
    
        # Histograms with errors
        with requests.get('http://'+IP+':'+PORT+'/monitoring/v1/metrics/histograms/histo/quantiles?bad_param=0.5&bad2=1') as r:
            self.assertEqual(400,r.status_code)
            self.assertEqual(b"Invalid query parameters: bad2, bad_param",r.content)
        with requests.get('http://'+IP+':'+PORT+'/monitoring/v1/metrics/histograms/histo/quantiles?percentiles=0.5&percentiles=0.75&bad_param=0.5') as r:
            self.assertEqual(400,r.status_code)
        with requests.get('http://'+IP+':'+PORT+'/monitoring/v1/metrics/histograms/histo/bad_metric') as r:
            self.assertEqual(400,r.status_code)

        # Test the decoration works
        with requests.get('http://'+IP+':'+PORT+'/monitoring/v1/metrics/meters/decorator_async/ok') as r:
            self.assertEqual(4,r.json()['count'])
        with requests.get('http://'+IP+':'+PORT+'/monitoring/v1/metrics/meters/decorator_async/error') as r:
            self.assertEqual(1,r.json()['count'])

        # Additional error cases
        with requests.get('http://'+IP+':'+PORT+'/bad/path/v1/metrics/histograms/histo/bad_metric') as r:
            self.assertEqual(404,r.status_code)

        # Test with a bad status
        backup_ih = self.LM.is_healthy
        self.LM.is_healthy = lambda: False

        backup_ir = self.LM.is_ready
        self.LM.is_ready = lambda: False

        with requests.get('http://'+IP+':'+PORT+'/monitoring/v1/is_healthy') as r:
            self.assertEqual(500,r.status_code)
        with requests.get('http://'+IP+':'+PORT+'/monitoring/v1/is_ready') as r:
            self.assertEqual(500,r.status_code)

        self.LM.is_healthy = backup_ih
        self.LM.is_ready = backup_ir

        # Test memory & CPU
        if not os.name=='posix':
            return

        with requests.get('http://'+IP+':'+PORT+'/monitoring/v1/metrics/gauges/memory/count') as r:
            self.assertGreater(r.json(),20000000)

        with requests.get('http://'+IP+':'+PORT+'/monitoring/v1/metrics/gauges/num_threads/count') as r:
            self.assertGreater(r.json(),2)
            self.assertLess(r.json(),10)

        with requests.get('http://'+IP+':'+PORT+'/monitoring/v1/metrics/gauges/cpu/count') as r:
            cpu = r.json()
        with requests.get('http://'+IP+':'+PORT+'/monitoring/v1/metrics/gauges/cpu/count') as r:
            self.assertEqual(cpu,r.json())
        time.sleep(0.5)
        requests.get('http://'+IP+':'+PORT+'/monitoring/v1/metrics/gauges/cpu/count')
