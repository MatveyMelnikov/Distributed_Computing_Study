import argparse
import urllib.request
import urllib.error
from http.server import ThreadingHTTPServer, BaseHTTPRequestHandler


class WebServerHandler(BaseHTTPRequestHandler):
    app_url = None

    def log_message(self, *_):
        pass

    def do_POST(self):
        length = int(self.headers.get("Content-Length", 0))
        body = self.rfile.read(length)
        print(f"[WEB SERVER] forwarding POST -> {self.app_url}")

        req = urllib.request.Request(
            self.app_url, data=body,
            headers={"Content-Type": "application/json"}, method="POST")
        try:
            with urllib.request.urlopen(req) as r:
                status, data = r.status, r.read()
        except urllib.error.HTTPError as e:
            status, data = e.code, e.read()
        except urllib.error.URLError:
            status = 502
            data = b'{"error":"app_server_unreachable"}'

        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)


class ReusableHTTPServer(ThreadingHTTPServer):
    allow_reuse_address = True


def parse_args(argv=None):
    p = argparse.ArgumentParser()
    p.add_argument(
        "--app-url",
        required=True,
        help="e.g. http://127.0.0.1:8001/")
    p.add_argument(
        "--host",
        default="127.0.0.1",
        help="interface to lsten"
    )
    p.add_argument(
        "--port",
        type=int,
        default=8000,
        help="port to listen on"
    )
    return p.parse_args(argv)


def main(argv=None):
    args = parse_args(argv)

    handler = type(
        "WebHandler",
        (WebServerHandler,),
        {"app_url": args.app_url}
    )
    server = ReusableHTTPServer((args.host, args.port), handler)
    print(f"[WEB SERVER] listening on http://{args.host}:{args.port}")
    print(f"[WEB SERVER] proxying to {args.app_url}")

    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\n[WEB SERVER] shutting down")
    finally:
        server.server_close()


if __name__ == "__main__":
    main()
