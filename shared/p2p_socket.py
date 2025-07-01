import socket, json, struct

def send_json(sock, obj): send_bytes(sock, json.dumps(obj).encode())
def recv_json(sock):
    data = recv_bytes(sock)
    if data is None: return None
    return json.loads(data.decode())

def send_bytes(sock, data: bytes):
    sock.sendall(struct.pack('!I', len(data)) + data)

def recv_bytes(sock):
    raw_len = recv_exact(sock, 4)
    if not raw_len: return None
    length = struct.unpack('!I', raw_len)[0]
    return recv_exact(sock, length)

def recv_exact(sock, size):
    data = b''
    while len(data) < size:
        packet = sock.recv(size - len(data))
        if not packet: return None
        data += packet
    return data
