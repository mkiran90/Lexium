import os

from flask import Flask, request, render_template, redirect, url_for
from spellchecker import SpellChecker
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

    images = [
        {
            "src": "https://images.unsplash.com/photo-1631451095765-2c91616fc9e6?crop=entropy&cs=tinysrgb&fit=max&fm=jpg&ixid=MnwxNDU4OXwwfDF8cmFuZG9tfHx8fHx8fHx8MTYzNDA0OTI3Nw&ixlib=rb-1.2.1&q=80&w=400",
            "alt": "Volcano and lava field against a stormy sky",
            "title": "Mountains and volcanos"
        },
        {
            "src": "https://images.unsplash.com/photo-1633621533308-8760aefb5521?crop=entropy&cs=tinysrgb&fit=max&fm=jpg&ixid=MnwxNDU4OXwwfDF8cmFuZG9tfHx8fHx8fHx8MTYzNDA1MjAyMQ&ixlib=rb-1.2.1&q=80&w=400",
            "alt": "Guy on a bike ok a wooden bridge with a forest backdrop",
            "title": "Adventure getaways"
        },
        {
            "src": "https://images.unsplash.com/photo-1633635146842-12d386e64058?crop=entropy&cs=tinysrgb&fit=max&fm=jpg&ixid=MnwxNDU4OXwwfDF8cmFuZG9tfHx8fHx8fHx8MTYzNDA1MjA5OA&ixlib=rb-1.2.1&q=80&w=400",
            "alt": "Person standing alone in a misty forest",
            "title": "Forest escapes"
        },
        {
            "src": "https://images.unsplash.com/photo-1568444438385-ece31a33ce78?crop=entropy&cs=tinysrgb&fit=max&fm=jpg&ixid=MnwxNDU4OXwwfDF8cmFuZG9tfHx8fHx8fHx8MTYzNDA1MjA5OA&ixlib=rb-1.2.1&q=80&w=400",
            "alt": "Person hiking on a trail through mountains while taking a photo with phone",
            "title": "Hiking trails"
        },
        {
            "src": "https://images.unsplash.com/photo-1633515257379-5fda985bd57a?crop=entropy&cs=tinysrgb&fit=max&fm=jpg&ixid=MnwxNDU4OXwwfDF8cmFuZG9tfHx8fHx8fHx8MTYzNDA1MjA5OA&ixlib=rb-1.2.1&q=80&w=400",
            "alt": "Street scene with person walking and others on motorbikes, all wearing masks",
            "title": "Street scenes"
        },
        {
            "src": "https://images.unsplash.com/photo-1633209931146-260ce0d16e22?crop=entropy&cs=tinysrgb&fit=max&fm=jpg&ixid=MnwxNDU4OXwwfDF8cmFuZG9tfHx8fHx8fHx8MTYzNDA1MjA5OA&ixlib=rb-1.2.1&q=80&w=400",
            "alt": "Fashionable-looking girl with blond hair and pink sunglasses",
            "title": "Trending"
        },
    ]
      
    query = request.args.get('query', '').strip()
    print(f"User query: {query}")

    if not query:
        return redirect(url_for('no_result'))

    
    spell = SpellChecker()

    try:
        result_gen = ResultGeneration(query, nlp, inverted_index, forward_index, lexicon, urlDict, meta_index, word_embedding)
    except Exception as e:
        print(f"Error initializing ResultGeneration: {e}")
        return redirect(url_for('no_result'))

    
    words = query.split()
    corrected_words = [spell.correction(word) for word in words]

   
    corrected_words = [word for word in corrected_words if word is not None]

  
    corrected_query_str = " ".join(corrected_words) if corrected_words else query

    show_suggestion = bool(corrected_query_str) and corrected_query_str != query
 
   
    urls = result_gen.get_search_results()

    # Case 1: No URLs and no typo suggestions
    if not urls and not show_suggestion:
        return redirect(url_for('no_result'))

    # Case 2: No URLs but there is a typo so give suggestions
    if not urls and show_suggestion:
        return render_template(
            'no_result.html',
            query=query,
            corrected_query=corrected_query_str,
            show_suggestion=True,
        )

    # Pagination thingy
    docs_per_page = 10
    total_docs = len(urls)
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
    paginated_urls = urls[start_index:end_index]

    # Case 3: URLs and typo suggestions
    if urls and show_suggestion:
        return render_template(
            'results.html',
            results=[{
                "title": extract_title_from_link(url),
                "link": url,
             
            } for url in paginated_urls],
            query=query,
            corrected_query=corrected_query_str, 
            show_suggestion=True,
            current_page=page,  
            total_pages=total_pages,  
            pagination_range=pagination_range,  
            images=images
        )

    # Case 4: URLs and no typo suggestions
    if urls and not show_suggestion:
        return render_template(
            'results.html',
            results=[{
                "title": extract_title_from_link(url),
                "link": url,
                
            } for url in paginated_urls],
            query=query,
            corrected_query=None,  
            show_suggestion=False,
            current_page=page, 
            total_pages=total_pages,  
            pagination_range=pagination_range, 
            images = images 
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
