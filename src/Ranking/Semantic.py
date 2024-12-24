import numpy as np


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

def get_semantic_score(query_meaning, doc_meta):

    return cosine_similarity(query_meaning, doc_meta.meaning)
