import re
from typing import List, Tuple, Any

import elasticsearch
import elasticsearch_dsl
from elasticsearch_dsl import connections, Q
from elasticsearch_dsl.query import Match, MultiMatch, Query
import requests


client = elasticsearch.Elasticsearch()
connections.create_connection()


def get_query(q: str) -> Tuple[Query, List[str]]:
    """Turn the user entry q into a Elasticsearch query."""
    queries: List[Query] = []
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
        return Q('bool', should=queries)


def handle_specific_field_request(q: str) -> Tuple[List[Query], List[str]]:
    """Get queries when user specified field by using a colon."""
    parts: List[str] = q.split(':')
    fields: List[str] = []
    keywords_sets: List[str] = []
    for part in parts[:-1]:
        words: List[str] = part.split(' ')
        fields.append(words[-1].strip(' '))
        if len(words[:-1]) > 0:
            keywords_sets.append(' '.join(words[:-1]).strip(' '))
    keywords_sets.append(parts[-1].strip(' '))
    # Edge case when question starts with a normal search term
    if len(keywords_sets) > len(fields):
        fields = ['alles'] + fields
    queries: List[Query] = []
    keywords: List[str] = []
    for i in range(len(fields)):
        if fields[i] == 'alles':
            queries.append(get_regular_query(keywords_sets[i]))
        else:
            queries.append(get_specific_field_query(fields[i], keywords_sets[i]))
        for keyword in keywords_sets[i].split(' '):
            keywords.append(keyword)
    return queries, keywords


def get_specific_field_query(field: str, keywords: str) -> Match:
    """Return the query if user wants to search a specific field."""
    # return {'match': {field: {'query': keywords}}}
    return Match(query=keywords, field=field)


def get_regular_query(keywords: str) -> MultiMatch:
    return MultiMatch('multi_match', query=keywords,
                      fields=['naam^3', 'datum^3', 'inhoud^2', 'getuigen', 'bron'])


def post_query(query, index, start, size):
    """Post the query to the localhost Elasticsearch server."""
    s = elasticsearch_dsl.Search(index=index).query(query)
    s = s[start:start+size]
    return s.execute()


def handle_results(raw, keywords, keys):
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
                            a += (item[key][end[i - 1]:start[i]] + u'<em>'
                                  + item[key][start[i]:end[i]] + u'</em>')
                        a += item[key][end[i]:]
                        item[key] = a
        res.append(item)
    return res, hits_total


def get_page_range(hits_total, page, cards_per_page):
    page_total = hits_total // cards_per_page + 1 * (hits_total % cards_per_page != 0)
    ext = 3
    first_item = max((page - ext, 1))
    last_item = min((page + ext, page_total))
    if page < ext + 1:
        last_item = min((last_item + ext + 1 - page, page_total))
    if page_total - page < ext + 1:
        first_item = max((first_item - ext + (page_total - page), 1))
    return list(range(first_item, last_item + 1))


def get_names_list(q):
    s = elasticsearch_dsl.Search(index='namenindex')
    s.aggs.bucket(name='op_naam',
                  agg_type='terms',
                  field='naam_keyword',
                  order={'_key': 'asc'},
                  include=f'{q.title()}.*',
                  size=2000)
    res = s.execute()
    names_list = res.aggregations['op_naam'].buckets
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
