from itertools import combinations

def _get_position_pairs(t1_positions: list, t2_positions: list):
    pairs = []

    if not t1_positions or not t2_positions:
        return pairs

    i, j = 0, 0

    '''
        * t1_positions, t2_positions are sorted unsigned integer lists.
        * two pointer approach.
        * Possible scenarios:
            - NEXT position in t1_positions is CLOSER to the current position of t2_positions
            - NEXT position in t2_positions is CLOSER to the current position of t1_positions
            - Both current positions are closest to each other.
    '''

    while i < len(t1_positions) and j < len(t2_positions):

        current_diff = t2_positions[j] - t1_positions[i] # Can be positive or negative (negative means that the pair is in the wrong order)
        next_diff = float('inf')

        # This is to eliminate pairs with wrong order.
        while current_diff < 0 and j + 1 < len(t2_positions):
            j += 1
            current_diff = t2_positions[j] - t1_positions[i]

        # If the SECOND condition of the loop above becomes false, that means the query pair has no pair in the document which is in the correct order.
        if current_diff < 0:
            break

        # From here onwards, current_diff will be positive ONLY.
        if i + 1 < len(t1_positions):
            next_diff = t2_positions[j] - t1_positions[i + 1]       # Can be positive or negative.

            # This means current pair is the closest possible pair which is in the correct order
            if next_diff < 0:
                pairs.append((t1_positions[i], t2_positions[j]))
                i += 1

                # 2nd list has no more positions to make pairs with.
                if not j + 1 < len(t2_positions):
                    break

                j += 1
                continue


        while 0 < next_diff < current_diff:
            current_diff = next_diff
            i += 1

            if i + 1 < len(t1_positions):
                next_diff = t2_positions[j] - t1_positions[i + 1]



        pairs.append((t1_positions[i], t2_positions[j]))

        if i + 1 < len(t1_positions) and j + 1 < len(t2_positions):
            i += 1
            j += 1
        else:
            break


    return pairs

def _get_query_pairs(query_terms: list):
    if len(query_terms) < 2:
        return

    return list(combinations(query_terms, 2))

# Range [1, 1.5]
def get_title_prox_score(presenceMap, docID: int):
    if len(presenceMap) == 1:
        return  1
    score = 1
    discounted_words = 0

    pairs = _get_query_pairs(presenceMap.keys())

    if not pairs:
        return score

    for pair in pairs:

        try:
            t1_title_positions = presenceMap[pair[0]].docMap[docID].title_positions
            t2_title_positions = presenceMap[pair[1]].docMap[docID].title_positions

        except KeyError as e:
            discounted_words += 1
            continue


        title_proximity = _calculate_proximity(t1_title_positions, t2_title_positions)

        score += (3 / (title_proximity + 1 + 3 * discounted_words))

    # If none of the pairs exist in the title.
    if len(pairs) <= discounted_words:
        return 1

    score = score / (len(pairs) - discounted_words)
    return score

# Range [1, 1.5]
def get_body_prox_score(presenceMap, docID: int):
    score = 1
    discounted_words = 0

    pairs: list = _get_query_pairs(presenceMap.keys())

    if len(presenceMap) == 1 or not pairs:
        return  score

    for pair in pairs:

        try:
            t1_body_positions = presenceMap[pair[0]].docMap[docID].body_positions
            t2_body_positions = presenceMap[pair[1]].docMap[docID].body_positions

        except KeyError as e:
            discounted_words += 1
            continue

        body_proximity = _calculate_proximity(t1_body_positions, t2_body_positions)

        score += 1 / (body_proximity + 1)

    # None of the pairs exist in the document.
    if len(pairs) <= discounted_words:
        return 1

    score += score / (len(pairs) + discounted_words)
    return score



def _calculate_proximity(t1_positions, t2_positions):
    proximity_sum = 0

    position_pairs: list = _get_position_pairs(t1_positions, t2_positions)


    if not position_pairs:
        return float('inf')

    for pos_pair in position_pairs:
        difference = pos_pair[1] - pos_pair[0]
        proximity_sum += difference

    return proximity_sum / len(position_pairs)

