import spacy
import os
import pandas as pd
from code.preprocessing.ValidityCheckers import *
nlp = spacy.load("en_core_web_md")

#TODO fix this shit cuz its not dynamic.
os.chdir("C:/Users/sabih/OneDrive/Documents/GitHub/Search-Engine/")

def clean_tags(text):
    doc = nlp(text)

    clean_tokens = [token.lemma_.lower() for token in doc]

    return " ".join(clean_tokens)


def clean_title(text):
    doc = nlp(text)

    clean_tokens = [token.lemma_.lower() for token in doc]

    return " ".join(clean_tokens)


def clean_text(text):
    doc = nlp(text)

    clean_tokens = [token.lemma_.lower() for token in doc if is_valid_text(token)]

    return " ".join(clean_tokens)

# function to clean each row and insert tokens in each row to lexicon
def process_row(row):
    row["text"] = clean_text(row["text"])
    row["title"] = clean_title(row["title"])
    row["tags"] = clean_tags(row["tags"])
    return row


# this function will load the dataset, clean it, add the tokens to lexicon, and generate
# a new csv file with the cleaned data
def process_and_save(file_path, output_file):

    df = pd.read_csv(file_path).head(10)

    df = df.apply(process_row, axis=1)

    df.to_csv(output_file, index=False)


# function call which creates the new csv
process_and_save(os.getcwd() + "\\medium_articles.csv", os.getcwd() + "\\updated_medium_articles.csv")