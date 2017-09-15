#!/usr/bin/env python3

from http.server import BaseHTTPRequestHandler, HTTPServer
import argparse
from slackwebhook import slackWebHook
import urllib.request
import json

def MakeHandlerClassFromArgv(init_args):
    class PingAdminRequestHandler(BaseHTTPRequestHandler):
        def __init__(self, *args, **kwargs):
             self.args = init_args
             super(PingAdminRequestHandler, self).__init__(*args, **kwargs)

        def gettaskinfo(self, tasknumber=''):
            # perform query to api
            defaultParams = '?a=api&sa=tasks&api_key={}'
            query = defaultParams.format(self.apikey)
            if tasknumber:
                query = query + '&task_id=' + tasknumber
            with urllib.request.urlopen(self.apihost + query) as f:
                rawasnwer = f.read()
            try:
                answer = rawasnwer.decode('utf8')
            except UnicodeDecodeError:
                answer = rawasnwer.decode('cp1251')
            return json.loads(answer)

        # GET
        def do_GET(self):
            self.apikey = self.args.pingadmin_apikey
            self.answer = self.args.pingadmin_answer
            self.secret = self.args.pingadmin_secret
            self.apihost = "https://ping-admin.ru/"
            self.slackcli = slackWebHook(self.args.slackurl, 'pingadmin', ':pingpong:')

            params = self.path.split('?')
            if len(params) == 1:
                self.pong()
                return 0
            reportstring = params[1]
            reportinfo = {}
            for pair in reportstring.split('&'):
                reportinfo[pair.split('=')[0]] = pair.split('=')[1]

            if 'skey' in reportinfo.keys():
                if reportinfo['skey'] == self.secret:
                    self.processError(reportinfo)
                    self.send_response(200)
                    self.logmessage("processing error")
                else:
                    self.send_response(403)
                    self.logmessage("secrets doesn't match!")
            else:
                self.processError(reportinfo)
                self.send_response(200)
                self.logmessage("processing error")

            # Send headers
            self.send_header('Content-type','text/html')
            self.end_headers()
            self.wfile.write(bytes(self.answer, "utf8"))

            return 0

        def do_HEAD(self):
            # Send response status code
            self.send_response(200)

            # Send headers
            self.send_header('Content-type','text/html')
            self.end_headers()
            return 0

        def processError(self, notifyinfo):
            self.taskinfo = self.gettaskinfo(notifyinfo['id'])
            print(self.taskinfo)
            if len(self.taskinfo) == 1:
                servicename = self.taskinfo[0]['nazv']
            else:
                self.log_message('something went wrong')
                return 1

            attachment = [{}]
            if notifyinfo['status'] != 'OK':
                attachment[0]['color'] = 'danger'
                msg = '{} is unavailable'.format(servicename)
                attachment[0]['text'] = msg
            else:
                attachment[0]['color'] = 'good'
                msg = '{} is OK'.format(servicename)
                attachment[0]['text'] = msg

            self.slackcli.send(attachment=attachment)

        def pong(self):
            # Send response status code
            self.send_response(200)
            # Send headers
            self.send_header('Content-type','text/html')
            self.end_headers()
            self.wfile.write(bytes(self.answer, "utf8"))
            return 0

        def logmessage(self, message):
            print(message)
            return 0

    return PingAdminRequestHandler

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("-a", "--address", type=str, default='127.0.0.1',
                        help="ip address to listen, default=127.0.0.1")
    parser.add_argument("-p", "--port", type=int, default='8081',
                        help='port to listen, default=8081')
    parser.add_argument("--slackurl", type=str, help="slack webhook url")
    parser.add_argument("--service", type=str, help="service to integrate")
    parser.add_argument("--pingadmin-apikey", type=str)
    parser.add_argument("--pingadmin-secret", type=str)
    parser.add_argument("--pingadmin-answer", type=str)
    args = parser.parse_args()
    print('starting server...')
    # Server settings
    # Choose port 8080, for port 80, which is normally used for a http server, you need root access
    HandlerClass = MakeHandlerClassFromArgv(args)
    server_address = (args.address, args.port)
    httpd = HTTPServer(server_address, HandlerClass)
    print('running server...')
    httpd.serve_forever()

if __name__ == "__main__":
    main()
