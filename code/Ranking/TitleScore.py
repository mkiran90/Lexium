
from code.forward_index.ForwardIndex import ForwardIndex

forward_index = ForwardIndex()

def get_title_score(presence_map, doc_id):

    words_in_title = 0

    for (word_id, presence) in presence_map.items():
        words_in_title += presence.docMap[doc_id].title_frequency()

    total_title_words = len(forward_index.get(doc_id).title_words)

    if total_title_words == 0:
        return 0

    return words_in_title/total_title_words


