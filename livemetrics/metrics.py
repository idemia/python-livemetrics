
# Inspired by https://metrics.dropwizard.io/4.0.0/

import math
import threading
import datetime
import random
import bisect

#______________________________________________________________________________
class Gauge(object):
    """
    A simple counter, registering a value and statistics (min and max) on this value.

    >>> g = Gauge(10)
    >>> g.mark(12)
    >>> g.min,g.count,g.max
    (10, 12, 12)

    >>> g.mark(8)
    >>> g.min,g.count,g.max
    (8, 8, 12)

    >>> g = Gauge()
    >>> g.mark(12)
    >>> g.min,g.count,g.max
    (12, 12, 12)

    >>> g.mark(8)
    >>> g.min,g.count,g.max
    (8, 8, 12)

    >>> g.mark(20)
    >>> g.min,g.count,g.max
    (8, 20, 20)

    >>> g.mark(15)
    >>> g.min,g.count,g.max
    (8, 15, 20)

    The alias ``value`` can also be used:

    >>> g.min,g.value,g.max
    (8, 15, 20)

    Any time, the value can be provided as a callable:

    >>> import random
    >>> g.mark(lambda: random.randrange(21,50))
    >>> g.count>20
    True

    The value can also be a callable from the start

    >>> g = Gauge(lambda: random.randrange(1,20))
    >>> g.mark(10)
    >>> g.min>=0,g.max<20
    (True, True)

    """

    def __init__(self,value=None):
        self.lock = threading.RLock()
        self._callable = None
        if callable(value):
            self._callable = value
            value = self._callable()
        self._value = value
        self._min = value
        self._max = value

    def mark(self,value):
        """
        Register a new value in the gauge and update the statistics.
        """
        with self.lock:
            if callable(value):
                self._callable = value
                value = self._callable()
            self._value = value
            self._min = min(self._min,value) if self._min else value
            self._max = max(self._max,value) if self._max else value

    @property
    def count(self):
        """
        Return the current value of the gauge.
        """
        if self._callable:
            self.mark(self._callable())
        return self._value

    @property
    def value(self):
        """
        Alias on :py:meth:`count`.
        """
        return self.count

    @property
    def min(self):
        """
        Return the minimum value ever registered in this gauge.
        """
        return self._min

    @property
    def max(self):
        """
        Return the maximum value ever registered in this gauge.
        """
        return self._max

    def to_dict(self):
        return dict(
            min=self.min,
            max=self.max,
            count=self.count
        )

#______________________________________________________________________________
class EWMA(object):
    """
    An exponentially-weighted moving average.
    See http://en.wikipedia.org/wiki/Moving_average#Exponential_moving_average

    Usage:

    >>> e = EWMA(1)
    >>> e.update()
    >>> import time
    >>> time.sleep(1)
    >>> e.update()
    >>> e._tick()
    >>> e.rate  #doctest: +ELLIPSIS
    0.39999...
    >>> e._tick()
    >>> e.rate  #doctest: +ELLIPSIS
    0.368017...
    """

    def __init__(self,nb_minutes=1,interval=5):
        self.initialized = False
        self._rate = 0.0

        self.uncounted = []
        self.alpha = 0.0
        self.interval = float(interval)*1000000.    # convert to microseconds
        self.alpha = 1.0 - math.exp(-interval / 60.0 / nb_minutes)

    def update(self,n=1):
        """
        Indicate an event has happened. *n* specifies the number of events.
        """
        self.uncounted.append(n)

    def _tick(self):
        # Mark the passage of time and decay the current rate accordingly.
        count = sum(self.uncounted)
        self.uncounted = []
        instantRate = count/self.interval
        if self.initialized:
            self._rate = self._rate + (self.alpha*(instantRate-self._rate))
        else:
            self._rate = instantRate
            self.initialized = True

    @property
    def rate(self):
        return self._rate*1000000.

