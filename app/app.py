import os

from flask import Flask, request, render_template, redirect, url_for

from src.document.DocURLDict import DocURLDict
from src.document.MetaIndex import MetaIndex
from src.forward_index.ForwardIndex import ForwardIndex
from src.inverted_index.InvertedIndex import InvertedIndex
from src.lexicon_gen.Lexicon import Lexicon
from src.lexicon_gen.WordEmbedding import WordEmbedding
from src.querying.ResultGeneration import ResultGeneration
from src.util.util_functions import get_nlp

app = Flask(__name__)



# THESE SHOULD BE LOADED AS APP STARTS UP, OR AS SERVER STARTS
nlp = get_nlp()
inverted_index = InvertedIndex()
forward_index = ForwardIndex()
lexicon = Lexicon()
urlDict = DocURLDict()
meta_index = MetaIndex()
word_embedding = WordEmbedding()

def extract_title_from_link(link):
    try:
       
        title_with_sequence = link.split("/")[4]
        # replace "-" with spaces
        title = ' '.join(title_with_sequence.split('-')[:-1])
        return title
    except IndexError:
        return "Invalid link"

def extract_author_from_link(link):
    try:
        # Extract the part of the URL containing the author
        author_with_at = link.split("/")[3]
        # Remove the "@" prefix
        author = author_with_at.lstrip("@")
        return author
    except IndexError:
        return "Invalid link"


@app.route('/results')
def results():
    query = request.args.get('query', '').strip()
    
    print(f"User query: {query}")
    
    result_gen = ResultGeneration(query, nlp,inverted_index,forward_index,lexicon,urlDict,meta_index,word_embedding)
    corrected_query = result_gen._correct_query_words()
    print(f"Corrected query: {corrected_query}")

    urls = result_gen.get_search_results()

    # Handle no results
    if not query or query.lower() == "no results" or not urls:
        return redirect(url_for('no_result'))

    docs_per_page = 10
    total_docs = len(urls)
    total_pages = (total_docs + docs_per_page - 1) // docs_per_page

    # Ensure the page number is valid
    page = int(request.args.get('page', 1))  # Default to page 1
    if page < 1 or page > total_pages:
        return redirect(url_for('no_result'))

    # Pagination range
    pagination_range = list(
        range(max(1, page - 2), min(total_pages + 1, page + 3))
    )

    start_index = (page - 1) * docs_per_page
    end_index = start_index + docs_per_page
    paginated_urls = urls[start_index:end_index]

    try:
         # Generate results for the current page
     paginated_results = [
        {
            "title": extract_title_from_link(url),
            "link":   url,
            "author": extract_author_from_link(url),
        }
        for url in paginated_urls
    ]
    except Exception as e:
        print(f"Error fetching results: {e}")
        return redirect(url_for('no_result'))

    typo_suggestion = None if query == corrected_query else f'Did you mean "{corrected_query}"?'

    # Render the results page
    return render_template(
        'results.html',
        typo_suggestion=typo_suggestion,
        results=paginated_results,
        query=query,
        current_page=page,
        total_pages=total_pages,
        pagination_range=pagination_range,
    )


@app.route('/')
def home():
    return render_template('search.html')

# Route to handle form submission
#@app.route('/submit_article', methods=['POST'])
# def submit_article():
#     title = request.form['title']
#     body = request.form['body']
#     tags = request.form['tags']
#
#     article_url = create_url_from_title(title)
#
#
#     doc_url_dict = DocURLDict()
#     docID = doc_url_dict.store(article_url)
#
#     # Process the newly added article for indexing
#     document = row_to_document({"title": title, "text": body, "tags": tags, "url": ""})
#     lexicon.save_lexicon()  # Update lexicon with new word
#     document.store(fwd_index)  # Store in forward index
#     build_word_presences()
#     index_word_presences()
#
#     return "Article added successfully!"

if __name__ == "__main__":
    app.run(debug=True)
