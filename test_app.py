"""
Tests para Instagram Followers Analyzer
"""

import pytest
import json
from app import (
    InstagramUser,
    parse_followers,
    parse_following,
    parse_followers_with_timestamps,
    parse_following_with_timestamps,
    analyze,
    generate_excel
)


# =============================================================================
# FIXTURES
# =============================================================================

@pytest.fixture
def valid_followers_json():
    """JSON válido de followers en formato Instagram"""
    data = [
        {
            "title": "",
            "media_list_data": [],
            "string_list_data": [
                {"href": "https://www.instagram.com/user1", "value": "user1", "timestamp": 123}
            ]
        },
        {
            "title": "",
            "media_list_data": [],
            "string_list_data": [
                {"href": "https://www.instagram.com/user2", "value": "user2", "timestamp": 124}
            ]
        },
        {
            "title": "",
            "media_list_data": [],
            "string_list_data": [
                {"href": "https://www.instagram.com/user3", "value": "user3", "timestamp": 125}
            ]
        }
    ]
    return json.dumps(data).encode('utf-8')


@pytest.fixture
def valid_following_json():
    """JSON válido de following en formato Instagram"""
    data = {
        "relationships_following": [
            {
                "title": "user2",
                "string_list_data": [
                    {"href": "https://www.instagram.com/_u/user2", "timestamp": 123}
                ]
            },
            {
                "title": "user4",
                "string_list_data": [
                    {"href": "https://www.instagram.com/_u/user4", "timestamp": 124}
                ]
            }
        ]
    }
    return json.dumps(data).encode('utf-8')


@pytest.fixture
def empty_followers_json():
    """JSON vacío de followers"""
    return b"[]"


@pytest.fixture
def empty_following_json():
    """JSON vacío de following"""
    return json.dumps({"relationships_following": []}).encode('utf-8')


@pytest.fixture
def malformed_json():
    """JSON malformado"""
    return b"not valid json at all"


@pytest.fixture
def sample_followers():
    """Set de usuarios seguidores"""
    return {
        InstagramUser("user1"),
        InstagramUser("user2"),
        InstagramUser("user3")
    }


@pytest.fixture
def sample_following():
    """Set de usuarios seguidos"""
    return {
        InstagramUser("user2"),
        InstagramUser("user4")
    }


# =============================================================================
# TESTS: InstagramUser
# =============================================================================

class TestInstagramUser:
    """Tests para la entidad InstagramUser"""

    def test_profile_url_generation(self):
        """Verifica que se genera correctamente la URL del perfil"""
        user = InstagramUser("testuser")
        assert user.profile_url == "https://www.instagram.com/testuser"

    def test_avatar_url_generation(self):
        """Verifica que se genera URL de avatar"""
        user = InstagramUser("testuser")
        assert "dicebear.com" in user.avatar_url
        assert "testuser" in user.avatar_url

    def test_equality_case_insensitive(self):
        """Verifica que la comparación es case-insensitive"""
        user1 = InstagramUser("TestUser")
        user2 = InstagramUser("testuser")
        user3 = InstagramUser("TESTUSER")

        assert user1 == user2
        assert user2 == user3
        assert user1 == user3

    def test_hash_consistency(self):
        """Verifica que usuarios iguales tienen el mismo hash"""
        user1 = InstagramUser("TestUser")
        user2 = InstagramUser("testuser")

        assert hash(user1) == hash(user2)

    def test_set_deduplication(self):
        """Verifica que usuarios duplicados se eliminan en sets"""
        users = {
            InstagramUser("user1"),
            InstagramUser("USER1"),
            InstagramUser("User1")
        }
        assert len(users) == 1

    def test_different_users_are_not_equal(self):
        """Verifica que usuarios diferentes no son iguales"""
        user1 = InstagramUser("user1")
        user2 = InstagramUser("user2")

        assert user1 != user2
        assert hash(user1) != hash(user2)


# =============================================================================
# TESTS: Parser de Followers
# =============================================================================

class TestParseFollowers:
    """Tests para parse_followers"""

    def test_parse_valid_followers(self, valid_followers_json):
        """Parsea correctamente JSON válido de followers"""
        users = parse_followers([valid_followers_json])

        assert len(users) == 3
        assert InstagramUser("user1") in users
        assert InstagramUser("user2") in users
        assert InstagramUser("user3") in users

    def test_parse_multiple_files(self, valid_followers_json):
        """Parsea múltiples archivos y deduplica"""
        users = parse_followers([valid_followers_json, valid_followers_json])

        # Deben estar deduplicados
        assert len(users) == 3

    def test_parse_empty_returns_empty_set(self, empty_followers_json):
        """Retorna set vacío para JSON vacío"""
        users = parse_followers([empty_followers_json])
        assert len(users) == 0

    def test_parse_malformed_returns_empty_set(self, malformed_json):
        """Retorna set vacío para JSON malformado (no lanza excepción)"""
        users = parse_followers([malformed_json])
        assert len(users) == 0

    def test_parse_empty_list_returns_empty_set(self):
        """Retorna set vacío para lista vacía de archivos"""
        users = parse_followers([])
        assert len(users) == 0


