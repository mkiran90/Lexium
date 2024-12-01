import re

def is_valid_text(token):
    return (
            (is_valid_pattern(token.text) and not token.is_stop)
            or
            (
                not token.is_stop
                and not token.is_punct
                and not token.is_digit
                and len(token.text) <= 15
                and not token.is_space
                and not token.like_url
                and not token.like_email
                and not is_invalid_pattern(token.text)
            )
    )


def is_valid_title(token):
    return not token.is_stop and not token.is_punct


def is_valid_pattern(text):
    anum_pattern = r'^[a-zA-Z]+[0-9]*$'
    anum_hyph_pattern = r'^[a-zA-Z]+-*[a-zA-Z0-9.]+$'
    return re.match(anum_pattern, text) or re.match(anum_hyph_pattern, text)


def is_invalid_pattern(text):
    invalid_num_pattern = r'^[0-9\w_]'
    superscript_pattern = r'^[\u00B9\u00B2\u00B3\u2070-\u2079\u2080-\u2089]'
    return re.match(invalid_num_pattern, text) or re.match(superscript_pattern, text)
