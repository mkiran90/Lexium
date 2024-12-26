from src.document.DocURLDict import DocURLDict
from src.document.MetaIndex import MetaIndex
from src.forward_index.ForwardIndex import ForwardIndex
from src.inverted_index.InvertedIndex import InvertedIndex
from src.lexicon_gen.Lexicon import Lexicon
from src.lexicon_gen.WordEmbedding import WordEmbedding
from src.new_articles.adding_articles import ArticleAddition
from src.util.util_functions import get_nlp, get_word2vec

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