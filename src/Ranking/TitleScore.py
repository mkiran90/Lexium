
def get_title_score(presence_map, doc_id):

    words_in_title = 0

    for (word_id, presence) in presence_map.items():

        try:
            words_in_title += presence.docMap[doc_id].title_frequency()

        except KeyError:
            continue

    return words_in_title