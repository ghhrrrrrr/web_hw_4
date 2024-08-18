from datetime import datetime
import json
from threading import Thread
from http.server import HTTPServer, BaseHTTPRequestHandler
import pathlib
import urllib.parse
import mimetypes
import socket


class HttpHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        pr_url = urllib.parse.urlparse(self.path)
        if pr_url.path == '/':
            self.send_html_file('templates/index.html')
        elif pr_url.path == '/message':
            self.send_html_file('templates/message.html') 
        else:
            if pathlib.Path().joinpath(pr_url.path[1:]).exists():
                self.send_static()
            else:
                self.send_html_file('templates/error.html', 404)

    def do_POST(self):
        data = self.rfile.read(int(self.headers['Content-Length']))
        print(data)
        data_parse = urllib.parse.unquote_plus(data.decode())
        print(data_parse)
        data_dict = {key: value for key, value in [el.split('=') for el in data_parse.split('&')]}
        print(data_dict)

        send_message_to_socket_server(data_dict)

        self.send_response(302)
        self.send_header('Location', '/')
        self.end_headers()


    def send_static(self):
        self.send_response(200)
        mt = mimetypes.guess_type(self.path)
        if mt:
            self.send_header("Content-type", mt[0])
        else:
            self.send_header("Content-type", 'text/plain')
        self.end_headers()
        with open(f'.{self.path}', 'rb') as file:
            self.wfile.write(file.read())


    def send_html_file(self, filename, status=200):
        self.send_response(status)
        self.send_header('Content-type', 'text/html')
        self.end_headers()
        with open(filename, 'rb') as fd:
            self.wfile.write(fd.read())

def send_message_to_socket_server(data):
    UDP_IP = "127.0.0.1"
    UDP_PORT = 5000
    MESSAGE = json.dumps(data).encode()

    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.sendto(MESSAGE, (UDP_IP, UDP_PORT))

def run_http_server():
    server_address = ('localhost', 3000)
    http = HTTPServer(server_address, HttpHandler)
    try:
        http.serve_forever()
    except KeyboardInterrupt:
        http.server_close()

def run_socket_server():
    UDP_IP = "127.0.0.1"
    UDP_PORT = 5000

    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.bind((UDP_IP, UDP_PORT))

    data_file = 'storage/data.json'

    while True:
        data, addr = sock.recvfrom(1024)
        message = json.loads(data.decode())
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S.%f')
        with open(data_file, 'r') as f:
            all_data = json.load(f)
        all_data[timestamp] = message
        with open(data_file, 'w') as f:
            json.dump(all_data, f, indent=4)


if __name__ == '__main__':
    http_thread = Thread(target=run_http_server)
    socket_thread = Thread(target=run_socket_server)

    http_thread.start()
    socket_thread.start()

    http_thread.join()
    socket_thread.join()