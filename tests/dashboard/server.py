
import http.server
import random
import time

import livemetrics
import livemetrics.publishers.http

LM = livemetrics.LiveMetrics('{"version":"1.0"}',"Test server",True, True)

LM.gauge("random",lambda: random.randint(1,10))

#______________________________________________________________________________
class TestHTTPRequestHandler(livemetrics.publishers.http.HTTPRequestHandler):

    @LM.timer("time",None,None)
    def do_test(self):
        value = int(self.path.split('/')[-1])
        LM.mark('test','ok')
        if value % 5 == 0:
            LM.mark('test','error')
        LM.histogram("values",value)
        time.sleep(random.triangular(0.1,0.2,0.4))
        self.send_response(200)
        self.end_headers()

    def do_GET(self):
        if self.path.startswith('/test'):
            return self.do_test()
        else:
            return super().do_GET()

    def log_message(self, format, *args):
        pass

def _serve():
    global LM
    server_address = ('0.0.0.0', 7070)
    httpd = http.server.HTTPServer(server_address, lambda r,a,s: TestHTTPRequestHandler(LM,r,a,s))
    httpd.allow_reuse_address = True
    httpd.serve_forever()

# ______________________________________________________________________________
if __name__=='__main__':
    _serve()

