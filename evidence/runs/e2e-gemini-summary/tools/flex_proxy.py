#!/usr/bin/env python3
"""Reverse proxy: agent -> Gemini API, adding serviceTier=flex and the real key.

The agent container only ever sees a dummy key. Listens on 0.0.0.0:9090; paths
/v1/<rest> and /v1beta/<rest> are forwarded to generativelanguage.googleapis.com/v1beta/<rest>.
Every request is logged (status, service tier header, usage when non-streaming
or from the last SSE chunk) to $PROXY_LOG as JSON lines.
"""
import http.client, http.server, json, os, socket, socketserver, ssl, sys, time, threading

# Some workers have no IPv6 route; http.client tries addresses in order and would hang on AAAA.
_gai = socket.getaddrinfo
socket.getaddrinfo = lambda h, *a, **k: [r for r in _gai(h, *a, **k) if r[0] == socket.AF_INET] or _gai(h, *a, **k)

KEY = open(os.environ.get('GEMINI_KEY_FILE', '/run/ebv/gemini_key')).read().strip()
TIER = os.environ.get('GEMINI_TIER', 'flex')
LOG = open(os.environ.get('PROXY_LOG', '/job/out/proxy.jsonl'), 'a', buffering=1)
HOST = 'generativelanguage.googleapis.com'
lock = threading.Lock()
CTX = ssl.create_default_context()

class H(http.server.BaseHTTPRequestHandler):
    protocol_version = 'HTTP/1.1'
    def log_message(self, *a): pass
    def _fwd(self):
        t0 = time.time()
        path = self.path
        for pre in ('/v1beta/', '/v1/'):
            if path.startswith(pre):
                path = '/v1beta/' + path[len(pre):]; break
        n = int(self.headers.get('content-length') or 0)
        body = self.rfile.read(n) if n else b''
        if body and ('generateContent' in path or 'GenerateContent' in path):
            try:
                d = json.loads(body); d['serviceTier'] = TIER; body = json.dumps(d).encode()
            except Exception: pass
        hdr = {k: v for k, v in self.headers.items()
               if k.lower() not in ('host', 'content-length', 'x-goog-api-key', 'authorization', 'connection', 'accept-encoding')}
        hdr['x-goog-api-key'] = KEY; hdr['content-length'] = str(len(body))
        rec = {'t': round(t0), 'path': path.split('?')[0]}
        for attempt in range(6):
            try:
                c = http.client.HTTPSConnection(HOST, timeout=900, context=CTX)
                c.request(self.command, path, body=body, headers=hdr)
                r = c.getresponse()
                if r.status in (429, 500, 502, 503, 504) and attempt < 5:
                    r.read(); c.close(); rec.setdefault('retries', []).append(r.status)
                    time.sleep(min(60, 5 * 2 ** attempt)); continue
                break
            except Exception as e:
                rec.setdefault('errors', []).append(type(e).__name__)
                if attempt == 5:
                    self.send_response(502); self.send_header('content-length', '0'); self.end_headers()
                    rec['status'] = 502; self._log(rec, t0); return
                time.sleep(min(60, 5 * 2 ** attempt))
        rec['status'] = r.status; rec['tier'] = r.getheader('x-gemini-service-tier')
        self.send_response(r.status)
        for k, v in r.getheaders():
            if k.lower() not in ('transfer-encoding', 'connection', 'content-length', 'content-encoding'):
                self.send_header(k, v)
        self.send_header('transfer-encoding', 'chunked'); self.end_headers()
        tail = b''
        try:
            while True:
                chunk = r.read1(65536) if hasattr(r, 'read1') else r.read(65536)
                if not chunk: break
                tail = (tail + chunk)[-8192:]
                self.wfile.write(b'%x\r\n%s\r\n' % (len(chunk), chunk)); self.wfile.flush()
            self.wfile.write(b'0\r\n\r\n'); self.wfile.flush()
        except Exception as e:
            rec['client_error'] = type(e).__name__
        i = tail.rfind(b'"usageMetadata"')
        if i >= 0:
            try:
                rec['usage'] = json.JSONDecoder().raw_decode(tail[i + len(b'"usageMetadata"'):].lstrip(b': ').decode())[0]
            except Exception: pass
        c.close(); self._log(rec, t0)
    def _log(self, rec, t0):
        rec['dur'] = round(time.time() - t0, 1)
        with lock: LOG.write(json.dumps(rec) + '\n')
    do_POST = do_GET = _fwd

class S(socketserver.ThreadingMixIn, http.server.HTTPServer):
    daemon_threads = True; allow_reuse_address = True

if __name__ == '__main__':
    S(('0.0.0.0', int(os.environ.get('PROXY_PORT', 9090))), H).serve_forever()
