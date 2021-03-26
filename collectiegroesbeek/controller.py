import re
from typing import Dict, List, Tuple, Iterable, Optional, Set, Type

import elasticsearch_dsl
from elasticsearch_dsl import connections, Q, Search
from elasticsearch_dsl.query import MultiMatch, Query
from elasticsearch_dsl.response import Hit

from . import app
from .model import CardNameDoc, BaseDocument, list_doctypes


connections.create_connection('default', hosts=[app.config['elasticsearch_host']])


class Searcher:

    def __init__(
            self,
            q: str,
            start: int,
            size: int,
            doctypes: List[Type[BaseDocument]],
    ):
        self.q: str = q
        self.start: int = start
        self.size: int = size
        if doctypes is None:
            doctypes = list_doctypes()
        self.multimatch_fields = [field for doctype in doctypes for field in doctype.get_multimatch_fields()]
        year_range: Optional[Tuple[int, int]] = self.parse_year_range()
        queries_must = []
        self.keywords: Set[str] = set()
        for part in self.q.split('&'):
            part = part.strip()
            if part:
                queries_must.append(self.get_query(part))
        query = Q('bool', must=queries_must)
        indices = [doctype.Index.name for doctype in doctypes]
        s: Search = Search(index=indices, doc_type=doctypes).query(query)
        s = s[self.start: self.start + self.size]
        if year_range:
            s = s.filter('range', **{'jaar': {'gte': year_range[0], 'lte': year_range[1]}})
        s = s.highlight('*', number_of_fragments=0)
        self.s = s

    def get_query(self, q) -> Query:
        """Turn the user entry q into a Elasticsearch query."""
        queries: List[Query] = []
        if ':' in q:
            query_list, keywords = self.handle_specific_field_request(q)
            queries.extend(query_list)
        else:
            queries.append(self.get_regular_query(q))
            keywords = q.split()
        keywords = [word.strip('"') for word in keywords]
        self.keywords.update(keywords)
        if len(queries) == 0:
            raise RuntimeError('No query.')
        elif len(queries) == 1:
            return queries[0]
        else:
            return Q('bool', must=queries)

    def handle_specific_field_request(self, q) -> Tuple[List[Query], List[str]]:
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
                queries.append(self.get_regular_query(keywords_sets[i]))
            else:
                queries.append(self.get_specific_field_query(fields[i], keywords_sets[i]))
            for keyword in keywords_sets[i].split(' '):
                keywords.append(keyword)
        return queries, keywords

    @staticmethod
    def get_specific_field_query(field: str, keywords: str) -> Query:
        """Return the query if user wants to search a specific field."""
        return Q('match', **{field: {'query': keywords, 'operator': 'and'}})

    def get_regular_query(self, keywords: str) -> Query:
        """Return the query if user wants to search in all fields."""
        try:
            return self.get_partial_phrase_match_query(keywords)
        except ValueError:
            return MultiMatch('multi_match', query=keywords, fields=self.multimatch_fields)

    def get_partial_phrase_match_query(self, keywords: str) -> Query:
        matches = re.findall(r'("[^"]*")', keywords)
        if not matches:
            raise ValueError('Query doesnt have double double quotes.')
        queries = [
            Q('multi_match', type='phrase', query=match.strip('"'), fields=self.multimatch_fields)
            for match in matches
        ]
        leftover = keywords
        for match in matches:
            leftover = leftover.replace(match, '')
        leftover = leftover.strip()
        if leftover:
            queries.append(MultiMatch('multi_match', query=leftover, fields=self.multimatch_fields))
        return Q('bool', must=queries)

    def parse_year_range(self) -> Optional[Tuple[int, int]]:
        pattern = re.compile(r'(\d{4})-(\d{4})')
        match = pattern.search(self.q)
        if match is None:
            return None
        year_start = int(match.group(1))
        year_end = int(match.group(2))
        self.q = pattern.sub(repl='', string=self.q).strip()
        return year_start, year_end

    def count(self) -> int:
        return self.s.count()

    def get_results(self) -> List[BaseDocument]:
        res: List[BaseDocument] = list(self.s)
        for hit in res:
            if hasattr(hit.meta, 'highlight'):
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
    s = elasticsearch_dsl.Search(index=CardNameDoc.Index.name)
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


def get_suggestions(keywords: Iterable[str]):
    tokens = [token for token in keywords if not token.isdigit()]
    s = CardNameDoc.search()
    for field in ['naam', 'inhoud', 'bron', 'getuigen']:
        s = s.suggest(name=field, text=' '.join(tokens),
                      term={'field': field, 'size': 5, 'suggest_mode': 'always'})
    s = s.extra(size=0)
    resp = s.execute()
    suggestions: Dict[str, Set[str]] = {}
    tokens_set = set(tokens)
    for res_per_token in resp.suggest.to_dict().values():
        for token_res in res_per_token:
            token = token_res['text']
            for option in token_res['options']:
                suggestion = option['text']
                if suggestion not in tokens_set:
                    suggestions.setdefault(token, set()).add(suggestion)
    return {k: sorted(v) for k, v in suggestions.items()}
