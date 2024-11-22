import pytest

from ingest.locations import extract_location


@pytest.mark.parametrize(
    "text, expected",
    [
        (
            "Pouwels Florysz aan Henric Claesz een huis en erf in de Corte Bagynestraat, an d'een zyde: Heertgen de backer, an d'ander zyde: Symon van Zaenden, afterwaerts streckende an Heertgen voors.",
            ["Corte Bagynestraat"],
        ),
        (
            "Claes van der Laen erkent dat Claes Garbrantsz hem heeft afgelost 10 st 6 d gr. sjaars die hij gecoft heeft van Frans Dircsz en dezelve Frans hadde op ten huis en erf in Willem Bruijnenstege, an d'een zide: Claes voors, an d'ander zide: Math[ys ?] Aerntsz met Claes voors. After streckende an Claes voorn.",
            ["Willem Bruijnenstege"],
        ),
        (
            "Guerte c me [coman ?] met Dirc de Weever [?] als haar gecoren voogd verkoopt aan Adriaen Willem Jansz weduwe, ½ van huis en erf op t Grote Heyligland, an d'een zide: Pieter uijten Hage, an d'ander zide: de Bernaditen buiten Haerlem, after streckende an Pieter voorn.",
            ["Grote Heyligland"],
        ),
        (
            "Frans Dircsz vercoopt Geryt Jan Huijssersz een huis en erf in de Zijlstraat, an d'een zyde: Jan Pietersz, an d'ander zyde: Cille Caygen (Caggen ?), afterwaerts streckende an die Beeck",
            ["Zijlstraat"],
        ),
        (
            "Guerte Nannen weduwe met Willem Nannincxz als voogd verkoopt aan Vrerick Gerytsz een huis en erf buiten Scalcwyckerpoort, an d'een zyde: Martyn Jansz, Garbrant Dircxz en Lambert Volkertsz [doorgehaald: der stede vest an die ander zyde], streckende voor van de zomerwech after an der stede Vest",
            ["Scalcwyckerpoort"],
        ),
        (
            "Outger Claesz, snijder, aan Mathijs Jacobsz een huis en erf in de Grote Houtstraet, an d'een zide: Claes lapper, an d'ander zide: Geryt van der Hoel, afterwaerts streckende in die Geerstraet",
            ["Grote Houtstraet", "Geerstraet"],
        ),
        (
            "Margriet Pieter Baertsz weduwe, met Claes Kibbe als gecoren voogd, verkoopt aan Claes Bouwensz twee huysen en erven mitter broutou, ende hiertoe nog een cleyn huijstgen ofte varckenschot in Hontcoepstege, also groot en cleyn als dat al tesamen gestaen en gelegen is an de Burchwalsgraft op de hoeck van de Hagestraat, an d'een zide: die Hagestraet voors, an d'ander zide: Baernt Jansz, glasemaker, after streckende an Willem Arijsz. En van t huijsgen of varckenschot in Hontscoepstege zijn lendens an d'een zide: Jan Claesz.., an d'ander zide: Jan Wolbrantsz, afterwaerts streckende an Jan Wolbrantsz voirs",
            ["Hontcoepstege", "Burchwalsgraft", "Hagestraat", "Hagestraet", "Hontscoepstege"],
        ),
        (
            "Aechte Martijn Willemsz weduwe met Jan Pietersz hant, haers broeders en voogd, verkoopt aan Claes Garbrantsz en Thonijs Heertgensz tesamen een huis en erf op te Scepmakersdyck",
            ["Scepmakersdyck"],
        ),
        (
            "Aechte Nannincxdochter, bagyn op ten Groten Hof, met Gheryt Vredericsz Casteleijn als haar gecoren voogd, lijt dat zij Aechte Gerytsdochter, haars zustersdochter, gegeven heeft voor haar moeders erve ende zy noch van haer moeder onder hadde, ½ van een huis en erf in Egmondtsstege [zijsteeg van de St Jansstraet]. Afterwerts streckende an Dirck van Bekesteyn, an d'een zide: mr Steven cyrurgyn, an d'ander: Maritgen Jansdochter",
            ["Egmondtsstege", "zijsteeg", "St Jansstraet"],
        ),
    ],
)
def test_extract_location(text, expected):
    assert extract_location(text) == expected
