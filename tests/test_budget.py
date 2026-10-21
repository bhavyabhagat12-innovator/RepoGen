from repogen.generator import split_budget


def test_budget_adds_up_to_total():
    b = split_budget(200, 300)
    assert 190 <= sum(lo for lo, _ in b.values()) <= 210
    assert 290 <= sum(hi for _, hi in b.values()) <= 310


def test_each_range_is_valid():
    for lo, hi in split_budget(100, 200).values():
        assert hi > lo > 0