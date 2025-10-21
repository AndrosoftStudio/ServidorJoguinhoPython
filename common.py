
import json, struct, socket, math, time
from dataclasses import dataclass, asdict
from typing import Dict, Any, Tuple, List

# Simple length-prefixed JSON over TCP (so we don't have to worry about packet boundaries)
def send_msg(sock, obj):
    data = json.dumps(obj).encode('utf-8')
    sock.sendall(len(data).to_bytes(4, 'big') + data)

def recv_msg(sock):
    header = recvall(sock, 4)
    if not header:
        return None
    n = int.from_bytes(header, 'big')
    payload = recvall(sock, n)
    if payload is None:
        return None
    return json.loads(payload.decode('utf-8'))

def recvall(sock, n):
    buf = bytearray()
    while len(buf) < n:
        chunk = sock.recv(n - len(buf))
        if not chunk:
            return None
        buf.extend(chunk)
    return bytes(buf)

def now() -> float:
    return time.time()

def clamp(v, lo, hi):
    return max(lo, min(hi, v))

def circle_rect_collision(cx, cy, cr, rx, ry, rw, rh):
    # clamp circle center to rect bounds
    nearest_x = clamp(cx, rx, rx + rw)
    nearest_y = clamp(cy, ry, ry + rh)
    dx = cx - nearest_x
    dy = cy - nearest_y
    return (dx*dx + dy*dy) <= (cr*cr)

def get_lan_ip():
    # Best-effort LAN IP detection without external calls
    ip = "127.0.0.1"
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
    except Exception:
        pass
    return ip
