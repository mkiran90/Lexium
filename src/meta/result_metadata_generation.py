'''

HISTORY:

this data structure was first called DOC_URL_DICT
a simple mapping from docID -> docURL
now is a mapping from docID -> docURL, docImgURL, title
we'll use the previous DOC_URL_DICT and a csv that contains the img urls and title's to generate the new structure


IMPORTANT: THIS IS A ONE-TIME SCRIPT
'''
import csv
import struct

from src.forward_index.ForwardIndex import ForwardIndex
from src.meta.ResultMetaIndex import ResultMetaIndex

fwd_index = ForwardIndex()
url_dict = ResultMetaIndex()


def title_from_url(url:str):

    title_part = url.split("/")[-1]
    title = " ".join([s.capitalize() for s in title_part.split('-')[:-1]])

    return title
def get_new_data(docID, url_to_proc_docID_title, proc_docID_to_imgURL):

    url = url_dict.get(docID)
    info = url_to_proc_docID_title.get(url)

    if info is not None:
        proc_docID, title = info
        img_url = proc_docID_to_imgURL.get(proc_docID)
        if img_url is None:
            img_url = ""
            print("shouldn't happen", proc_docID)
    else:
        print(url)
        img_url = ""
        title = title_from_url(url)
        print(title)

    return url + '\0' + img_url + '\0' + title




if __name__ == "__main__":

    url_to_proc_docID_title = {}
    proc_docID_to_imgURL = {}

    with open(r"C:\Users\hunkh\Downloads\processed.csv",
           "r", encoding="utf8") as processed, open(
        r"C:\Users\hunkh\Downloads\scraped.csv", "r", encoding="utf8") as scraped:

        proc_reader = csv.reader(processed)
        scrap_reader = csv.reader(scraped)
        scrap_reader.__next__()
        proc_reader.__next__()

        for row in proc_reader:
            proc_docID = int(row[0])
            title = row[1]
            url = row[2]
            url_to_proc_docID_title[url] = (proc_docID, title)

        for row in scrap_reader:

            scrap_docID = int(row[0])
            img_url = row[1]

            if not img_url.startswith("http"):
                img_url = ""

            proc_docID_to_imgURL[scrap_docID] = img_url



    with open("../../res/metadata/result/new_data.txt", "w", encoding="utf8") as data, open(
            "../../res/metadata/result/new_offset.bin", "wb") as offset:

        for docID in range(fwd_index.size()):
            new_data = get_new_data(docID, url_to_proc_docID_title, proc_docID_to_imgURL)
            new_offset = data.tell()
            data.write(new_data + '\n')

            assigned_docID = offset.tell() / 4

            offset.write(struct.pack("I", new_offset))

            assert assigned_docID == docID
            if docID % 1000 == 0:
                print(docID)
