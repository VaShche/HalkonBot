import pickle
import os


def load_dict_from_file(f_path):
    if os.path.exists(f_path):
        with open(f_path, 'rb') as f:
            res = pickle.load(f)
        return res
    return dict()


def save_dict_to_file(f_path, data):
    with open(f_path, 'wb') as f:
        pickle.dump(data, f)

