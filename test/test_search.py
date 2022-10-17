from bioproject_keyword_search import search_in_bioproject, check_proper_entrez_response


class TestSearchInBioproject:
    def test_search_in_bioproject_returns_list(self):
        """Test that the function returns a list of strings"""
        assert isinstance(search_in_bioproject(["test"], "2021/01/01", "2021/01/01"), list)

    def test_search_in_bioproject_returns_correct_ids(self):
        """Test that the function always returns the same ID list for the same keywords"""
        assert sorted(search_in_bioproject(["Faecal Microbiota Transplantation"], "2022/01/01", "2022/08/31")) == \
               sorted(['801993', '801992', '839171', '839266', '819370', '863194'])


class TestCheckProperEntrezResponse:
    def test_check_proper_entrez_response_returns_true(self):
        """Test that the function returns True when the response is properly formatted"""
        assert check_proper_entrez_response(["1. test", "BioProject Accession: test"]) is True

    def test_check_proper_entrez_response_returns_false(self):
        """Test that the function returns False when the response doesn't have accesion and abstract"""
        assert check_proper_entrez_response(["test", "test"]) is False

    def test_check_proper_entrez_response_returns_false_2(self):
        """Test that the function returns False when the response doesn't have accesion or abstract"""
        assert check_proper_entrez_response(["1. test", "test"]) is False
        assert check_proper_entrez_response(["test", "BioProject Accession: test"]) is False

    def test_check_proper_entrez_response_handles_more_entries(self):
        """Test that the function works when the input has more entries than required"""
        assert check_proper_entrez_response(["1. test", "BioProject Accession: test", "test", "test"]) is True
        assert check_proper_entrez_response(["1. test", "test", "BioProject Accession: test", "test"]) is True
        assert check_proper_entrez_response(["test", "1. test", "test", "BioProject Accession: test"]) is True
        assert check_proper_entrez_response(["test", "test", "1. test", "BioProject Accession: test"]) is True
        assert check_proper_entrez_response(["test", "test", "BioProject Accession: test", "1. test"]) is True
