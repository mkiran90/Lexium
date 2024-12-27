from src.document.DocURLDict import DocURLDict
from src.document.MetaIndex import MetaIndex
from src.forward_index.ForwardIndex import ForwardIndex
from src.inverted_index.InvertedIndex import InvertedIndex
from src.lexicon_gen.Lexicon import Lexicon
from src.lexicon_gen.WordEmbedding import WordEmbedding
from src.new_articles.adding_articles import ArticleAddition
from src.util.util_functions import get_nlp, get_word2vec

from flask import Flask, render_template, request

lexicon = Lexicon()
fwd_index = ForwardIndex()
inv_index = InvertedIndex()
url_dict = DocURLDict()
model = get_word2vec()
word_embedding = WordEmbedding()
meta = MetaIndex()
nlp = get_nlp()


Adder = ArticleAddition(lexicon,fwd_index,inv_index,url_dict,model,word_embedding,meta,nlp)

url = ""
Adder.add_article(url=url)
lexicon.save_lexicon()



addService = Flask(__name__)

@addService.route('/add_articles', methods=['GET', 'POST'])
def add_articles():
    if request.method == 'POST':
        title = request.form.get('title')
        body = request.form.get('body')
        url = request.form.get('url')
        tab = request.form.get('tab') 

        
        if tab == 'content' and title and body and url: 
            Adder.add_article(url)  
            return "Article with content added successfully."
        elif tab == 'link' and url:  
            Adder.placeholder_add(url) 
            return "URL added successfully."

    return render_template('add_articles.html')

if __name__ == '__main__':
    addService.run(port=5001, debug=True)
