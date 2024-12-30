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

# Initialize necessary components
nlp = get_nlp()
inverted_index = InvertedIndex()
forward_index = ForwardIndex()
lexicon = Lexicon()
result_meta = ResultMetaIndex()
rank_meta = RankingMetaIndex()
word_embedding = WordEmbedding()

# Global storage for query, results, and current page
search_state = {
    'query': None,
    'results': None,
    'current_page': 1,
}

#fetch corrected query using the spellChecker
def fetch_and_correct_query(query):
    
    spell = SpellChecker()
    words = query.split()
    corrected_query = " ".join([spell.correction(word) or word for word in words])
    return corrected_query, corrected_query != query

#fetch results
def fetch_results(query):
   
    if search_state['query'] == query:
        return search_state['results']

    try:
        result_gen = ResultGeneration(query, nlp, inverted_index, forward_index, lexicon, result_meta, rank_meta, word_embedding)
        articles = result_gen.get_search_results()
    except Exception as e:
        print(f"Error: {e}")
        articles = []

    search_state['query'] = query
    search_state['results'] = articles
    return articles

#pagination 
def paginate_results(articles, page, docs_per_page):
  
    total_docs = len(articles)
    total_pages = max((total_docs + docs_per_page - 1) // docs_per_page, 1)
    page = max(1, min(page, total_pages))

    start_index = (page - 1) * docs_per_page
    end_index = start_index + docs_per_page
    return articles[start_index:end_index], total_pages

@app.route('/results')
def results():
    query = request.args.get('query', '').strip()
    page = int(request.args.get('page', search_state['current_page']))
    if not query:
        return redirect(url_for('no_result'))

    if page == 1:
        corrected_query, show_suggestion = fetch_and_correct_query(query)
    else:
        corrected_query, show_suggestion = query, False

    articles = fetch_results(query)
    docs_per_page = 9
    search_state['current_page'] = page
    paginated_urls, total_pages = paginate_results(articles, page, docs_per_page)
    pagination_range = list(range(max(1, page - 2), min(total_pages + 1, page + 3)))
    default_img_url = url_for('static', filename='img/default.png')


    print(query)
    print(corrected_query)
    
    #if no result no suggestion
    if not articles and not show_suggestion:
        return redirect(url_for('no_result'))
    
    #if no result but there is suggestion
    if not articles and show_suggestion:
        return render_template(
            'no_result.html',
            query=query,
            corrected_query=corrected_query,
            show_suggestion=True,
        )
    
    #if artciles are present 
    return render_template(
        'results.html',
        results=[{
            "title": title,
            "link": url,
            "img_url": img_url or default_img_url,
        } for url, img_url, title in paginated_urls],
        query=query,
        corrected_query=corrected_query if show_suggestion else None,
        show_suggestion=show_suggestion,
        current_page=page,
        total_pages=total_pages,
        pagination_range=pagination_range,
    )


@app.route('/no_result')
def no_result():
     return render_template('no_result.html', message="No results found.")

@app.route('/')
def home():
    return render_template('search.html')

if __name__ == "__main__":
    app.run(port=5000, debug=True)
