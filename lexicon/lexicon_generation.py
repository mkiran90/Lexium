# ID_TO_POSITION_FILE_PATH = "/id_to_position.bin"
# LEXICON_DATA_PATH = "/lexicon_data.bin"

import os
import string
import struct


DICTIONARY_ROOT = "dictionary/"

def insert(key:string):

    word_id = get_word_id()

    path = DICTIONARY_ROOT + "/".join(key)
    os.makedirs(path, exist_ok=True)
    file_name = path + "/data.bin"

    with open(file_name, 'wb') as file:
        file.write(struct.pack('i', word_id))


def retrieve(key:string):

    path = DICTIONARY_ROOT + "/".join(key)
    os.makedirs(path, exist_ok=True)
    file_name = f'{path}/data.bin'

    try:
        with open(file_name, 'rb') as file:
            return struct.unpack('i', file.read(4))[0]
    except FileNotFoundError:
        pass


def get_word_id():
    word_id = 0
    counter_path = DICTIONARY_ROOT + "counter.bin"


    if not os.path.exists(counter_path):
        os.makedirs(os.path.dirname(counter_path), exist_ok=True)

        with open(counter_path, 'wb') as f:
            f.write(struct.pack('I', 0))
    else:
        with open(counter_path, 'rb') as f:
            word_id = struct.unpack('I', f.read(4))[0]

        word_id += 1

        with open(counter_path, 'wb') as f:
            f.write(struct.pack('I', word_id))

    return word_id





