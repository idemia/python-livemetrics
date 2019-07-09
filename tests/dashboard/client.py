
import time
import requests
import json
import random

def inject():
    # Send some events
    for y in range(5):
        time.sleep(0.5)

        for x in range(20):
            requests.get('http://localhost:7070/test/'+str(y*25+x))

    for y in range(10,15):
        for x in range(30):
            requests.get('http://localhost:7070/test/'+str(y*25+x))

    for x in range(100):
        requests.get('http://localhost:7070/test/'+str(random.randrange(300)))


# ______________________________________________________________________________
if __name__=='__main__':
    inject()

