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

def get_semantic_score(query_word_ids, doc_id, word_embedding, document_metadata):

    vec_sum = np.zeros(shape=(300,))

    if len(query_word_ids) == 0:
        query_embedding = vec_sum
    else:
        for word_id in query_word_ids:
            vec = word_embedding.get_word_embedding(word_id)

            if vec is not None:
                vec_sum += vec

        query_embedding = (vec_sum / len(query_word_ids)).astype(np.float32)

    doc_embedding = document_metadata.get_doc_embedding(doc_id)

    score = cosine_similarity(query_embedding, doc_embedding)

    return score
