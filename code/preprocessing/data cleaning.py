import spacy
import re
import os
import pandas as pd

nlp = spacy.load("en_core_web_trf")

#TODO fix this shit cuz its not dynamic.
os.chdir("C:/Users/sabih/OneDrive/Documents/GitHub/Search-Engine/")

# chunk_size = 10000

def clean_tags(text):

    doc = nlp(text)

    clean_tokens = [
        re.sub(r'[<>:"/\\|?*]', '', token.lemma_) for token in doc
        if not token.is_space
        and not token.is_quote
        and not token.is_punct
        and not token.is_digit
    ]

    return " ".join(clean_tokens)

def clean_title(text):
    doc = nlp(text)

    clean_tokens = [
        re.sub(r'[<>:"/\\|?*]', '', token.lemma_) for token in doc
        if not token.is_stop
        and not token.is_punct
        and not token.is_quote
        and not token.is_space
        and not token.is_digit
    ]

    return " ".join(clean_tokens)

def clean_text(text):
    doc = nlp(text)

    # discarded_words = []

    superscript_pattern = r'^[\u00B9\u00B2\u00B3\u2070-\u2079\u2080-\u2089]'
    url_pattern = r'http[s]?://\S+|www\.\S+'

    clean_tokens = [
        re.sub(r'[<>:\"@/\'|?*]', '', token.lemma_)
        for token in doc
        if not token.is_stop
        and not token.is_punct
        and not token.text[0] in "\"'"
        and not token.is_space
        and not token.text[0].isdigit()
        and not re.match(url_pattern, token.text)
        and not re.match(r'^\d', token.text)
        and not re.match(superscript_pattern, token.text)
        and (
               re.search(r'[a-zA-Z]+[0-9]*', token.text)
               or re.search(r'[a-zA-Z]+-*[a-zA-Z0-9]+', token.text)
       )
        or discarded_words.append(token.text)
    ]

    # with open(os.getcwd() + '\\discarded_words.txt', 'w', encoding='utf-8') as f:
    #     for word in discarded_words:
    #         f.write(f"{word}\n")
    #
    # with open(os.getcwd() + '\\recorded_words.txt', 'a', encoding='utf-8') as f:
    #     for word in clean_tokens:
    #         f.write(f"{word}\n")

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

    df = pd.read_csv(file_path).head(2)

    df = df.apply(process_row, axis=1)

    df.to_csv(output_file, index=False)


# function call which creates the new csv
process_and_save(os.getcwd() + "\\medium_articles.csv", os.getcwd() + "\\updated_medium_articles.csv")