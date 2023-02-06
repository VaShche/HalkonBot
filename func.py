import pickle
from cryptography.fernet import Fernet
import os


def load_dict_from_file(f_path, key=None):
    if os.path.exists(f_path):
        with open(f_path, 'rb') as f:
            f_data = f.read()
            if key:
                ciper = Fernet(key)
                f_data = ciper.decrypt(f_data)
            res = pickle.loads(f_data)
        return res
    return dict()


def save_dict_to_file(f_path, data, key=None):
    with open(f_path, 'wb') as f:
        f_data = pickle.dumps(data)
        if key:
            ciper = Fernet(key)
            f_data = ciper.encrypt(f_data)
        f.write(f_data)

