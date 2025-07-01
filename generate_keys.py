import os
from Crypto.PublicKey import RSA

def generate_key_pair(filename_prefix):
    os.makedirs("keys", exist_ok=True)  # Tạo thư mục nếu chưa có

    key = RSA.generate(2048)
    private_key = key.export_key()
    public_key = key.publickey().export_key()

    with open(f"keys/{filename_prefix}_private.pem", "wb") as f:
        f.write(private_key)
    with open(f"keys/{filename_prefix}_public.pem", "wb") as f:
        f.write(public_key)

generate_key_pair("sender")
generate_key_pair("receiver")
