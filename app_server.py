import argparse
import json
from http.server import ThreadingHTTPServer, BaseHTTPRequestHandler

from database import Database


class AppServerHandler(BaseHTTPRequestHandler):
    database = None

    def log_message(self, *_):
        pass

    def do_POST(self):
        try:
            length = int(self.headers.get("Content-Length", 0))
            payload = json.loads(self.rfile.read(length))
            number = payload["number"]
        except:
            return self._respond(400, {"error": "bad_request"})

        if type(number) is not int or number < 0:
            return self._respond(
                400,
                {
                    "error": "bad_request",
                    "message": "number must be a natural number (0..N)"
                }
            )

        status, body = self._process(number)
        self._respond(status, body)

    def _process(self, n):
        error = self.database.check_and_insert(n)
        if error:
            code, msg = error
            print(f"[APP SERVER] ERROR: {msg}")
            return 400, {"error": code, "message": msg}
        print(f"[APP SERVER] OK: processed {n}, returning {n + 1}")
        return 200, {"result": n + 1}

    def _respond(self, status, obj):
        data = json.dumps(obj).encode()
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
        "--db-url",
        required=True,
        help="e.g. mysql://app_user:app_password@127.0.0.1:3306/numbers"
    )
    p.add_argument(
        "--host",
        default="127.0.0.1",
        help="interface to listen"
    )
    p.add_argument(
        "--port",
        type=int,
        default=8001,
        help="tcp port to listen (default: 8001)"
    )
    return p.parse_args(argv)


def main(argv=None):
    args = parse_args(argv)

    print(f"[APP SERVER] db_url: {args.db_url}")
    db = Database(args.db_url)

    # Test
    db.reset()

    handler = type("AppHandler", (AppServerHandler,), {"database": db})
    server = ReusableHTTPServer((args.host, args.port), handler)
    print(f"[APP SERVER] listening on http://{args.host}:{args.port}")

    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\n[APP SERVER] shutting down")
    finally:
        server.server_close()


if __name__ == "__main__":
    main()
