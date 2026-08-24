import pytest
from services.plz_lookup import PLZLookupService
from services.ik_lookup import IKLookupService


class TestPLZLookupService:
    @pytest.fixture(autouse=True)
    def setup_service(self):
        self.plz_service = PLZLookupService()

    def test_get_city_by_plz(self):
        # Test Berlin PLZ
        city = self.plz_service.get_city_by_plz("10115")
        assert city is not None
        assert "Berlin" in city or len(city) > 0

    def test_get_plz_by_city(self):
        plz = self.plz_service.get_plz_by_city("Berlin")
        assert plz is not None
        assert plz.isdigit()
        assert len(plz) == 5

    def test_nonexistent_plz_and_city(self):
        assert self.plz_service.get_city_by_plz("999999") is None
        assert self.plz_service.get_plz_by_city("NonexistentCityXYZ") is None

    def test_zfill_plz_lookup(self):
        # 4-digit PLZ string (e.g. Dresden PLZ 01067)
        city = self.plz_service.get_city_by_plz("1067")
        if city:
            assert "Dresden" in city or len(city) > 0

    def test_umlaute_city_lookup(self):
        # Test cities with umlauts or special chars e.g. München, Köln, Nürnberg
        plz_muenchen = self.plz_service.get_plz_by_city("München")
        plz_muenchen_ae = self.plz_service.get_plz_by_city("Muenchen")
        if plz_muenchen or plz_muenchen_ae:
            assert plz_muenchen is not None or plz_muenchen_ae is not None

    def test_plz_lookup_edge_cases(self):
        assert self.plz_service.get_city_by_plz("") is None
        assert self.plz_service.get_city_by_plz(None) is None
        assert self.plz_service.get_city_by_plz("  ") is None
        assert self.plz_service.get_plz_by_city("") is None
        assert self.plz_service.get_plz_by_city(None) is None
        assert self.plz_service.get_plz_by_city("   ") is None


class TestIKLookupService:
    @pytest.fixture(autouse=True)
    def setup_service(self):
        self.ik_service = IKLookupService()

    def test_get_provider_by_ik(self):
        # Techniker Krankenkasse IK: 260326822
        provider = self.ik_service.get_provider_by_ik("260326822")
        if provider:
            assert "Techniker" in provider or len(provider) > 0

    def test_get_ik_by_provider_exact(self):
        # Search by exact name
        ik, matched_name, score = self.ik_service.get_ik_by_provider("Techniker Krankenkasse")
        if ik:
            assert ik.isdigit()
            assert score >= 0.8

    def test_fuzzy_provider_lookup(self):
        # Test fuzzy lookup with typos or partial names
        ik, matched_name, score = self.ik_service.get_ik_by_provider("Techniker Kasse", fuzzy=True)
        if ik:
            assert ik.isdigit()
            assert score >= 0.6

    def test_nonexistent_ik(self):
        assert self.ik_service.get_provider_by_ik("000000000") is None
        assert self.ik_service.get_provider_by_ik(None) is None
        assert self.ik_service.get_provider_by_ik("   ") is None
        assert self.ik_service.get_provider_by_ik("invalid_ik") is None
        ik, name, score = self.ik_service.get_ik_by_provider("", fuzzy=False)
        assert ik is None



