import csv
import time

from code.forward_index.ForwardIndex import ForwardIndex
from code.lexicon_gen.Lexicon import Lexicon

from code.document.DocURLDict import DocURLDict

index = ForwardIndex()
lexicon = Lexicon()
urlDict = DocURLDict()

def get_position_map(body_words: list[int]):
    position_map = {}
    for i in range(len(body_words)):
        word = body_words[i]
        if position_map.get(word) is None:
            position_map[word] = [i]
        else:
            position_map[word].append(i)

    return position_map

# converts row to a document, while storing all new words inside the document into the lexicon
def row_to_document(row):
    from code.document.Document import Document, DocumentBodyWord

    title_wordIDs = [lexicon.get_or_assign(word) for word in row["title"].split()]
    tag_wordIDs = [lexicon.get_or_assign(word) for word in row["tags"].split()]

    body_wordIDs = [lexicon.get_or_assign(word) for word in row["text"].split()]


    position_map = get_position_map(body_wordIDs)

    del body_wordIDs

    body_words: list[DocumentBodyWord] = [DocumentBodyWord(wordID, positions) for wordID, positions in position_map.items()]

    return Document(title_wordIDs, tag_wordIDs, body_words)

# stores all documents inside the csv into the forward index and new words into the lexicon
def store_rows_from_csv(csv_path):
    with open(csv_path, mode='r', encoding="utf-8") as file:
        csv_reader = csv.DictReader(file)

        #store the document information entirely.
        for row in csv_reader:
            document = row_to_document(row)
            docIDl = document.store(index)

            docIDd = urlDict.store(row["url"])

            assert docIDl==docIDd


# takes about 5 minutes to run.
def index_all_csvs():
    for i in range(1, 193 + 1):
        A = time.time()
        store_rows_from_csv(f"../../res/dataset/clean_split_dataset/clean_part_{i}.csv")
        print(f"Indexed documents from part {i} in {time.time() - A} seconds")

if __name__ == "__main__":

   #index_all_csvs
   pass
lexicon.save_lexicon()

