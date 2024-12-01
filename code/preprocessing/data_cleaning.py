import spacy

nlp = spacy.load("en_core_web_md")

# string of cleaned tags, separated by spaces.
def clean_tags(text):

    # the string stored in the csv is the string representation of a list of tags
    tag_list:list[str] = eval(text)

    clean_tags = [tag.lower() for tag in tag_list]

    return " ".join(clean_tags)

# string of cleaned title words, separated by spaces
def clean_title(text):
    doc = nlp(str(text))

    clean_tokens = [token.lemma_.lower() for token in doc if not token.is_punct and not token.is_stop]

    return " ".join(clean_tokens)

#overall validity (to let through or not)
def is_valid(token):

    # CERTAIN VALID (the second part captures meaningul named entities that have appeared multiple times over intent, C++ google.com etc)
    if (token.is_alpha and not token.is_stop) or (not token.is_oov and not token.is_stop and any([c.isalpha() for c in token.text])):
        return True

    # CERTAIN INVALID
    if token.is_stop or all(not c.isalpha() for c in token.text) or token.like_url:
        return False

    # GREY AREA

    # non-alphabetical words with this much length? statistically certain to be code blocks.
    if len(token.text) > 15:
        return False

    # this matches for purely alphanumeric strings OR strings that have the same special character (- or .) repeated indefinitely
    alpha, digit, special = 0, 0, 0
    last_special = '\n'
    same_special = True
    for c in token.text:
        if c.isalpha():
            alpha += 1
        elif '0' <= c <= '9':
            digit += 1
        else:
            special += 1
            if last_special == '\n':
                last_special = c
            else:
                if c != last_special:
                    same_special = False

    # purely alpha numeric string with size < 15 OR one special character OR U.S.A U-S-A etc.
    if special <= 1 or (same_special and last_special in ['-', '.']):
        return True

    # default
    return False

# string of cleaned body words, separated by spaces
def clean_body(text):
    doc = nlp(str(text))

    clean_tokens = [token.lemma_.lower() for token in doc if is_valid(token)]

    return " ".join(clean_tokens)



