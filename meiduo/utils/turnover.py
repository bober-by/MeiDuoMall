import base64
import pickle

def dumps(cart_dict):
    # 1:
    cart_bytes = pickle.dumps(cart_dict)
    # 2
    cart_64 = base64.b64encode(cart_bytes)
    # 3
    cart_str = cart_64.decode()

    return cart_str

def loads(cart_str):
    # 3
    cart_64 = cart_str.encode()
    # 2
    cart_bytes = base64.b64decode(cart_64)
    # 1
    cart_dict = pickle.loads(cart_bytes)
    return cart_dict