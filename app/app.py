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

def extract_title_from_link(link):
    try:
       
        title_with_sequence = link.split("/")[-1]
  
        title_parts = title_with_sequence.split("-")
        
        if title_parts[-1].isalnum():  
            title_parts.pop()
        
        title = ' '.join(title_parts).title()
        
        return title

    except Exception as e:
        print(f"Error: {e}")
        return "Invalid link"



@app.route('/results')
def results():
   
    query = request.args.get('query', '').strip()
    print(f"User query: {query}")

    if not query:
        return redirect(url_for('no_result'))

    spell = SpellChecker()

    try:
        result_gen = ResultGeneration(query, nlp, inverted_index, forward_index, lexicon, result_meta, rank_meta, word_embedding)
    except Exception as e:
        print(f"Error initializing ResultGeneration: {e}")
        return redirect(url_for('no_result'))

    words = query.split()
    corrected_words = [spell.correction(word) for word in words]
    corrected_words = [word for word in corrected_words if word is not None]
    corrected_query_str = " ".join(corrected_words) if corrected_words else query

    show_suggestion = bool(corrected_query_str) and corrected_query_str != query

    
    
    articles = result_gen.get_search_results()

    # Case 1: No URLs and no typo suggestions
    if not articles and not show_suggestion:
        return redirect(url_for('no_result'))

    # Case 2: No URLs but there is a typo, so give suggestions
    if not articles and show_suggestion:
        return render_template(
            'no_result.html',
            query=query,
            corrected_query=corrected_query_str,
            show_suggestion=True,
        )

    # Pagination thing
    docs_per_page = 9
    total_docs = len(articles)
    total_pages = max((total_docs + docs_per_page - 1) // docs_per_page, 1)

    try:
        page = int(request.args.get('page', 1))
        if page < 1 or page > total_pages:
            raise ValueError
    except ValueError:
        return redirect(url_for('no_result'))

    pagination_range = list(range(max(1, page - 2), min(total_pages + 1, page + 3)))
    start_index = (page - 1) * docs_per_page
    end_index = start_index + docs_per_page
    paginated_urls = articles[start_index:end_index]

    default_img_url = url_for('static', filename='img/default.png')

    # Case 3: URLs and typo suggestions
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

    # Case 4: URLs and no typo suggestions
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
