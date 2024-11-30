import shutil

import spacy
import pandas as pd

nlp = spacy.load("en_core_web_sm")

chunk_size = 10000

def clean_tags(text):

    doc = nlp(text)

    clean_tokens = [
        token.lemma_ for token in doc
    ]

    return " ".join(clean_tokens)


def clean_title(text):
    doc = nlp(text)

    clean_tokens = [
        token.lemma_ for token in doc
        if not token.is_stop and not token.is_punct and not token.is_space
    ]

    return " ".join(clean_tokens)

def clean_text(text):
    doc = nlp(text)

    clean_tokens = [
        token.lemma_ for token in doc
        if not token.is_stop
        and not token.is_punct
        and not token.is_space
        and not token.is_digit
        and (token.is_alpha and token.like_num)
    ]

    return " ".join(clean_tokens)


def process_and_save(file_path, output_file):
    df = pd.read_csv(file_path, chunksize = chunk_size)

    for chunk in df:
        df["text"] = df["text"].apply(clean_text)
        df["title"] = df["title"].apply(clean_title)
        df["tags"] = df["tags"].apply(clean_tags)

    df.to_csv(output_file, index=False)




