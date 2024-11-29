import shutil

import spacy
import pandas as pd

nlp = spacy.load("en_core_web_sm")


def clean_data(text):
    doc = nlp(text)

    clean_tokens = [
        token.lemma_ for token in doc
        if not token.is_stop and not token.is_punct and not token.is_space
    ]

    return " ".join(clean_tokens)


def process_and_save(file_path, output_file):
    shutil.copy(file_path, output_file)

    df["text"] = df["text"].apply(clean_data)

    with open(file_path, 'r+') as f:
        # Reposition the cursor to the beginning of the file
        f.seek(0)
        # Write the updated DataFrame back to the CSV, replacing the original "text" column
        df.to_csv(f, index=False, header=True)

    df = df.rename(columns={"text": "clean text"})

    df.to_csv(output_file, index=False, header=["cleaned_text"])




