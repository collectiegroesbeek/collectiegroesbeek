import pytest

from ingest.generate_bronnen import split_multibron


@pytest.mark.parametrize(
    "text, expected",
    [
        ("Batavia Illustrata bl 1192", ["Batavia Illustrata"]),
        ("Arch Nassau Domeinraad I 2 reg 1074", ["Arch Nassau Domeinraad"]),
        ("Stadsrek Leiden II p 67/68", ["Stadsrek Leiden"]),
        (
            "Ned Leeuw jg 1922 p 47; A.R.A Holl Leenkamer no 105 fol 1v",
            ["Ned Leeuw", "A.R.A Holl Leenkamer"],
        ),
        (
            "Arch Culemborg Regest 10a/Sloet no 1073 bis/v.d. Bergh II no 498/Navorscher 1916 p 470",
            ["Arch Culemborg"],
        ),
        ("E.A. Dossiers dl III dossier 3244", ["E.A. Dossiers"]),
        (
            "Mr van Overvoorde: Arch Kloosters regest 1193, 1207 (klooster Engelendaal)",
            ["Mr van Overvoorde: Arch Kloosters regest 1193, 1207 (klooster Engelendaal)"],
        ),
        ("Inv no 1081 p 72 (1 omslag)", ["Inv no 1081 p 72 (1 omslag)"]),
        ("A.R.A. Graf Rekenkamer 2158/Rek Rentmeester Land van Arkel", ["A.R.A. Graf Rekenkamer"]),
        ("A.R.A. Leenkamer 32 Copieen fol 1/EL 25 fol 1", ["A.R.A. Leenkamer"]),
        ("A.R.A. Leenkamer 117b, Copie fol 121/Reg Charolais fol 59", ["A.R.A. Leenkamer"]),
        ("A.R.A. copie Leenkamer 1 fol 3v en 4/EL 6 fol 2v", ["A.R.A. copie Leenkamer"]),
        ("Alg Ned Familieblad 1889 VI p 75 en p 52", ["Alg Ned Familieblad"]),
        ("Alg Ned Familieblad jg 1889 VI p 139/Taxandria 1914 p 39", ["Alg Ned Familieblad"]),
        ("Alg Ned Familieblad 1889, dl 6 p 139", ["Alg Ned Familieblad"]),
        ("No matching word here", ["No matching word here"]),
    ],
)
def test_split_multibron(text, expected):
    assert split_multibron(text) == expected
