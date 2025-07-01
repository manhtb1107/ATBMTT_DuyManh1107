import sys
import os
import base64
import socket
import threading
import time
from PyQt5 import QtWidgets, QtGui, QtCore
from utils.crypto_utils import *
from utils.audio_utils import record_audio, play_audio
from shared.p2p_socket import send_json, recv_json

SEND_FILE = 'sender/audio/message.wav'
RECV_FILE = 'receiver/audio/received.wav'

class ChatSimulator(QtWidgets.QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("🔐 Mô phỏng Chat Âm thanh Bảo mật")
        self.setGeometry(200, 100, 700, 520)
        self.setStyleSheet("background-color: #f0f4f7; font-family: Arial; font-size: 13px;")
        self.setup_ui()

    def setup_ui(self):
        main_layout = QtWidgets.QVBoxLayout()

        # ====== Group: Cấu hình kết nối ======
        config_group = QtWidgets.QGroupBox("⚙️ Cấu hình kết nối")
        config_layout = QtWidgets.QGridLayout()

        self.my_port = QtWidgets.QLineEdit()
        self.my_port.setPlaceholderText("Cổng của bạn (VD: 5000)")
        self.my_port.setMinimumHeight(30)

        self.receiver_ip = QtWidgets.QLineEdit()
        self.receiver_ip.setPlaceholderText("IP người nhận (VD: 127.0.0.1)")
        self.receiver_ip.setMinimumHeight(30)

        self.receiver_port = QtWidgets.QLineEdit()
        self.receiver_port.setPlaceholderText("Cổng người nhận (VD: 5000)")
        self.receiver_port.setMinimumHeight(30)

        config_layout.addWidget(QtWidgets.QLabel("🔌 Cổng của bạn:"), 0, 0)
        config_layout.addWidget(self.my_port, 0, 1)
        config_layout.addWidget(QtWidgets.QLabel("🌐 IP người nhận:"), 1, 0)
        config_layout.addWidget(self.receiver_ip, 1, 1)
        config_layout.addWidget(QtWidgets.QLabel("🔌 Cổng người nhận:"), 2, 0)
        config_layout.addWidget(self.receiver_port, 2, 1)

        config_group.setLayout(config_layout)
        main_layout.addWidget(config_group)

        # ====== Group: Nhật ký hoạt động ======
        self.info = QtWidgets.QTextEdit()
        self.info.setReadOnly(True)
        self.info.setStyleSheet("background-color: #ffffff; border: 1px solid #ccc; padding: 5px;")
        self.info.setMinimumHeight(150)
        main_layout.addWidget(QtWidgets.QLabel("📋 Nhật ký hoạt động:"))
        main_layout.addWidget(self.info)

        # ====== Group: Điều khiển ======
        control_group = QtWidgets.QGroupBox("🎮 Điều khiển")
        control_layout = QtWidgets.QHBoxLayout()

        self.btn_record_send = QtWidgets.QPushButton("🎙️ Ghi âm & Gửi")
        self.btn_record_send.setMinimumHeight(40)
        self.btn_record_send.clicked.connect(self.send_audio)

        self.btn_listen = QtWidgets.QPushButton("🔐 Chờ & Nhận")
        self.btn_listen.setMinimumHeight(40)
        self.btn_listen.clicked.connect(self.listen_audio)

        self.btn_play_audio = QtWidgets.QPushButton("▶️ Phát âm thanh")
        self.btn_play_audio.setMinimumHeight(40)
        self.btn_play_audio.setEnabled(False)
        self.btn_play_audio.clicked.connect(self.play_received_audio)

        control_layout.addWidget(self.btn_record_send)
        control_layout.addWidget(self.btn_listen)
        control_layout.addWidget(self.btn_play_audio)
        control_group.setLayout(control_layout)

        main_layout.addWidget(control_group)
        self.setLayout(main_layout)

    def log(self, msg):
        timestamp = time.strftime("%H:%M:%S", time.localtime())
        self.info.append(f"[{timestamp}] {msg}")
        print(msg)

    def play_received_audio(self):
        try:
            self.log("🎧 Đang phát âm thanh đã nhận...")
            play_audio(RECV_FILE)
        except Exception as e:
            self.log(f"❌ Không thể phát âm thanh: {e}")

    def send_audio(self):
        def run():
            try:
                ip = self.receiver_ip.text().strip()
                port_text = self.receiver_port.text().strip()
                if not ip or not port_text:
                    self.log("❌ Vui lòng nhập IP và PORT người nhận.")
                    return
                port = int(port_text)

                self.log("📡 Đang kết nối tới người nhận...")
                sock = socket.socket(); sock.connect((ip, port))
                send_json(sock, {"message": "Hello!"})
                if recv_json(sock).get("status") != "Ready!":
                    self.log("❌ Người nhận không sẵn sàng.")
                    return

                self.log("🔐 Đang trao khóa...")
                des_key = generate_des_key()
                sender_priv = load_rsa_private_key("keys/sender_private.pem")
                receiver_pub = load_rsa_public_key("keys/receiver_public.pem")
                metadata = f"sender_123_{int(time.time())}".encode()
                sig = rsa_sign(metadata, sender_priv)
                enc_key = rsa_encrypt(des_key, receiver_pub)

                send_json(sock, {
                    "metadata": metadata.decode(),
                    "signed_info": base64.b64encode(sig).decode(),
                    "encrypted_des_key": base64.b64encode(enc_key).decode()
                })

                self.log("🎤 Ghi âm tin nhắn...")
                record_audio(SEND_FILE, duration=5)
                with open(SEND_FILE, 'rb') as f:
                    audio = f.read()
                cipher = des_encrypt(audio, des_key)
                hash_val = sha256_hash(cipher)
                sig_data = rsa_sign(cipher, sender_priv)

                send_json(sock, {
                    "cipher": base64.b64encode(cipher).decode(),
                    "hash": hash_val,
                    "sig": base64.b64encode(sig_data).decode()
                })

                res = recv_json(sock)
                self.log(f"📬 Phản hồi: {res.get('status')}")
                sock.close()

            except Exception as e:
                self.log(f"❌ Lỗi gửi: {e}")
        threading.Thread(target=run).start()

    def listen_audio(self):
        def run():
            try:
                port_text = self.my_port.text().strip()
                if not port_text:
                    self.log("❌ Vui lòng nhập cổng nhận.")
                    return
                port = int(port_text)

                self.log(f"🔒 Đang lắng nghe tại cổng {port}...")
                sock = socket.socket(); sock.bind(('0.0.0.0', port)); sock.listen(1)
                conn, addr = sock.accept()
                self.log(f"📥 Kết nối từ {addr[0]}:{addr[1]}")

                if recv_json(conn).get("message") != "Hello!":
                    self.log("❌ Sai tín hiệu bắt tay.")
                    conn.close(); return

                send_json(conn, {"status": "Ready!"})
                self.log("🔐 Nhận khóa...")

                recv_info = recv_json(conn)
                receiver_priv = load_rsa_private_key("keys/receiver_private.pem")
                sender_pub = load_rsa_public_key("keys/sender_public.pem")

                metadata = recv_info["metadata"].encode()
                sig = base64.b64decode(recv_info["signed_info"])
                enc_key = base64.b64decode(recv_info["encrypted_des_key"])

                if not rsa_verify(metadata, sig, sender_pub):
                    self.log("❌ Sai chữ ký metadata.")
                    send_json(conn, {"status": "NACK"}); return

                des_key = rsa_decrypt(enc_key, receiver_priv)

                self.log("🎧 Nhận dữ liệu âm thanh...")
                data = recv_json(conn)
                cipher = base64.b64decode(data["cipher"])
                if sha256_hash(cipher) != data["hash"]:
                    self.log("❌ Dữ liệu bị thay đổi (Hash sai).")
                    send_json(conn, {"status": "NACK"}); return

                if not rsa_verify(cipher, base64.b64decode(data["sig"]), sender_pub):
                    self.log("❌ Sai chữ ký dữ liệu.")
                    send_json(conn, {"status": "NACK"}); return

                plain = des_decrypt(cipher, des_key)
                os.makedirs("receiver/audio", exist_ok=True)
                with open(RECV_FILE, 'wb') as f: f.write(plain)

                self.log("✅ Đã nhận file âm thanh. Nhấn ▶️ để nghe.")
                self.btn_play_audio.setEnabled(True)
                send_json(conn, {"status": "ACK"})
                conn.close()

            except Exception as e:
                self.log(f"❌ Lỗi nhận: {e}")
        threading.Thread(target=run).start()

if __name__ == '__main__':
    app = QtWidgets.QApplication(sys.argv)
    window = ChatSimulator()
    window.show()
    sys.exit(app.exec_())
