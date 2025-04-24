import pytest
from elasticsearch_dsl.query import Q
from collectiegroesbeek.controller import Searcher
from model import list_doctypes


@pytest.mark.parametrize(
    "query, expected_queries, expected_keywords, expected_q_stripped",
    [
        # Single field with single value
        ("naam:value", [Q("match", naam={"query": "value", "operator": "and"})], ["value"], ""),
        # Single field with multi-word value
        (
            'naam:"multi word value"',
            [Q("match", naam={"query": "multi word value", "operator": "and"})],
            ["multi", "word", "value"],
            "",
        ),
        # Multiple fields with single and multi-word values
        (
            'naam:single datum:"multi word value"',
            [
                Q("match", naam={"query": "single", "operator": "and"}),
                Q("match", datum={"query": "multi word value", "operator": "and"}),
            ],
            ["single", "multi", "word", "value"],
            "",
        ),
        # Mixed query with normal search terms
        (
            "normal search naam:value another",
            [Q("match", naam={"query": "value", "operator": "and"})],
            ["value"],
            "normal search another",
        ),
        # No field specified
        ("normal search", [], [], "normal search"),
        # Case where colon appears as part of a value for a field
        (
            'naam:"value:with:colons"',
            [Q("match", naam={"query": "value:with:colons", "operator": "and"})],
            ["value:with:colons"],
            "",
        ),
        # Case where colon appears as part of a value without field
        ("value:with:colons", [], [], "value:with:colons"),
    ],
)
def test_handle_specific_field_request(
    query, expected_queries, expected_keywords, expected_q_stripped
):
    searcher = Searcher(q=query, start=0, size=10, doctypes=list_doctypes())
    queries, keywords, q_stripped = searcher.handle_specific_field_request(query)

    assert queries == expected_queries
    assert sorted(keywords) == sorted(expected_keywords)
    assert q_stripped == expected_q_stripped
