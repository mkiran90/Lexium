import os
import pandas as pd
from data_cleaning import clean_body, clean_title, clean_tags
import time
import argparse

PARENT_CSV = "../../res/dataset/medium_articles.csv"
SPLIT_CSV_ROOT = "../../res/dataset/split_dataset/"
CLEAN_SPLIT_CSV_ROOT = "../../res/dataset/clean_split_dataset/"

# split parent csv into smaller csv for parallel processing
def split_csv(input_file = PARENT_CSV, output_dir = SPLIT_CSV_ROOT, rows_per_file = 1000):
    """
    Splits a CSV file into multiple smaller CSV files.

    Parameters:
    - input_file: Path to the input CSV file.
    - output_dir: Directory where the output CSV files will be saved.
    - rows_per_file: Number of rows each output CSV file should have.
    """
    # Ensure the output directory exists
    os.makedirs(output_dir, exist_ok=True)

    # Read the input CSV file in chunks
    chunk_number = 1
    for chunk in pd.read_csv(input_file, chunksize=rows_per_file):
        output_file = os.path.join(output_dir, f"part_{chunk_number}.csv")
        chunk.to_csv(output_file, index=False)
        print(f"Created: {output_file}")
        chunk_number += 1

def clean_csv_and_store(input_csv, output_dir=CLEAN_SPLIT_CSV_ROOT):

    df = pd.read_csv(input_csv)[['title', 'text', 'tags', 'url']] #dataframe containing selected columns for all rows

    df = df[df['text'].apply(len) > 100] #empirically determined value to filter out garbage and faulty articles

    # cleaning_data_frame, url remains unchanged

    df['title'] = df['title'].apply(clean_title)
    df['text'] = df['text'].apply(clean_body)
    df['tags'] = df['tags'].apply(clean_tags)

    output_path = os.path.join(output_dir, f"clean_{os.path.basename(input_csv)}")

    # save cleaned csv
    df.to_csv(output_path, index=False)

if __name__=="__main__":

    parser = argparse.ArgumentParser(description="Process the CSV")
    parser.add_argument("csv_num", type=int, help="Maximum number of rows per file.")
    n = parser.parse_args().csv_num
    input_file_path = os.path.join(SPLIT_CSV_ROOT + f"part_{n}.csv")

    A = time.time()
    clean_csv_and_store(input_file_path)
    print(f"Cleaned part {n} in {time.time()-A} seconds")