#______________________________________________________________________________
class Meter(object):
    """
    An object measuring the rates of occurence of an event.
    Each event is reported with a call to :py:meth:`mark`. The rates are decayed as time
    goes by.

    For testing, we will reduce the tick interval managing the decaying of values.

    >>> Meter.TICK_INTERVAL = 0.1

    Then we create a new object:

    >>> mtr = Meter()

    At start, it is empty:

    >>> mtr.mean
    0.0

    Then if we mark an event:

    >>> mtr.mark()

    Mean is still 0 because there is no enough time difference to calculate it.

    >>> mtr.mean
    0.0

    Let's move forward in time:

    >>> import time
    >>> time.sleep(0.1)

    and report a second event:

    >>> mtr.mark()
    >>> mtr.mean>17 and mtr.mean<25
    True
    >>> mtr.count
    2
    >>> mtr.mark()
    >>> time.sleep(0.5)
    >>> 10.0-mtr.rate1<0.1,10.0-mtr.rate5<0.1,10.0-mtr.rate15<0.1
    (True, True, True)

    Rates decreases as time goes:

    >>> time.sleep(1.0)
    >>> 9.8-mtr.rate1<0.1,9.9-mtr.rate5<0.1,10.0-mtr.rate15<0.1
    (True, True, True)

    We marked 3 times in 2.1 seconds

    >>> round(mtr.mean,1)
    1.9
    """
    TICK_INTERVAL = 5

    def __init__(self):
        self.lock = threading.RLock()
        self.ewma1 = EWMA(1,self.TICK_INTERVAL)
        self.ewma5 = EWMA(5,self.TICK_INTERVAL)
        self.ewma15 = EWMA(15,self.TICK_INTERVAL)
        self._count = 0
        self.start = datetime.datetime.now()
        self.last_tick = datetime.datetime.now()

    def mark(self):
        """
        Indicate an event has just occurred.
        """
        with self.lock:
            self._tick_if_necessary()
            self._count += 1
            self.ewma1.update()
            self.ewma5.update()
            self.ewma15.update()

    def _tick_if_necessary(self):
        new_tick = datetime.datetime.now()
        age = new_tick - self.last_tick
        while age.seconds*1000.+age.microseconds/1000.>self.TICK_INTERVAL*1000.:
            self.last_tick += datetime.timedelta(seconds=self.TICK_INTERVAL)
            age = new_tick - self.last_tick
            self.ewma1._tick()
            self.ewma5._tick()
            self.ewma15._tick()

    @property
    def mean(self):
        """
        The number of events divided by the time the application is running.
        This gives a very rough estimation of the average number of events
        per seconds.
        """
        if self._count==0:
            return 0.0
        period = datetime.datetime.now()-self.start
        period = period.seconds*1.0 + period.microseconds/1000000.
        if period<=0.1:
            return 0.0            
        return self._count/period

    @property
    def count(self):
        """
        Return the number of events reported to this object since it was created.
        """
        return self._count

    @property
    def rate1(self):
        """
        Return the 1-minute moving average rate.
        """
        with self.lock:
            self._tick_if_necessary()
            return self.ewma1.rate

    @property
    def rate5(self):
        """
        Return the 5-minute moving average rate.
        """
        with self.lock:
            self._tick_if_necessary()
            return self.ewma5.rate

    @property
    def rate15(self):
        """
        Return the 15-minute moving average rate.
        """
        with self.lock:
            self._tick_if_necessary()
            return self.ewma15.rate

    def to_dict(self):
        return dict(
            mean=self.mean,
            count=self.count,
            rate1=self.rate1,
            rate5=self.rate5,
            rate15=self.rate15
        )

#______________________________________________________________________________
class WeightedSample(object):
    def __init__(self,value,weight):
        self.value = value
        self.weight = weight

    def __repr__(self):
        return "value={}; weight={}".format(self.value,self.weight)

