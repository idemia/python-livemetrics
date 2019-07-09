import time
import unittest
import requests
import json
import math
import statistics

from livemetrics.metrics import *

#_______________________________________________________________________________
class TestMetrics(unittest.TestCase):
    
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

    def test_simple(self):
        self.maxDiff = None
        his = Histogram()
        l = [10, 10, 10, 0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19]
        for x in l:
            his.update(x)
        self.assertEqual(l,[x.value for x in his._reservoir.values.values()])
        self.assertEqualFloat(statistics.mean(l),his.snapshot.mean)
        self.assertEqualFloat(statistics.pstdev(l),his.snapshot.stddev)
        self.assertEqualFloat(statistics.median(l),his.snapshot.get_value(0.5))

    def test_histograms(self):
        self.maxDiff = None
        his = Histogram()
        l = [0,1,2,3,4,5,6,7,8,9,10,11,12,13,14,15,16,17,18,19,25,26,27,28,29,30,31,32,33,34,35,36,37,38,
            39,40,41,42,43,44,50,51,52,53,54,55,56,57,58,59,60,61,62,63,64,65,66,67,68,69,75,76,77,78,79,
            80,81,82,83,84,85,86,87,88,89,90,91,92,93,94,100,101,102,103,104,105,106,107,108,109,110,111,112,113,114,115,116,117,118,119]
        for x in l:
            his.update(x)
        self.assertEqual(l,[x.value for x in his._reservoir.values.values()])
        self.assertEqualFloat(statistics.mean(l),his.snapshot.mean)
        self.assertEqualFloat(statistics.pstdev(l),his.snapshot.stddev)
        self.assertEqualQuantile(statistics.median(l),his.snapshot.get_value(0.5))

        self.assertEqual(0,his.snapshot.min)
        self.assertEqual(119,his.snapshot.max)
        self.assertEqual(100,his.snapshot.size)
        #self.assertEqual(61.57,round(his.snapshot.mean,2))
        self.assertEqualFloat(35.93,his.snapshot.stddev)
        self.assertEqualQuantile(61.5,round(his.snapshot.get_value(0.5),1))


# ______________________________________________________________________________
if __name__=='__main__':
    unittest.main(argv=['-v'])

