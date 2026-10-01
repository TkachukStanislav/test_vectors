import math

import pytest

from app.embeddings import fake_embedding


def test_vector_has_8_numbers():
    vector = fake_embedding("hello")

    assert len(vector) == 8


def test_vector_is_normalized():
    vector = fake_embedding("hello")

    length = math.sqrt(sum(x * x for x in vector))
    assert length == pytest.approx(1.0)


def test_same_letters_same_vector():
    assert fake_embedding("hello") == pytest.approx(fake_embedding("olleh"))


def test_empty_text():
    assert fake_embedding("") == [0.0] * 8
