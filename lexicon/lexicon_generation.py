# ID_TO_POSITION_FILE_PATH = "/id_to_position.bin"
# LEXICON_DATA_PATH = "/lexicon_data.bin"

import os
import random
import string
import struct

# Function to generate a random word of given length
def generate_random_word(length=5):
    return ''.join(random.choices(string.ascii_lowercase, k=length))

DICTIONARY_ROOT = "dictionary/"

def insert(key:string, val:int):

    path = DICTIONARY_ROOT + "/".join(key)
    os.makedirs(path, exist_ok=True)
    file_name = f'{path}/data.bin'

    with open(file_name, 'wb') as file:
        file.write(struct.pack('i', val))

def retrieve(key:string):

    path = DICTIONARY_ROOT + "/".join(key)
    os.makedirs(path, exist_ok=True)
    file_name = f'{path}/data.bin'

    try:
        with open(file_name, 'rb') as file:
            return struct.unpack('i', file.read(4))[0]
    except FileNotFoundError:
        pass

for i in range(1, 1001):
    insert(generate_random_word(random.randint(1, 11)), i)





