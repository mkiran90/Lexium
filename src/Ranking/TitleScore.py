from torchgen.api.cpp import return_type


def get_title_score(presence_map, doc_id, doc_meta):

    words_in_title = 0

    for (word_id, presence) in presence_map.items():

        try:
            words_in_title += presence.docMap[doc_id].title_frequency()

        except KeyError:
            continue

    return words_in_title

    # total_title_words = doc_meta.title_length
    #
    # if total_title_words == 0:
    #     return 0
    #
    # return words_in_title/total_title_words


