import re
import requests


def get_query(q):
    """Turn the user entry q into a Elasticsearch query."""
    queries = []
    if ':' in q:
        query_list, keywords = handle_specific_field_request(q)
        queries.extend(query_list)
    else:
        queries.append(get_regular_query(q))
        keywords = q.split(' ')
    if len(queries) == 0:
        raise RuntimeError('No query.')
    elif len(queries) == 1:
        return queries[0], keywords
    else:
        return {'bool': {'should': queries}}, keywords


def handle_specific_field_request(q):
    """Get queries when user specified field by using a colon."""
    parts = q.split(':')
    fields = []
    keywords_sets = []
    for part in parts[:-1]:
        words = part.split(' ')
        fields.append(words[-1].strip(' '))
        if len(words[:-1]) > 0:
            keywords_sets.append(' '.join(words[:-1]).strip(' '))
    keywords_sets.append(parts[-1].strip(' '))
    # Edge case when question starts with a normal search term
    if len(keywords_sets) > len(fields):
        fields = [u'alles'] + fields
    queries = []
    keywords = []
    for i in range(len(fields)):
        if fields[i] == u'alles':
            queries.append(get_regular_query(keywords_sets[i]))
        else:
            queries.append(get_specific_field_query(fields[i], keywords_sets[i]))
        for keyword in keywords_sets[i].split(' '):
            keywords.append(keyword)
    return queries, keywords


def get_specific_field_query(field, keywords):
    """Return the query if user wants to search a specific field."""
    return {'match': {field: {'query': keywords}}}


def get_regular_query(keywords):
    """Return the query if user wants to search in all fields."""
    return {'multi_match': {'query': keywords,
                            'fields': ['naam^3', 'datum^3', 'inhoud^2', 'getuigen', 'bron']
                            }
            }


def post_query(query, index, start, size):
    """Post the query to the localhost Elasticsearch server."""
    payload = {'query': query,
               'from': start,
               'size': size}
    resp = requests.post('http://localhost:9200/{}/_search'.format(index), json=payload)
    resp.raise_for_status()
    return resp


def handle_results(r, keywords, keys):
    raw = r.json()
    hits_total = raw['hits']['total']
    res = []
    for hit in raw['hits']['hits']:
        item = {key: None for key in keys}
        item['score'] = hit['_score']
        item['id'] = hit['_id']
        for key in keys:
            if key in hit['_source'] and hit['_source'][key] is not None:
                item[key] = hit['_source'][key]
                for keyword in keywords:
                    if keyword in item[key].lower():
                        start = [m.start() for m in re.finditer(keyword, item[key].lower())]
                        end = [m.end() for m in re.finditer(keyword, item[key].lower())]
                        i = 0
                        a = item[key][:start[i]] + u'<em>' + item[key][start[i]:end[i]] + u'</em>'
                        for i in range(1, len(start)):
                            a += item[key][end[i-1]:start[i]]+ u'<em>' + item[key][start[i]:end[i]] + u'</em>'
                        a += item[key][end[i]:]
                        item[key] = a
        res.append(item)
    return res, hits_total


def get_page_range(hits_total, page, cards_per_page):
    page_total = hits_total // cards_per_page + 1 * (hits_total % cards_per_page != 0)
    ext = 3
    first_item = max((page - ext, 1))
    last_item = min((page + ext, page_total))
    if page < ext+1:
        last_item = min((last_item + ext+1 - page, page_total))
    if page_total - page < ext+1:
        first_item = max((first_item - ext + (page_total - page), 1))
    return list(range(first_item, last_item + 1))


def get_names_list(q):
    payload = {"size": 0,
               "aggs": {"op_naam": {"terms": {"field": "naam_keyword",
                                              "order": {"_key": "asc"},
                                              "include": "{}.*".format(q.title()),
                                              "size": 2000}
               }}}
    resp = requests.post('http://localhost:9200/namenindex/_search', json=payload)
    resp.raise_for_status()
    raw = resp.json()
    names_list = raw['aggregations']['op_naam']['buckets']
    return names_list


def is_elasticsearch_reachable() -> bool:
    """Return a boolean whether the Elasticsearch service is available on localhost."""
    try:
        resp = requests.get('http://localhost:9200')
        resp.raise_for_status()
    except requests.exceptions.ConnectionError:
        return False
    else:
        return True
