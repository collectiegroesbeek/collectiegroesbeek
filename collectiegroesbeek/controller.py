import re
from typing import Dict, List, Tuple, Iterable, Optional, Set, Type

import elasticsearch_dsl
from elasticsearch import Elasticsearch  # type: ignore
from elasticsearch_dsl import Q, Search
from elasticsearch_dsl.query import MultiMatch, Query

from .model import CardNameDoc, BaseDocument, list_doctypes, index_name_to_doctype, list_index_names


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
        self.multimatch_fields = [
            field for doctype in doctypes for field in doctype.get_multimatch_fields()
        ]
        year_range: Optional[Tuple[int, int]] = self.parse_year_range()
        queries_must = []
        self.keywords: Set[str] = set()
        for part in self.q.split("&"):
            part = part.strip()
            if part:
                queries_must.append(self.get_query(part))
        query = Q("bool", must=queries_must)
        indices = [doctype.Index.name for doctype in doctypes]
        s: Search = Search(index=indices, doc_type=doctypes).query(query)
        s = s[self.start : self.start + self.size]
        if year_range:
            s = s.filter("range", **{"jaar": {"gte": year_range[0], "lte": year_range[1]}})
        s = s.highlight("*", number_of_fragments=0)
        self.s = s

    def get_query(self, q) -> Query:
        """Turn the user entry q into a Elasticsearch query."""
        queries: List[Query] = []
        if ":" in q:
            query_list, keywords = self.handle_specific_field_request(q)
            queries.extend(query_list)
        else:
            queries.append(self.get_regular_query(q))
            keywords = q.split()
        keywords = [word.strip('"') for word in keywords]
        self.keywords.update(keywords)
        if len(queries) == 0:
            raise RuntimeError("No query.")
        elif len(queries) == 1:
            return queries[0]
        else:
            return Q("bool", must=queries)

    def handle_specific_field_request(self, q) -> Tuple[List[Query], List[str]]:
        """Get queries when user specified field by using a colon."""
        parts: List[str] = q.split(":")
        fields: List[str] = []
        keywords_sets: List[str] = []
        for part in parts[:-1]:
            words: List[str] = part.split(" ")
            fields.append(words[-1].strip(" "))
            if len(words[:-1]) > 0:
                keywords_sets.append(" ".join(words[:-1]).strip(" "))
        keywords_sets.append(parts[-1].strip(" "))
        # Edge case when question starts with a normal search term
        if len(keywords_sets) > len(fields):
            fields = ["alles"] + fields
        queries: List[Query] = []
        keywords: List[str] = []
        for i in range(len(fields)):
            if fields[i] == "alles":
                queries.append(self.get_regular_query(keywords_sets[i]))
            else:
                queries.append(self.get_specific_field_query(fields[i], keywords_sets[i]))
            for keyword in keywords_sets[i].split(" "):
                keywords.append(keyword)
        return queries, keywords

    @staticmethod
    def get_specific_field_query(field: str, keywords: str) -> Query:
        """Return the query if user wants to search a specific field."""
        return Q("match", **{field: {"query": keywords, "operator": "and"}})

    def get_regular_query(self, keywords: str) -> Query:
        """Return the query if user wants to search in all fields."""
        try:
            return self.get_partial_phrase_match_query(keywords)
        except ValueError:
            return MultiMatch("multi_match", query=keywords, fields=self.multimatch_fields)

    def get_partial_phrase_match_query(self, keywords: str) -> Query:
        matches = re.findall(r'("[^"]*"|\d+-\d+(?:-\d+)?)', keywords)
        if not matches:
            raise ValueError("no phrases")
        queries = [
            Q("multi_match", type="phrase", query=match.strip('"'), fields=self.multimatch_fields)
            for match in matches
        ]
        leftover = keywords
        for match in matches:
            leftover = leftover.replace(match, "")
        leftover = leftover.strip()
        if leftover:
            queries.append(MultiMatch("multi_match", query=leftover, fields=self.multimatch_fields))
        return Q("bool", must=queries)

    def parse_year_range(self) -> Optional[Tuple[int, int]]:
        pattern = re.compile(r"(\d{4})-(\d{4})")
        match = pattern.search(self.q)
        if match is None:
            return None
        year_start = int(match.group(1))
        year_end = int(match.group(2))
        self.q = pattern.sub(repl="", string=self.q).strip()
        return year_start, year_end

    def sort(self, sort_by: Optional[str]):
        if not sort_by:
            return
        self.s = self.s.sort(*sort_by.split(","))

    @staticmethod
    def get_sort_options() -> Dict[str, str]:
        return {
            "jaar": "Jaartal (oplopend)",
            "-jaar": "Jaartal (aflopend)",
        }

    def count(self) -> int:
        return self.s.count()

    def get_results(self) -> List[BaseDocument]:
        res: List[BaseDocument] = list(self.s)
        for hit in res:
            if hasattr(hit.meta, "highlight"):
                for key, values in hit.meta.highlight.to_dict().items():
                    setattr(hit, key, " ".join(values))
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


def get_bronnen_list() -> List[dict]:
    s = elasticsearch_dsl.Search(index="voornamen")  # TODO: all indexes
    s.aggs.bucket(
        name="op_bron",
        agg_type="terms",
        field="bron_prefix",
        order={"_key": "asc"},
        size=10_000,
    )
    res = s.execute()
    bron_list: List[dict] = list(res.aggregations["op_bron"].buckets)
    if len(bron_list) >= 10_000:
        raise ValueError("Number of bronnen exceeded max size")
    # items of the form: {'key': 'Aa', 'doc_count': 117}
    return bron_list


def get_suggestions(keywords: Iterable[str]):
    tokens = [token for token in keywords if not token.isdigit()]
    s = CardNameDoc.search()
    for field in ["naam", "inhoud", "bron", "getuigen"]:
        s = s.suggest(
            name=field,
            text=" ".join(tokens),
            term={"field": field, "size": 5, "suggest_mode": "always"},
        )
    s = s.extra(size=0)
    resp = s.execute()
    suggestions: Dict[str, Set[str]] = {}
    tokens_set = set(tokens)
    for res_per_token in resp.suggest.to_dict().values():
        for token_res in res_per_token:
            token = token_res["text"]
            for option in token_res["options"]:
                suggestion = option["text"]
                if suggestion not in tokens_set:
                    suggestions.setdefault(token, set()).add(suggestion)
    return {k: sorted(v) for k, v in suggestions.items()}


def get_doc(doc_id: int) -> BaseDocument:
    s = Search(index="*", doc_type=list_doctypes())
    s = s.filter("ids", values=[doc_id])
    return list(s)[0]


def get_number_of_total_docs() -> int:
    s = Search()
    s = s.index(*index_name_to_doctype.keys())
    n_total_docs = s.count()
    return n_total_docs


def get_indices_and_doc_counts() -> Dict[str, int]:
    es = Elasticsearch()
    indices: list[dict[str, str]] = es.cat.indices(index=list_index_names(), format="json")  # type: ignore
    index_to_alias = get_index_to_alias()
    return {index_to_alias[index["index"]]: int(index["docs.count"]) for index in indices}


def get_index_to_alias() -> Dict[str, str]:
    es = Elasticsearch()
    aliases: list[dict[str, str]] = es.cat.aliases(name=list_index_names(), format="json")  # type: ignore
    return {item["index"]: item["alias"] for item in aliases}


def format_int(num: int) -> str:
    return f"{num:,d}".replace(",", ".")
