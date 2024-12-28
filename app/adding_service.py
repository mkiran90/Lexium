from src.meta.ResultMetaIndex import ResultMetaIndex
from src.meta.RankingMetaIndex import RankingMetaIndex
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
result_meta = ResultMetaIndex()

#TODO: model = get_word2vec()
model = None
word_embedding = WordEmbedding()
rank_meta = RankingMetaIndex()
nlp = get_nlp()


Adder = ArticleAddition(lexicon,fwd_index,inv_index,result_meta,model,word_embedding,rank_meta,nlp)


lexicon.save_lexicon()



addService = Flask(__name__)

@addService.route('/' , methods=['GET', 'POST'])
def home():
    print("Doob")
    if request.method == 'POST':
        title = request.form.get('title')
        body = request.form.get('body')
        url = request.form.get('url')
        tab = request.form.get('tab')

        if tab == 'content' and title and body and url:
            Adder.placeholder_add_with_content(title, body, url)
            print("Yeah")
            return "Article with content added successfully."
        elif tab == 'link' and url:
            print("No")
            Adder.placeholder_add(url)
            return "URL added successfully."

    return render_template('add_articles.html')




if __name__ == '__main__':
    addService.run(port=5001, debug=True)
