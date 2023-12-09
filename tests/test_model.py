from collectiegroesbeek.model import create_year


class TestCardNameIndex:
    @staticmethod
    def test_create_year():
        assert create_year("1513") == 1513
        assert create_year("") is None
        assert create_year("1513-04-01") == 1513
        assert create_year("1513-4-1") == 1513
        assert create_year("1316-11-21 en 1317-04-21") == 1316
