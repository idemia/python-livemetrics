
import time
import unittest
import requests
import json
import math

#_______________________________________________________________________________
class TestPublisher(unittest.TestCase):
    
    def assertEqualFloat(self,a,b,msg=None):
        # We want less than 1.5% of delta between the 2 values
        if math.fabs(a)<0.00001 and math.fabs(b)<0.00001:
            # both are null
            return
        if math.fabs(b)>=0.00001:
            r = a/b
        else:
            r = b/a
        if r<0.985 or r>1.015:
            self.fail(self._formatMessage(msg, "{} != {} (error: {}%)".format(a,b,round(r,3)*100)))

    def assertEqualQuantile(self,a,b,msg=None):
        if math.fabs(b-a)>1.0:
            self.fail(self._formatMessage(msg, "{} != {}".format(a,b)))

    def _validate(self):
        rJ = requests.get('http://localhost:8080/metrics').json()
        rP = requests.get('http://localhost:7070/monitoring/v1/metrics/meters').json()
        self.assertEqual(rJ['meters']['requests']['count'] , rP['test']['ok']['count'])
        self.assertEqualFloat(rJ['meters']['requests']['m1_rate'] , rP['test']['ok']['rate1'])
        self.assertEqualFloat(rJ['meters']['requests']['m5_rate'] , rP['test']['ok']['rate5'])
        self.assertEqualFloat(rJ['meters']['requests']['m15_rate'] , rP['test']['ok']['rate15'])

        rP = requests.get('http://localhost:7070/monitoring/v1/metrics/histograms').json()
        self.assertEqual(rJ['histograms']['values']['count'] , rP['values']['count'])
        self.assertEqualFloat(rJ['histograms']['values']['mean'] , rP['values']['mean'])
        self.assertEqualQuantile(rJ['histograms']['values']['p95'] , rP['values']['quantiles']['0.95'])
        self.assertEqualQuantile(rJ['histograms']['values']['p75'] , rP['values']['quantiles']['0.75'])
        self.assertEqualQuantile(rJ['histograms']['values']['p50'] , rP['values']['quantiles']['0.5'])

    def test_a(self):
        self.addTypeEqualityFunc(float,"assertEqualFloat")
        self.addTypeEqualityFunc(float,"assertEqualQuantile")

        # Send some events
        requests.get('http://localhost:8080/test/10')
        requests.get('http://localhost:7070/test/10')
        time.sleep(0.1)

        self._validate()

        for y in range(5):
            time.sleep(1.0)

            for x in range(20):
                requests.get('http://localhost:8080/test/'+str(y*25+x))
                requests.get('http://localhost:7070/test/'+str(y*25+x))
                time.sleep(0.1)

            self._validate()

# ______________________________________________________________________________
if __name__=='__main__':
    unittest.main(argv=['-v'])

