from app.rag.search import lexical_query, normalise_query, reciprocal_rank_fusion


def test_alarm_code_is_reduced_to_its_description():
    assert normalise_query("AL017_LOW_AIR_PRESSURE") == "LOW AIR PRESSURE"
    assert normalise_query("what does AL086_LINE_EMERGENCY_PRESSED mean?") == "what does LINE EMERGENCY PRESSED mean?"


def test_lexical_query_is_or_joined_and_deduplicated():
    assert lexical_query("low air, air pressure!") == "low | air | pressure"
    assert lexical_query("?!") == ""


def test_rrf_prefers_items_ranked_well_in_both_lists():
    fused = reciprocal_rank_fusion([[1, 2, 3], [2, 3, 9]])
    assert fused[0] == 2 and set(fused) == {1, 2, 3, 9}


def test_rrf_handles_an_empty_list():
    assert reciprocal_rank_fusion([[5, 6], []]) == [5, 6]
