import spacy
import re
import os
import pandas as pd

nlp = spacy.load("en_core_web_md")

#TODO fix this shit cuz its not dynamic.
os.chdir("C:/Users/sabih/OneDrive/Documents/GitHub/Search-Engine/")

# chunk_size = 10000

def clean_tags(text):
    doc = nlp(text)

    clean_tokens = [token.lemma_.lower() for token in doc]

    return " ".join(clean_tokens)


def clean_title(text):
    doc = nlp(text)

    clean_tokens = [
        token.lemma_.lower()
        for token in doc
        if not token.is_stop
        and not token.is_punct
    ]

    return " ".join(clean_tokens)

def clean_text(text):
    doc = nlp(text)

    def is_invalid_pattern(text):
        invalid_num_pattern = r'^[0-9\w_]'
        superscript_pattern = r'^[\u00B9\u00B2\u00B3\u2070-\u2079\u2080-\u2089]'
        return re.match(invalid_num_pattern, text) or re.match(superscript_pattern, text)

    def is_valid_pattern(text):
        anum_pattern = r'^[a-zA-Z]+[0-9]*$'
        anum_hyph_pattern = r'^[a-zA-Z]+-*[a-zA-Z0-9.]+$'
        return re.match(anum_pattern, text) or re.match(anum_hyph_pattern, text)


    clean_tokens = [
        token.lemma_.lower()
        for token in doc

        # VALID
        if (is_valid_pattern(token.text) and not token.is_stop)

        or

        # INVALID
        (not token.is_stop
        and not token.is_punct
        and not token.is_digit
        and not len(token.text) > 15
        and not token.is_space
        and not token.like_url
        and not token.like_email
        and is_invalid_pattern(token.text))
    ]

    return " ".join(clean_tokens)

# function to clean each row and insert tokens in each row to lexicon
def process_row(row):
    row["text"] = clean_text(row["text"])
    row["title"] = clean_title(row["title"])
    row["tags"] = clean_tags(row["tags"])

    # for token in row["text"].split():
    #     insert(token)
    #
    # for token in row["title"].split():
    #     insert(token)
    #
    # for token in row["tags"].split():
    #     insert(token)

    return row


# this function will load the dataset, clean it, add the tokens to lexicon, and generate
# a new csv file with the cleaned data
def process_and_save(file_path, output_file):

    df = pd.read_csv(file_path).head(10)

    df = df.apply(process_row, axis=1)

    df.to_csv(output_file, index=False)


# function call which creates the new csv
process_and_save(os.getcwd() + "\\medium_articles.csv", os.getcwd() + "\\updated_medium_articles.csv")