class WeightedSnapshot(object):
    """
    A (weighted) snapshot, i.e. a copy of a set of values that have a weight.
    The weight is used to calculate the quantiles.

    This class is used by :py:class:`Histogram` and returned by :py:attr:`Histogram.snapshot`

    Example:

    >>> snapshot = WeightedSnapshot( {i:WeightedSample(i,i) for i in range(10)})

    Access the statistics of the values:

    >>> print((snapshot.min,snapshot.max,round(snapshot.mean,1),round(snapshot.stddev,1)))
    (0, 9, 6.3, 2.2)

    >>> print(snapshot.get_value(0.5))
    7.5

    >>> print(snapshot.get_value(-1))
    Traceback (most recent call last):
    ...
    Exception: argument -1 is not in [0..1]

    >>> print(snapshot.get_value(2))
    Traceback (most recent call last):
    ...
    Exception: argument 2 is not in [0..1]

    >>> print(snapshot.get_distribution(5))
    [2, 2, 2, 2, 2]

    >>> print(snapshot.size)
    10

    The snapshot can also be empty:

    >>> snapshot = WeightedSnapshot( {})
    >>> print((snapshot.min,snapshot.max,round(snapshot.mean,1),round(snapshot.stddev,1)))
    (0, 0, 0, 0)

    >>> print(snapshot.get_value(0.5))
    0.0

    """
    def __init__(self,values):
        copy = [v for v in values.values()]
        copy.sort(key=lambda x: x.value)

        sum_weight = sum([x.weight for x in copy])
        self.values = [x.value for x in copy]
        self.norm_weights = [x.weight/sum_weight if sum_weight!=0 else 0 for x in copy]
        self.quantiles = [0.0]*len(copy)
        for i in range(1,len(copy)):
            self.quantiles[i] = self.quantiles[i-1] + self.norm_weights[i-1]

    def get_value(self,quantile):
        """
        Access the value (the quantile) for a given percentile, i.e. the value that defines the
        boundary between the two segment [O,percentile] and  [percentile,1].

        The percentile must be between 0 and 1.

        """
        if quantile < 0.0 or quantile > 1.0 or quantile is None:
            raise Exception("argument %s is not in [0..1]" % quantile)

        if len(self.values)==0:
            return 0.0

        posx = bisect.bisect_left(self.quantiles,quantile)
        if posx<0:
            posx = ((-posx) - 1) - 1

        if posx<1:
            return self.values[0]

        if posx >= len(self.values):
            return self.values[-1]

        return (self.values[posx]+self.values[posx-1])/2

    def get_distribution(self,range_value=10):
        """
        Return the distribution with the request resolution (i.e. number of values)
        """
        H = []
        posy = 0
        step = (float(self.max)-float(self.min))/float(range_value)
        x = self.min + step
        while x<self.max:
            nposy = bisect.bisect_left(self.values,x)
            H.append(nposy-posy)
            posy = nposy
            x += step
        nposy = len(self.values)
        H.append(nposy-posy)
        return H

    @property
    def size(self):
        """
        Number of values in this snapshot.
        """
        return len(self.values)

    @property
    def max(self):
        """
        Maximum value in this snapshot.
        """
        if len(self.values)==0:
            return 0
        return self.values[-1]

    @property
    def min(self):
        """
        Minimum value in this snapshot.
        """
        if len(self.values)==0:
            return 0
        return self.values[0]

    @property
    def mean(self):
        """
        Weighted average of the values in this snapshot.
        """
        if len(self.values)==0:
            return 0
        return sum( [self.values[i]*self.norm_weights[i] for i in range(len(self.values)) ] )

    @property
    def stddev(self):
        """
        Standard deviation of the weighted values in this snapshot.
        """
        if len(self.values)<=1:
            return 0
        mean = self.mean
        variance = 0.0
        for i in range(len(self.values)):
            diff = self.values[i] - mean
            variance += self.norm_weights[i]*diff*diff
        return math.sqrt(variance)

