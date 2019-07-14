import re
from typing import List, Tuple, Iterable, Optional

import elasticsearch_dsl
from elasticsearch_dsl import connections, Q, Search
from elasticsearch_dsl.query import Match, MultiMatch, Query

from .model import CardNameIndex

connections.create_connection('default', hosts=['localhost:9200'])


class Searcher:

    def __init__(self, q, index, start, size):
        self.keys: Iterable[str] = ['naam', 'datum', 'inhoud', 'getuigen', 'bron', 'bijzonderheden']
        self.q: str = q
        self.index: str = index
        self.start: int = start
        self.size: int = size
        year_range: Optional[Tuple[int, int]] = self.parse_year_range()
        query, keywords = self.get_query()
        self.keywords: Iterable[str] = keywords
        self.s = self.get_search(query, year_range)

    def get_query(self) -> Tuple[Query, List[str]]:
        """Turn the user entry q into a Elasticsearch query."""
        queries: List[Query] = []
        if ':' in self.q:
            query_list, keywords = self.handle_specific_field_request()
            queries.extend(query_list)
        else:
            queries.append(self.get_regular_query(self.q))
            keywords = self.q.split(' ')
        if len(queries) == 0:
            raise RuntimeError('No query.')
        elif len(queries) == 1:
            return queries[0], keywords
        else:
            return Q('bool', should=queries), keywords

    def handle_specific_field_request(self) -> Tuple[List[Query], List[str]]:
        """Get queries when user specified field by using a colon."""
        parts: List[str] = self.q.split(':')
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
                queries.append(self.get_regular_query(keywords_sets[i]))
            else:
                queries.append(self.get_specific_field_query(fields[i], keywords_sets[i]))
            for keyword in keywords_sets[i].split(' '):
                keywords.append(keyword)
        return queries, keywords

    @staticmethod
    def get_specific_field_query(field: str, keywords: str) -> Match:
        """Return the query if user wants to search a specific field."""
        return Match(query=keywords, field=field)

    @staticmethod
    def get_regular_query(keywords: str) -> MultiMatch:
        """Return the query if user wants to search in all fields."""
        return MultiMatch('multi_match', query=keywords,
                          fields=['naam^3', 'datum^3', 'inhoud^2', 'getuigen', 'bron'])

    def parse_year_range(self) -> Optional[Tuple[int, int]]:
        pattern = re.compile(r'(\d{4})-(\d{4})')
        match = pattern.search(self.q)
        if match is None:
            return None
        year_start = int(match.group(1))
        year_end = int(match.group(2))
        self.q = pattern.sub(repl='', string=self.q).strip()
        return year_start, year_end

    def get_search(self, query, filter_year) -> Search:
        """Get the final Search object with all queries.."""
        s: Search = CardNameIndex.search().query(query)
        s = s[self.start: self.start + self.size]
        if filter_year:
            s = s.filter('range', **{'jaar': {'gte': filter_year[0], 'lte': filter_year[1]}})
        s = s.highlight('*', number_of_fragments=0)
        return s

    def count(self) -> int:
        return self.s.count().value

    def get_results(self) -> List[CardNameIndex]:
        res: List[CardNameIndex] = list(self.s)
        for hit in res:
            for key, values in hit.meta.highlight.to_dict().items():
                setattr(hit, key, u' '.join(values))
        return res


def get_page_range(hits_total: int, page: int, cards_per_page: int) -> List[int]:
    page_total = hits_total // cards_per_page + 1 * (hits_total % cards_per_page != 0)
    ext = 3
    first_item = max((page - ext, 1))
    last_item = min((page + ext, page_total))
    if page < ext + 1:
        last_item = min((last_item + ext + 1 - page, page_total))
    if page_total - page < ext + 1:
        first_item = max((first_item - ext + (page_total - page), 1))
    return list(range(first_item, last_item + 1))


def get_names_list(q: str) -> List[dict]:
    s = elasticsearch_dsl.Search(index='namenindex')
    s.aggs.bucket(name='op_naam',
                  agg_type='terms',
                  field='naam_keyword',
                  order={'_key': 'asc'},
                  include=f'{q.title()}.*',
                  size=2000)
    res = s.execute()
    names_list: List[dict] = res.aggregations['op_naam'].buckets
    # items of the form: {'key': 'Aa', 'doc_count': 117}
    return names_list


def is_elasticsearch_reachable() -> bool:
    """Return a boolean whether the Elasticsearch service is available on localhost."""
    return connections.get_connection().ping()
