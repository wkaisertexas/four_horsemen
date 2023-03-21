"""
Testing the multi_meme.py module
"""
import unittest.mock as mock

from four_horsemen.multi_meme import get_pos, get_post_layout

DIMS = (400, 800)

def test_get_pos():
    """
    Tests the get_pos function from multi_meme.py
    """
    res = get_pos(0, 2, 2, 1, DIMS)
    assert res == (0, 0)

    res = get_pos(1, 2, 2, 1, DIMS)
    assert res == (0, 400)

    res = get_pos(2, 3, 2, 2, DIMS)
    assert res == (100, 400)

    res = get_pos(2, 4, 2, 2, DIMS)
    assert res == (0, 400)

    res = get_pos(3, 4, 2, 2, DIMS)
    assert res == (200, 400)


def test_get_post_layout():
    """
    Tests the get_post_layout function from multi_meme.py
    """
    mocker = mock.Mock()
    mocker.get_post_layout = get_post_layout

    mocker.get_rows_columns.return_value = (2, 2)

    assert mocker.get_post_layout(DIMS, 4) == [(0, 0), (200, 0), (0, 400), (200, 400)]

    mocker.get_rows_columns.return_value = (2, 3)
    assert(mocker.get_post_layout(DIMS, 5) == [(0, 0), (133, 0), (266, 0), (66, 400), (199, 400)])
