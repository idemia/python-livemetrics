
import http.server

import livemetrics
import livemetrics.publishers.http

import tests.publishers

LM = livemetrics.LiveMetrics('{"version":"1.0"}',"Test server",True, True)

#______________________________________________________________________________
class TestHTTPRequestHandler(livemetrics.publishers.http.HTTPRequestHandler):

    def do_GET(self):
        if self.path.startswith('/test'):
            value = int(self.path.split('/')[-1])
            LM.mark('test',"ok")
            LM.histogram("values",value)
            self.send_response(200)
            self.end_headers()
        else:
            return super().do_GET()

def _serve():
    global LM
    server_address = ('0.0.0.0', 7070)
    httpd = http.server.HTTPServer(server_address, lambda r,a,s: TestHTTPRequestHandler(LM,r,a,s))
    httpd.allow_reuse_address = True
    httpd.serve_forever()

# ______________________________________________________________________________
if __name__=='__main__':
    _serve()

