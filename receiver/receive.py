import sys, os, base64, socket
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from utils.crypto_utils import *
from utils.audio_utils import play_audio
from shared.p2p_socket import send_json, recv_json

# ==== Cấu hình ====
DEFAULT_PORT = 5000
AUDIO_OUTPUT = "receiver/audio/received.wav"

# ==== Nhập PORT từ dòng lệnh nếu có ====
PORT = int(sys.argv[1]) if len(sys.argv) > 1 else DEFAULT_PORT

print(f"[🔒] Đang lắng nghe trên cổng {PORT}...")

sock = socket.socket()
sock.bind(('0.0.0.0', PORT))
sock.listen(1)
conn, addr = sock.accept()
print(f"[📥] Kết nối từ {addr[0]}:{addr[1]}")

# ==== Bắt tay (Handshake) ====
if recv_json(conn).get("message") != "Hello!":
    print("[❌] Không đúng tín hiệu bắt tay."); conn.close(); exit()
send_json(conn, {"status": "Ready!"})
print("[🤝] Bắt tay thành công.")

# ==== Nhận thông tin trao đổi khóa và xác thực ====
receiver_priv = load_rsa_private_key("keys/receiver_private.pem")
sender_pub = load_rsa_public_key("keys/sender_public.pem")

info = recv_json(conn)
metadata = info["metadata"].encode()
sig = base64.b64decode(info["signed_info"])
enc_key = base64.b64decode(info["encrypted_des_key"])

# ==== Xác thực metadata ====
if not rsa_verify(metadata, sig, sender_pub):
    print("❌ Sai chữ ký metadata."); send_json(conn, {"status": "NACK"}); conn.close(); exit()
print("[🔐] Metadata được xác thực thành công.")

# ==== Giải mã khóa DES ====
des_key = rsa_decrypt(enc_key, receiver_priv)

# ==== Nhận và kiểm tra dữ liệu ====
data = recv_json(conn)
cipher = base64.b64decode(data["cipher"])
cipher_hash = data["hash"]
cipher_sig = base64.b64decode(data["sig"])

# ==== Kiểm tra toàn vẹn ====
if sha256_hash(cipher) != cipher_hash:
    print("❌ Hash không khớp."); send_json(conn, {"status": "NACK"}); conn.close(); exit()
if not rsa_verify(cipher, cipher_sig, sender_pub):
    print("❌ Chữ ký dữ liệu không hợp lệ."); send_json(conn, {"status": "NACK"}); conn.close(); exit()
print("[✅] Toàn vẹn và chữ ký dữ liệu hợp lệ.")

# ==== Giải mã và phát âm thanh ====
plain = des_decrypt(cipher, des_key)
os.makedirs(os.path.dirname(AUDIO_OUTPUT), exist_ok=True)
with open(AUDIO_OUTPUT, 'wb') as f:
    f.write(plain)
print("[🎧] Đã ghi âm thanh giải mã vào tệp.")

# ==== Phát âm thanh ====
play_audio(AUDIO_OUTPUT)

# ==== Gửi phản hồi và đóng kết nối ====
send_json(conn, {"status": "ACK"})
conn.close()
print("[✅] Gửi phản hồi thành công. Kết thúc.")