class Reservoir(object):
    """
    A reservoir holds the data of an :py:class:`Histogram`.
    It records values and decays them as time passes.
    It keeps only a statistical representative set of values.
    """
    TICK_INTERVAL = 1.0*60*60     # 1 hour expressed in seconds

    def __init__(self):
        self.values = {}
        self.alpha = 0.015
        self._size = 1028
        self.count = 0
        self.start = datetime.datetime.now()
        self.last_tick = datetime.datetime.now()

    @property
    def size(self):
        return min(self._size,self.count)

    def update(self,value):
        self._tick_if_necessary()
        period = datetime.datetime.now()-self.start
        period = period.seconds*1.0 + period.microseconds/1000000.
        item_weight = math.exp(self.alpha*period)
        sample = WeightedSample(value, item_weight)
        priority = item_weight / random.random()
        self.count += 1
        if self.count<=self.size:
            self.values[priority] = sample
        else:
            first = min(self.values.keys())
            if first<priority:
                if not priority in self.values:
                    self.values[priority] = sample
                    del self.values[first]
                else:
                    self.values[priority] = sample

    def _tick_if_necessary(self):
        new_tick = datetime.datetime.now()
        age = new_tick - self.last_tick
        while age.seconds+age.microseconds/1000000.>self.TICK_INTERVAL:
            self.last_tick += datetime.timedelta(seconds=self.TICK_INTERVAL)
            age = new_tick - self.last_tick
            self.rescale()

    def rescale(self):
        period = self.TICK_INTERVAL
        scaling_factor = math.exp(-self.alpha * period)
        if math.isclose(scaling_factor,0.0):
            self.values = {}
        else:
            values = {}
            for k,v in self.values.items():
                new_sample = WeightedSample(v.value, v.weight * scaling_factor)
                if math.isclose(new_sample.weight,0.0):
                    continue
                values[k*scaling_factor] = new_sample
            self.values = values
        self.count = len(self.values)
        self.start += datetime.timedelta(seconds=self.TICK_INTERVAL)


    @property
    def snapshot(self):
        self._tick_if_necessary()
        return WeightedSnapshot(self.values)


class Histogram(object):
    """
    An histogram represents the distribution of a set of values.
    Values are exponentially decayed so that more recent values have more weight than old values.

    For testing, we will reduce the tick interval managing the decaying of values.

    >>> Reservoir.TICK_INTERVAL = 0.1

    Usage:

    >>> his = Histogram()

    A new object has no value yet:

    >>> his.count
    0

    For the test, we 
    Let's add 100 sequential values:

    >>> for i in range(100):
    ...    his.update(i+1)

    The ``snapshot`` object gives access to some statistics:

    >>> round(his.snapshot.mean,1)
    50.5
    >>> round(his.snapshot.stddev,1)
    28.9

    And to the value for a percentile:

    >>> round(his.snapshot.get_value(0.25),1)
    26.5

    >>> his.snapshot.get_distribution()
    [10, 10, 10, 10, 10, 10, 10, 10, 10, 10]

    >>> his.snapshot.get_distribution(20)
    [5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5]

    If we wait a little and inject new values:

    >>> import time
    >>> time.sleep(1.0)
    >>> for i in range(100):
    ...    his.update(i*2)

    >>> his.snapshot.get_distribution(20)
    [14, 15, 15, 15, 15, 15, 15, 15, 15, 15, 6, 5, 5, 5, 5, 5, 5, 5, 5, 5]
    >>> round(his.snapshot.get_value(0.25),1)
    34.0

    >>> time.sleep(1.0)
    >>> for i in range(100):
    ...    his.update(i*2)
    >>> his.snapshot.get_distribution(20)
    [19, 20, 20, 20, 20, 20, 20, 20, 20, 20, 11, 10, 10, 10, 10, 10, 10, 10, 10, 10]
    >>> round(his.snapshot.get_value(0.25),1)
    38.0

    The size of the reservoir is by default 1024. When the number of values is over this
    limit, values are randomly removed, older values first.

    >>> his50 = Histogram()
    >>> his50._reservoir._size = 50
    >>> for i in range(100):
    ...    his50.update(i+1)

    >>> his.snapshot.mean!=his50.snapshot.mean
    True
    >>> his.snapshot.stddev!=his50.snapshot.stddev
    True

    """

    def __init__(self):
        self.lock = threading.RLock()
        self._count = 0
        self._reservoir = Reservoir()

    def update(self,value):
        """
        Register a new value in the histogram.
        """
        with self.lock:
            self._count += 1
            self._reservoir.update(value)

    @property
    def count(self):
        """
        Get the number of values recorded by this histogram.
        """
        return self._count

    @property
    def snapshot(self):
        """
        Get a :py:class:`WeightedSnapshot` for this histogram. The snapshot will then give
        access to quantiles and to the distribution of values.
        """
        return self._reservoir.snapshot

    def to_dict(self):
        snapshot = self.snapshot
        return dict(
            count=self.count,
            min=snapshot.min,
            max=snapshot.max,
            mean=snapshot.mean,
            stddev=snapshot.stddev,
        )
