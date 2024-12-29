from flask import Flask, request, render_template, redirect, url_for
from spellchecker import SpellChecker

from src.meta.ResultMetaIndex import ResultMetaIndex
from src.meta.RankingMetaIndex import RankingMetaIndex
from src.forward_index.ForwardIndex import ForwardIndex
from src.inverted_index.InvertedIndex import InvertedIndex
from src.lexicon_gen.Lexicon import Lexicon
from src.lexicon_gen.WordEmbedding import WordEmbedding
from src.querying.ResultGeneration import ResultGeneration
from src.util.util_functions import get_nlp

app = Flask(__name__)

nlp = get_nlp()
inverted_index = InvertedIndex()
forward_index = ForwardIndex()
lexicon = Lexicon()
result_meta = ResultMetaIndex()
rank_meta = RankingMetaIndex()
word_embedding = WordEmbedding()

# Global storage for query, results, and current page
search = {
    'query': None,
    'results': None,
    'current_page': 1,  # Store the current page
}

def fetch_and_correct_results(query):
    # If query same return the global results
    if search['query'] == query:
        return search['results'], query, False

    try:
        result_gen = ResultGeneration(query, nlp, inverted_index, forward_index, lexicon, result_meta, rank_meta, word_embedding)
    except Exception as e:
        print(f"Error initializing ResultGeneration: {e}")
        return [], "", False

    spell = SpellChecker()
    words = query.split()
    corrected_words = [spell.correction(word) for word in words]
    corrected_query_str = " ".join([word for word in corrected_words if word is not None]) if corrected_words else query

    show_suggestion = corrected_query_str != query
    
    # getting the articles
    articles = result_gen.get_search_results()

    # Store the query, results, and reset current page to 1 (default)
    search['query'] = query
    search['results'] = articles
    search['current_page'] = 1  # Reset to the first page when new query is made

    return articles, corrected_query_str, show_suggestion


def paginate_results(articles, page, docs_per_page):
    """Handle pagination of results."""
    total_docs = len(articles)
    total_pages = max((total_docs + docs_per_page - 1) // docs_per_page, 1)

    page = max(1, min(page, total_pages))

    start_index = (page - 1) * docs_per_page
    end_index = start_index + docs_per_page
    paginated_urls = articles[start_index:end_index]

    return paginated_urls, total_pages


@app.route('/results')
def results():
    query = request.args.get('query', '').strip()
    print(f"User query: {query}")

    if not query:
        return redirect(url_for('no_result'))

    # Fetch results for the query
    articles, corrected_query_str, show_suggestion = fetch_and_correct_results(query)

    # Pagination parameters
    docs_per_page = 9
    page = int(request.args.get('page', search['current_page']))  # Use stored page if not provided
    search['current_page'] = page  # Update the stored page

    # Paginate the results
    paginated_urls, total_pages = paginate_results(articles, page, docs_per_page)
    pagination_range = list(range(max(1, page - 2), min(total_pages + 1, page + 3)))
    default_img_url = url_for('static', filename='img/default.png')

    # Case 1: No articles and no typo suggestions
    if not articles and not show_suggestion:
        return redirect(url_for('no_result'))

    # Case 2: No articles but there is a typo, so give suggestions
    if not articles and show_suggestion:
        return render_template(
            'no_result.html',
            query=query,
            corrected_query=corrected_query_str,
            show_suggestion=True,
        )

    # Case 3: Articles and typo suggestions
    if articles and show_suggestion:
        return render_template(
            'results.html',
            results=[{
                "title": title,
                "link": url,
                "img_url": img_url if img_url else default_img_url,
            } for url, img_url, title in paginated_urls],
            query=query,
            corrected_query=corrected_query_str,
            show_suggestion=True,
            current_page=page,
            total_pages=total_pages,
            pagination_range=pagination_range,
        )

    # Case 4: Articles and no typo suggestions
    if articles and not show_suggestion:
        return render_template(
            'results.html',
            results=[{
                "title": title,
                "link": url,
                "img_url": img_url if img_url else default_img_url,
            } for url, img_url, title in paginated_urls],
            query=query,
            corrected_query=None,
            show_suggestion=False,
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


if __name__ == "__main__": 
    app.run(port=5000, debug=True)