# =============================================================================
# TESTS: Parser de Following
# =============================================================================

class TestParseFollowing:
    """Tests para parse_following"""

    def test_parse_valid_following(self, valid_following_json):
        """Parsea correctamente JSON válido de following"""
        users = parse_following(valid_following_json)

        assert len(users) == 2
        assert InstagramUser("user2") in users
        assert InstagramUser("user4") in users

    def test_parse_empty_returns_empty_set(self, empty_following_json):
        """Retorna set vacío para JSON vacío"""
        users = parse_following(empty_following_json)
        assert len(users) == 0

    def test_parse_malformed_returns_empty_set(self, malformed_json):
        """Retorna set vacío para JSON malformado"""
        users = parse_following(malformed_json)
        assert len(users) == 0


# =============================================================================
# TESTS: Analyze
# =============================================================================

class TestAnalyze:
    """Tests para la función analyze"""

    def test_not_following_back(self, sample_followers, sample_following):
        """Identifica correctamente quién no te sigue de vuelta"""
        results = analyze(sample_followers, sample_following)

        # user4 está en following pero no en followers
        assert InstagramUser("user4") in results["not_following_back"]
        assert len(results["not_following_back"]) == 1

    def test_not_followed_by_me(self, sample_followers, sample_following):
        """Identifica correctamente a quién no sigues"""
        results = analyze(sample_followers, sample_following)

        # user1 y user3 están en followers pero no en following
        assert InstagramUser("user1") in results["not_followed_by_me"]
        assert InstagramUser("user3") in results["not_followed_by_me"]
        assert len(results["not_followed_by_me"]) == 2

    def test_mutual_followers(self, sample_followers, sample_following):
        """Identifica correctamente los seguidores mutuos"""
        results = analyze(sample_followers, sample_following)

        # user2 está en ambos
        assert InstagramUser("user2") in results["mutual"]
        assert len(results["mutual"]) == 1

    def test_totals_are_correct(self, sample_followers, sample_following):
        """Verifica que los totales son correctos"""
        results = analyze(sample_followers, sample_following)

        assert results["total_followers"] == 3
        assert results["total_following"] == 2

    def test_empty_sets(self):
        """Maneja correctamente sets vacíos"""
        results = analyze(set(), set())

        assert len(results["not_following_back"]) == 0
        assert len(results["not_followed_by_me"]) == 0
        assert len(results["mutual"]) == 0
        assert results["total_followers"] == 0
        assert results["total_following"] == 0

    def test_all_mutual(self):
        """Cuando todos son mutuos"""
        followers = {InstagramUser("a"), InstagramUser("b")}
        following = {InstagramUser("a"), InstagramUser("b")}

        results = analyze(followers, following)

        assert len(results["mutual"]) == 2
        assert len(results["not_following_back"]) == 0
        assert len(results["not_followed_by_me"]) == 0

    def test_no_mutual(self):
        """Cuando no hay mutuos"""
        followers = {InstagramUser("a"), InstagramUser("b")}
        following = {InstagramUser("c"), InstagramUser("d")}

        results = analyze(followers, following)

        assert len(results["mutual"]) == 0
        assert len(results["not_following_back"]) == 2
        assert len(results["not_followed_by_me"]) == 2


# =============================================================================
# TESTS: Excel Export
# =============================================================================

class TestGenerateExcel:
    """Tests para generate_excel"""

    def test_returns_bytes(self, sample_followers, sample_following):
        """Verifica que retorna bytes"""
        results = analyze(sample_followers, sample_following)
        excel_data = generate_excel(results)

        assert isinstance(excel_data, bytes)
        assert len(excel_data) > 0

    def test_excel_with_empty_results(self):
        """Genera Excel correctamente con resultados vacíos"""
        results = {
            "not_following_back": set(),
            "not_followed_by_me": set(),
            "mutual": set(),
            "total_followers": 0,
            "total_following": 0
        }

        excel_data = generate_excel(results)

        assert isinstance(excel_data, bytes)
        assert len(excel_data) > 0

    def test_excel_with_single_user(self):
        """Genera Excel con un solo usuario"""
        results = {
            "not_following_back": {InstagramUser("ghost_user")},
            "not_followed_by_me": set(),
            "mutual": set(),
            "total_followers": 0,
            "total_following": 1
        }

        excel_data = generate_excel(results)

        assert isinstance(excel_data, bytes)
        assert len(excel_data) > 0


# =============================================================================
# TESTS DE INTEGRACIÓN
# =============================================================================

