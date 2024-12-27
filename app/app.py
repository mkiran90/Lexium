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

def extract_info_from_link(link):
    try:
        
        if "medium.com" not in link:
            return {"title": "Invalid link", "author": "Invalid link"}

   
        split_link = link.split("/")

        # Case 1: (https://medium.com/@author/title)
        if "@" in split_link[3]:
            author = split_link[3].lstrip("@")  
            if len(split_link) > 4:
                title_with_sequence = split_link[4]
                
                title = ' '.join(title_with_sequence.split('-')[:-1]).strip()
            else:
                title = "Invalid title"

        # Case 2: (https://author.medium.com/title)
        elif  split_link[2].count('.') == 2 :
            author = split_link[2].split('.')[0]  
            if len(split_link) > 3:
                title_with_sequence = split_link[3]
                
                title = ' '.join(title_with_sequence.split('-')[:-1]).strip()
            else:
                title = "Invalid title"

         # Case 3: (https://medium.com/author/title)
        else:
            author = split_link[3] 
            author = ' '.join(author.split('-')[:-1]).strip() # author name
            if len(split_link) > 4:
                title_with_sequence = split_link[4]
                
                title = ' '.join(title_with_sequence.split('-')[:-1]).strip()
            else:
                title = "Invalid title"

        return {"title": title, "author": author}

    except IndexError:
        return {"title": "Invalid link", "author": "Invalid link"}
    except Exception as e:
        print(f"Error: {e}")
        return {"title": "Invalid link", "author": "Invalid link"}

    
def extract_title_from_link(link):
    return extract_info_from_link(link)["title"]

def extract_author_from_link(link):
    return extract_info_from_link(link)["author"]


# Fixed the function name and logic
def extract_author_from_link(link):
    return extract_info_from_link(link)["author"] 

@app.route('/results')
def results():
    query = request.args.get('query', '').strip()  # Clean up query from request
    print(f"User query: {query}")

    # If no query entered, show no result page
    if not query:
        return redirect(url_for('no_result'))

    # Preprocess the query: split it into words and pass it to ResultGeneration
    query_words = query.split()  # Split query into words

    # Create ResultGeneration object and correct the query words
    result_gen = ResultGeneration(query_words, nlp, inverted_index, forward_index, lexicon, urlDict, meta_index, word_embedding)
    corrected_query = result_gen._correct_query_words()  # Get corrected words
    corrected_query_str = " ".join(corrected_query)
    print(f"Corrected query: {corrected_query_str}")

    # Get search results
    urls = result_gen.get_search_results()

    # If no results, handle typo suggestion if correction exists
    if not urls:
        if corrected_query_str != query:  # Only suggest if query was corrected
            return redirect(url_for('no_result', query=query, corrected_query=corrected_query_str))
        else:
            return redirect(url_for('no_result'))  # No typo suggestion

    # Handle case where results are found
    docs_per_page = 10
    total_docs = len(urls)
    total_pages = (total_docs + docs_per_page - 1) // docs_per_page

    # Ensure the page number is valid
    page = int(request.args.get('page', 1))  # Default to page 1
    if page < 1 or page > total_pages:
        return redirect(url_for('no_result'))

    # Pagination range
    pagination_range = list(range(max(1, page - 2), min(total_pages + 1, page + 3)))

    start_index = (page - 1) * docs_per_page
    end_index = start_index + docs_per_page
    paginated_urls = urls[start_index:end_index]

    try:
        # Generate results for the current page
        paginated_results = [
            {
                "title": extract_title_from_link(url),
                "link": url,
                "author": extract_author_from_link(url),
            }
            for url in paginated_urls
        ]
    except Exception as e:
        print(f"Error fetching results: {e}")
        return redirect(url_for('no_result'))

    # Render the results page
    return render_template(
        'results.html',
        results=paginated_results,
        query=query,
        current_page=page,
        total_pages=total_pages,
        pagination_range=pagination_range,
    )


@app.route('/no_result')
def no_result():
    query = request.args.get('query', '').strip()
    corrected_query = request.args.get('corrected_query', '').strip()

    # Check if corrected query exists and suggest it
    typo_suggestion = None
    if corrected_query and corrected_query.lower() != query.lower():
        typo_suggestion = f'Did you mean "{corrected_query}"?'

    return render_template('no_result.html', message="No results found for your query.", typo_suggestion=typo_suggestion, corrected_query=corrected_query)


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
 app.run(port=5000, debug=True)
