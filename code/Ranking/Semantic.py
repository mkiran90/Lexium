import time

import numpy as np
import torch

from sentence_transformers.util import cos_sim

from code.document.DocumentMetadata import DocumentMetadata
from code.lexicon_gen.Lexicon import Lexicon
from code.lexicon_gen.WordEmbedding import WordEmbedding

document_metadata = DocumentMetadata()
word_embedding = WordEmbedding()
lexicon = Lexicon()

def encode_document(model, document, chunk_size=1024):
    # Split document into chunks of chunk_size words
    words = document.split()
    chunks = [' '.join(words[i:i + chunk_size]) for i in range(0, len(words), chunk_size)]
    chunk_embeddings = model.encode(chunks, convert_to_tensor=True)

    document_embedding = chunk_embeddings.mean(dim=0)
    return document_embedding

def cosine_similarity(a, b):

    # Compute the dot product of a and b
    dot_product = np.dot(a, b)

    # Compute the magnitudes of a and b
    norm_a = np.linalg.norm(a)
    norm_b = np.linalg.norm(b)

    # Compute cosine similarity
    if norm_a == 0 or norm_b == 0:
        return 0.0  # Handle zero vectors
    return dot_product / (norm_a * norm_b)

def get_semantic_score(query, doc_id):

    vec_sum = np.zeros(shape=(300,))

    if len(query) == 0:
        query_embedding = vec_sum
    else:
        for word in query:
            word_id = lexicon.get(word)
            vec = word_embedding.get_word_embedding(word_id)

            if vec is not None:
                vec_sum += vec

        query_embedding = (vec_sum / len(query)).astype(np.float32)

    doc_embedding = document_metadata.get_doc_embedding(doc_id)

    score = cosine_similarity(query_embedding, doc_embedding)

    return score
