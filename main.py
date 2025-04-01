import mimetypes
import pathlib
from http.server import HTTPServer, BaseHTTPRequestHandler
import urllib.parse
import json
from datetime import datetime
import os
from jinja2 import Environment, FileSystemLoader


class HttpHandler(BaseHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        self.env = Environment(loader=FileSystemLoader('templates'))
        super().__init__(*args, **kwargs)

    def do_POST(self):
        data = self.rfile.read(int(self.headers['Content-Length']))
        print(data)
        data_parse = urllib.parse.unquote_plus(data.decode())
        print(data_parse)
        data_dict = {key: value for key, value in [
            el.split('=') for el in data_parse.split('&')]}
        print(data_dict)

        os.makedirs('storage', exist_ok=True)

        new_message = {
            str(datetime.now().strftime("%Y-%m-%d %H:%M:%S")): {
                "username": data_dict.get('username'),
                "message": data_dict.get('message')
            }
        }

        try:
            with open('storage/data.json', 'r') as file:
                messages = json.load(file)
        except (FileNotFoundError, json.JSONDecodeError):
            messages = {}

        messages.update(new_message)

        with open('storage/data.json', 'w') as file:
            json.dump(messages, file, indent=2)

        self.send_response(302)
        self.send_header('Location', '/read')
        self.end_headers()

    def do_GET(self):
        pr_url = urllib.parse.urlparse(self.path)
        if pr_url.path == '/':
            self.send_html_file('index.html')
        elif pr_url.path == '/message':
            self.send_html_file('message.html')
        elif pr_url.path == '/read':
            try:
                with open('storage/data.json', 'r') as file:
                    messages = json.load(file)
            except (FileNotFoundError, json.JSONDecodeError):
                messages = {}

            self.send_template('read.jinja', {'messages': messages})
        else:
            if pathlib.Path().joinpath(pr_url.path[1:]).exists():
                self.send_static()
            else:
                self.send_html_file('error.html', 404)

    def send_html_file(self, filename, status=200):
        self.send_response(status)
        self.send_header('Content-type', 'text/html')
        self.end_headers()
        with open(filename, 'rb') as fd:
            self.wfile.write(fd.read())

    def send_template(self, template_name, data={}, status=200):
        self.send_response(status)
        self.send_header('Content-type', 'text/html')
        self.end_headers()

        template = self.env.get_template(template_name)
        html = template.render(**data)
        self.wfile.write(html.encode())

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


def run(server_class=HTTPServer, handler_class=HttpHandler):
    server_address = ('', 3000)
    http = server_class(server_address, handler_class)
    try:
        print("Server started! On http://localhost:3000")
        http.serve_forever()
    except KeyboardInterrupt:
        http.server_close()


if __name__ == '__main__':
    run()
