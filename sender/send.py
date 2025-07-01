import sys, os, time, base64, socket
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from utils.crypto_utils import *
from utils.audio_utils import record_audio
from shared.p2p_socket import send_json, recv_json

# ==== Cấu hình ====
DEFAULT_RECEIVER_IP = '127.0.0.1'
DEFAULT_PORT = 5000
AUDIO_FILE = 'sender/audio/message.wav'

# ==== Cho phép nhập IP và PORT từ dòng lệnh ====
RECEIVER_IP = sys.argv[1] if len(sys.argv) > 1 else DEFAULT_RECEIVER_IP
PORT = int(sys.argv[2]) if len(sys.argv) > 2 else DEFAULT_PORT

print(f"[📡] Kết nối tới {RECEIVER_IP}:{PORT}...")

try:
    sock = socket.socket()
    sock.connect((RECEIVER_IP, PORT))
except Exception as e:
    print(f"[❌] Không thể kết nối: {e}")
    sys.exit(1)

# ==== Bắt tay (Handshake) ====
send_json(sock, {"message": "Hello!"})
if recv_json(sock).get("status") != "Ready!":
    print("[❌] Người nhận chưa sẵn sàng.")
    sock.close()
    sys.exit(1)
print("[🤝] Bắt tay thành công.")

# ==== Trao đổi khóa và xác thực (RSA) ====
print("[🔐] Đang tạo khóa và ký metadata...")
des_key = generate_des_key()
sender_priv = load_rsa_private_key("keys/sender_private.pem")
receiver_pub = load_rsa_public_key("keys/receiver_public.pem")
metadata = f"sender_123_{int(time.time())}".encode()
signature = rsa_sign(metadata, sender_priv)
enc_des_key = rsa_encrypt(des_key, receiver_pub)

send_json(sock, {
    "metadata": metadata.decode(),
    "signed_info": base64.b64encode(signature).decode(),
    "encrypted_des_key": base64.b64encode(enc_des_key).decode()
})
print("[📤] Đã gửi thông tin xác thực và khóa DES.")

# ==== Ghi âm và gửi dữ liệu ====
print("[🎙️] Đang ghi âm trong 5 giây...")
record_audio(AUDIO_FILE, duration=5)

with open(AUDIO_FILE, 'rb') as f:
    audio = f.read()

cipher = des_encrypt(audio, des_key)
hash_val = sha256_hash(cipher)
cipher_sig = rsa_sign(cipher, sender_priv)

send_json(sock, {
    "cipher": base64.b64encode(cipher).decode(),
    "hash": hash_val,
    "sig": base64.b64encode(cipher_sig).decode()
})
print("[🚀] Đã gửi âm thanh mã hóa và chữ ký.")

# ==== Nhận phản hồi ====
status = recv_json(sock)
print(f"[📬] Phản hồi từ người nhận: {status.get('status')}")
sock.close()
