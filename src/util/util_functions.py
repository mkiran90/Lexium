import os

import numpy as np
import spacy
from gensim.models import KeyedVectors


def get_position_map(body_words: list[int]):
    position_map = {}
    for i in range(len(body_words)):
        word = body_words[i]
        if position_map.get(word) is None:
            position_map[word] = [i]
        else:
            position_map[word].append(i)

    return position_map

def get_word2vec():
    return KeyedVectors.load_word2vec_format((os.path.dirname(os.path.abspath(__file__)) + "../../res/GoogleNews-vectors-negative300.bin"), binary=True)

def get_nlp():
    return spacy.load("en_core_web_md")

def get_word_vector(word, model):
        """
        Gets the word vector for a given word.
        :param word: Input word.
        :param model: Pre-trained word vector model.
        :return: Word vector (list) or zero(300) if the word is not in the vocabulary.
        """
        if word in model.key_to_index:
            return model[word]
        else:
            return np.zeros(shape=(300,), dtype=np.float32)

def body_meaning(body_words, model, inv_lexicon):

        total = 0
        vec_sum = np.zeros(shape=(300,))
        for word in body_words:
            token = inv_lexicon[word.wordID]
            vec = get_word_vector(token, model)
            summed_vec = vec * word.frequency()
            vec_sum += summed_vec
            total += word.frequency()

        return (vec_sum / total).astype(np.float32)