class TestIntegration:
    """Tests de integración del flujo completo"""

    def test_full_flow(self, valid_followers_json, valid_following_json):
        """Test del flujo completo: parse -> analyze -> export"""
        # Parse
        followers = parse_followers([valid_followers_json])
        following = parse_following(valid_following_json)

        assert len(followers) == 3
        assert len(following) == 2

        # Analyze
        results = analyze(followers, following)

        assert results["total_followers"] == 3
        assert results["total_following"] == 2
        assert len(results["mutual"]) == 1  # user2
        assert len(results["not_following_back"]) == 1  # user4
        assert len(results["not_followed_by_me"]) == 2  # user1, user3

        # Export
        excel_data = generate_excel(results)

        assert isinstance(excel_data, bytes)
        assert len(excel_data) > 0

    def test_real_instagram_format(self):
        """Test con formato exacto de Instagram"""
        # Formato real de followers
        followers_data = [
            {
                "title": "",
                "media_list_data": [],
                "string_list_data": [
                    {
                        "href": "https://www.instagram.com/__belpon.ce",
                        "value": "__belpon.ce",
                        "timestamp": 1765415787
                    }
                ]
            }
        ]

        # Formato real de following
        following_data = {
            "relationships_following": [
                {
                    "title": "nadiedicenada",
                    "string_list_data": [
                        {
                            "href": "https://www.instagram.com/_u/nadiedicenada",
                            "timestamp": 1766201170
                        }
                    ]
                }
            ]
        }

        followers = parse_followers([json.dumps(followers_data).encode()])
        following = parse_following(json.dumps(following_data).encode())

        assert len(followers) == 1
        assert InstagramUser("__belpon.ce") in followers

        assert len(following) == 1
        assert InstagramUser("nadiedicenada") in following


# =============================================================================
# TESTS: Timestamp Parsing
# =============================================================================

class TestParseFollowersWithTimestamps:
    """Tests para parse_followers_with_timestamps"""

    def test_extracts_timestamps(self):
        """Verifica que extrae correctamente los timestamps"""
        data = [
            {
                "title": "",
                "media_list_data": [],
                "string_list_data": [
                    {"href": "https://www.instagram.com/user1", "value": "user1", "timestamp": 1000}
                ]
            },
            {
                "title": "",
                "media_list_data": [],
                "string_list_data": [
                    {"href": "https://www.instagram.com/user2", "value": "user2", "timestamp": 2000}
                ]
            }
        ]
        content = json.dumps(data).encode('utf-8')

        users, timestamps = parse_followers_with_timestamps([content])

        assert len(users) == 2
        assert InstagramUser("user1") in users
        assert InstagramUser("user2") in users
        assert timestamps["user1"] == 1000
        assert timestamps["user2"] == 2000

    def test_handles_missing_timestamps(self):
        """Maneja usuarios sin timestamp"""
        data = [
            {
                "title": "",
                "media_list_data": [],
                "string_list_data": [
                    {"href": "https://www.instagram.com/user1", "value": "user1"}
                ]
            }
        ]
        content = json.dumps(data).encode('utf-8')

        users, timestamps = parse_followers_with_timestamps([content])

        assert len(users) == 1
        assert "user1" not in timestamps  # No timestamp provided

    def test_empty_returns_empty(self):
        """Retorna vacíos para entrada vacía"""
        users, timestamps = parse_followers_with_timestamps([b"[]"])

        assert len(users) == 0
        assert len(timestamps) == 0


class TestParseFollowingWithTimestamps:
    """Tests para parse_following_with_timestamps"""

    def test_extracts_timestamps(self):
        """Verifica que extrae correctamente los timestamps"""
        data = {
            "relationships_following": [
                {
                    "title": "user1",
                    "string_list_data": [
                        {"href": "https://www.instagram.com/_u/user1", "timestamp": 3000}
                    ]
                },
                {
                    "title": "user2",
                    "string_list_data": [
                        {"href": "https://www.instagram.com/_u/user2", "timestamp": 4000}
                    ]
                }
            ]
        }
        content = json.dumps(data).encode('utf-8')

        users, timestamps = parse_following_with_timestamps(content)

        assert len(users) == 2
        assert InstagramUser("user1") in users
        assert InstagramUser("user2") in users
        assert timestamps["user1"] == 3000
        assert timestamps["user2"] == 4000

    def test_handles_missing_timestamps(self):
        """Maneja usuarios sin timestamp"""
        data = {
            "relationships_following": [
                {
                    "title": "user1",
                    "string_list_data": [
                        {"href": "https://www.instagram.com/_u/user1"}
                    ]
                }
            ]
        }
        content = json.dumps(data).encode('utf-8')

        users, timestamps = parse_following_with_timestamps(content)

        assert len(users) == 1
        assert "user1" not in timestamps  # No timestamp provided

    def test_empty_returns_empty(self):
        """Retorna vacíos para entrada vacía"""
        data = {"relationships_following": []}
        content = json.dumps(data).encode('utf-8')

        users, timestamps = parse_following_with_timestamps(content)

        assert len(users) == 0
        assert len(timestamps) == 0
