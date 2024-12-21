import time

import torch

from sentence_transformers import SentenceTransformer
from sentence_transformers.util import cos_sim, semantic_search

model = SentenceTransformer('sentence-transformers/all-MiniLM-L6-v2')

FILE = "model.pth"

# model = torch.load(FILE)
torch.save(model, FILE)


def encode_document(model, document, chunk_size=1024):
    # Split document into chunks of chunk_size words
    words = document.split()
    chunks = [' '.join(words[i:i + chunk_size]) for i in range(0, len(words), chunk_size)]
    chunk_embeddings = model.encode(chunks, convert_to_tensor=True)

    document_embedding = chunk_embeddings.mean(dim=0)
    return document_embedding



def get_semantic_score(query, document):

    query_embedding = model.encode(query, convert_to_tensor=True)
    doc_embedding = encode_document(model, document)

    score = cos_sim(query_embedding, doc_embedding).item()

    return score
