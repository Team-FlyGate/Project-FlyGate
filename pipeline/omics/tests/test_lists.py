import pathlib

import pytest

from pipeline.omics import build, lists

OMICS = pathlib.Path(__file__).resolve().parents[1]


@pytest.mark.skipif(not lists.SIDER.exists(), reason="SIDER pilot reference set is not on this machine")
def test_v1_lists_are_what_their_sources_give():
    drugs, pairs = lists.lists(lists.SIDER)
    assert build.read_lines(OMICS / "drugs_v1.txt") == drugs
    assert build.read_pairs(OMICS / "pairs_v1.txt") == pairs
    assert (len(drugs), len(pairs)) == (245, 19)
    assert drugs[:2] == ["ACETAMINOPHEN", "ADAPALENE"]
    assert pairs[0] == ("NIRAPARIB", "thrombocytopenia") and pairs[-1] == ("METFORMIN", "lactic acidosis")
