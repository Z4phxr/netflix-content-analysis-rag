from app.services.retrieval import determine_top_k


def test_list_10_movies():
    assert determine_top_k("List 10 movies") == 20


def test_compare_a_and_b():
    assert determine_top_k("Compare A and B") == 10


def test_who_directed_x():
    assert determine_top_k("Who directed X?") == 10


def test_list_all():
    assert determine_top_k("List all movies") == 50
