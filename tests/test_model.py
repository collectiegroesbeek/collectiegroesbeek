import pytest

from collectiegroesbeek.model import create_year, split_bron


class TestCardNameIndex:
    @staticmethod
    def test_create_year():
        assert create_year("1513") == 1513
        assert create_year("") is None
        assert create_year("1513-04-01") == 1513
        assert create_year("1513-4-1") == 1513
        assert create_year("1316-11-21 en 1317-04-21") == 1316


@pytest.mark.parametrize("text, expected", [
    ("Batavia Illustrata bl 1192", ["Batavia Illustrata"]),
    ("Arch Nassau Domeinraad I 2 reg 1074", ["Arch Nassau Domeinraad I 2"]),
    ("Stadsrek Leiden II p 67/68", ["Stadsrek Leiden II"]),
    (
            "Ned Leeuw jg 1922 p 47; A.R.A Holl Leenkamer no 105 fol 1v",
            ["Ned Leeuw jg 1922", "A.R.A Holl Leenkamer no 105"]
    ),
    ("No matching word here", ["No matching word here"]),
])
def test_split_bron(text, expected):
    assert split_bron(text) == expected
