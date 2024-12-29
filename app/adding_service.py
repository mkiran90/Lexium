from src.meta.ResultMetaIndex import ResultMetaIndex
from src.meta.RankingMetaIndex import RankingMetaIndex
from src.forward_index.ForwardIndex import ForwardIndex
from src.inverted_index.InvertedIndex import InvertedIndex
from src.lexicon_gen.Lexicon import Lexicon
from src.lexicon_gen.WordEmbedding import WordEmbedding
from src.new_articles.adding_articles import ArticleAddition
from src.util.util_functions import get_nlp, get_word2vec

from flask import Flask, render_template, request, jsonify

import time  # remove this just for testing 

lexicon = Lexicon()
fwd_index = ForwardIndex()
inv_index = InvertedIndex()
result_meta = ResultMetaIndex()

model = get_word2vec()
word_embedding = WordEmbedding()
rank_meta = RankingMetaIndex()
nlp = get_nlp()

Adder = ArticleAddition(lexicon, fwd_index, inv_index, result_meta, model, word_embedding, rank_meta, nlp)

addService = Flask(__name__)

def handle_get():
    return render_template('add_articles.html', status="")

def handle_post():
    response = {"status": "error", "message": ""}
    url = request.form.get('url')
    urlonly = request.form.get('urlonly')
    title = request.form.get('title')
    body = request.form.get('body')
    print('doo')

    try:
        if title and body and url:
           
            Adder.add_with_content(title, body, url)
            response["status"] = "success"
        elif urlonly:
            print(urlonly)
            print('adding')
            Adder.add_with_url(urlonly)
            time.sleep(5)  # remove this just for testing 
            response["status"] = "success"
            print('added')
    except Exception as e:
        print(f"Error: {e}")
        response["status"] = "error"
        response["message"] = str(e)

    return response

@addService.route('/', methods=['GET', 'POST'])
def home():
    if request.method == 'GET':
        return handle_get()  
    elif request.method == 'POST':
        result = handle_post()  
        return jsonify(result)

if __name__ == '__main__':
    addService.run(port=5001, debug=True)
