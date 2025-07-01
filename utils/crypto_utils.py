import base64
from Crypto.Cipher import DES, PKCS1_OAEP
from Crypto.PublicKey import RSA
from Crypto.Signature import pkcs1_15
from Crypto.Hash import SHA256
from Crypto.Random import get_random_bytes
from Crypto.Util.Padding import pad, unpad

def generate_des_key():
    return get_random_bytes(8)

def des_encrypt(data: bytes, key: bytes) -> bytes:
    iv = get_random_bytes(8)
    cipher = DES.new(key, DES.MODE_CBC, iv)
    return iv + cipher.encrypt(pad(data, DES.block_size))

def des_decrypt(data: bytes, key: bytes) -> bytes:
    iv = data[:8]
    cipher = DES.new(key, DES.MODE_CBC, iv)
    return unpad(cipher.decrypt(data[8:]), DES.block_size)

def sha256_hash(data: bytes) -> str:
    return SHA256.new(data).hexdigest()

def load_rsa_private_key(path): return RSA.import_key(open(path, 'rb').read())
def load_rsa_public_key(path): return RSA.import_key(open(path, 'rb').read())

def rsa_encrypt(data: bytes, pub): return PKCS1_OAEP.new(pub, hashAlgo=SHA256).encrypt(data)
def rsa_decrypt(data: bytes, priv): return PKCS1_OAEP.new(priv, hashAlgo=SHA256).decrypt(data)

def rsa_sign(data: bytes, priv): return pkcs1_15.new(priv).sign(SHA256.new(data))
def rsa_verify(data: bytes, sig: bytes, pub) -> bool:
    try:
        pkcs1_15.new(pub).verify(SHA256.new(data), sig)
        return True
    except: return False
