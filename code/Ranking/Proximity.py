from itertools import combinations
from code.inverted_index.InvertedIndex import InvertedIndex

inverted_index = InvertedIndex()


def _get_position_pairs(t1_positions: list, t2_positions: list):
    pairs = []

    if not t1_positions or not t2_positions:
        return pairs

    i, j = 0, 0

    '''
        * t1_positions, t2_positions are sorted unsigned integer lists.
        * two pointer approach.
        * Three scenarios:
            - NEXT position in t1_positions is CLOSER to the current position of t2_positions
            - NEXT position in t2_positions is CLOSER to the current position of t1_positions
            - Both current positions are closest to each other.
    '''

    while i < len(t1_positions) and j < len(t2_positions):

        # Make sure j+1 is within bounds
        if j + 1 < len(t2_positions):
            next_diff = abs(t1_positions[i] - t2_positions[j + 1])
        else:
            next_diff = float('inf')

        current_diff = abs(t1_positions[i] - t2_positions[j])

        while j + 1 < len(t2_positions) and current_diff > next_diff:
            j += 1
            if j + 1 < len(t2_positions):
                next_diff = abs(t1_positions[i] - t2_positions[j + 1])
            current_diff = abs(t1_positions[i] - t2_positions[j])

        if i + 1 < len(t1_positions):
            next_diff = abs(t1_positions[i + 1] - t2_positions[j])
        else:
            next_diff = float('inf')

        while i + 1 < len(t1_positions) and current_diff > next_diff:
            i += 1
            if i + 1 < len(t1_positions):
                next_diff = abs(t1_positions[i + 1] - t2_positions[j])
            current_diff = abs(t1_positions[i] - t2_positions[j])

        pairs.append((t1_positions[i], t2_positions[j]))
        i += 1
        t2_positions.pop(j)

        if j >= len(t2_positions):
            return pairs

    return pairs


def _get_query_pairs(query_terms: list):
    return list(combinations(query_terms, 2))


def get_proximity_score(presenceMap, docID: int):
    score = 0
    pairs: list = _get_query_pairs(presenceMap.keys())

    for pair in pairs:
        t1_body_positions = presenceMap[pair[0]].docMap[docID].body_positions

        t2_body_positions = presenceMap[pair[1]].docMap[docID].body_positions

        t1_title_positions = presenceMap[pair[0]].docMap[docID].title_positions
        t2_title_positions = presenceMap[pair[1]].docMap[docID].title_positions

        title_proximity = _calculate_proximity(t1_title_positions, t2_title_positions)
        body_proximity = _calculate_proximity(t1_body_positions, t2_body_positions)

        score += (1.5 * 1 / (title_proximity + 1)) + 1 / (body_proximity + 1)

    score = score / len(pairs)

    return score


def _calculate_proximity(t1_positions, t2_positions):
    proximity_sum = 0

    position_pairs: list = _get_position_pairs(t1_positions, t2_positions)

    if not position_pairs:
        return float('inf')

    for pos_pair in position_pairs:
        proximity_sum = abs(pos_pair[0] - pos_pair[1])

    return proximity_sum / len(position_pairs)
