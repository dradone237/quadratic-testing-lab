"""Tests de la table de correspondance Jenny -> coefficients (S-40).

Les lettres a..e de Jenny sont des ÉTIQUETTES DE VALEURS ; elles ne
désignent pas les coefficients mathématiques a, b, c.
"""

from __future__ import annotations

import itertools
from decimal import Decimal

import pytest

from quadratic_lab.mapping import (
    DEFAULT_DOMAIN,
    JENNY_LETTERS,
    MappingError,
    decode_tokens,
    encode_values,
    mapping_rows,
    parse_token,
)

D = Decimal


def test_domain_matches_the_specification_table():
    assert [dim.name for dim in DEFAULT_DOMAIN] == ["a", "b", "c"]
    assert [dim.index for dim in DEFAULT_DOMAIN] == [1, 2, 3]
    assert DEFAULT_DOMAIN[0].values == tuple(D(v) for v in (-10, -1, 0, 1, 10))
    assert DEFAULT_DOMAIN[1].values == tuple(D(v) for v in (-10, -2, 0, 2, 10))
    assert DEFAULT_DOMAIN[2].values == tuple(D(v) for v in (-10, -1, 0, 1, 10))
    assert all(dim.labels == ("a", "b", "c", "d", "e") for dim in DEFAULT_DOMAIN)


def test_example_from_the_assignment():
    # « 1a 2c 3d » => a = -10, b = 0, c = 1
    assert decode_tokens(("1a", "2c", "3d")) == (D(-10), D(0), D(1))


def test_label_letters_are_not_coefficient_names():
    # 1c (étiquette c de la dimension 1) est la valeur 0 du coefficient a.
    assert decode_tokens(("1c", "2a", "3a")) == (D(0), D(-10), D(-10))


@pytest.mark.parametrize(
    "token,expected",
    [("1a", (1, "a")), ("3e", (3, "e")), ("12Z", (12, "Z")), ("2z", (2, "z"))],
)
def test_parse_token(token, expected):
    assert parse_token(token) == expected


@pytest.mark.parametrize("token", ["a1", "1", "a", "1ab", "0a", "-1a", "1é", "", " 1a"])
def test_parse_token_rejects(token):
    with pytest.raises(MappingError):
        parse_token(token)


@pytest.mark.parametrize(
    "tokens",
    [
        ("1a", "2b"),
        ("1a", "2b", "3c", "4d"),
        ("2a", "1b", "3c"),
        ("1a", "2f", "3c"),
        ("1a", "1b", "3c"),
    ],
)
def test_decode_rejects_inconsistent_combinations(tokens):
    with pytest.raises(MappingError):
        decode_tokens(tokens)


def test_encode_decode_round_trip_on_all_125_combinations():
    for values in itertools.product(*(dim.values for dim in DEFAULT_DOMAIN)):
        tokens = encode_values(values)
        assert decode_tokens(tokens) == values


def test_encode_rejects_value_outside_domain():
    with pytest.raises(MappingError):
        encode_values((D(3), D(0), D(0)))


def test_jenny_letter_alphabet():
    assert JENNY_LETTERS[:5] == "abcde"
    assert len(JENNY_LETTERS) == 52


def test_mapping_rows_for_documentation():
    rows = mapping_rows()
    assert len(rows) == 15
    assert rows[0] == {"etiquette": "1a", "dimension": 1, "coefficient": "a", "valeur": "-10"}
    assert {"etiquette": "2c", "dimension": 2, "coefficient": "b", "valeur": "0"} in rows
