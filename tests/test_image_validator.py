from src.image_validator import interpret_labels


def test_valid_fish_is_accepted_with_structured_output():
    result = interpret_labels([("tench", 0.72), ("lake_shore", 0.08)])
    assert result.is_valid is True
    assert result.is_fish is True
    assert result.status == "accepted"
    assert result.detected_label == "tench"


def test_clear_non_fish_is_rejected():
    result = interpret_labels([("sports_car", 0.84), ("car_wheel", 0.08)])
    assert result.is_valid is False
    assert result.is_fish is False
    assert result.status == "rejected"


def test_uncertain_result_does_not_reach_prediction():
    result = interpret_labels([("coral_reef", 0.18), ("tench", 0.06)])
    assert result.is_valid is False
    assert result.status == "uncertain"


def test_multiple_fish_scores_can_establish_presence():
    result = interpret_labels(
        [("tench", 0.08), ("coral_reef", 0.07), ("sturgeon", 0.05)]
    )
    assert result.is_valid is True
    assert result.confidence == 0.13


def test_incidental_fish_probability_cannot_override_top_non_fish_label():
    result = interpret_labels(
        [("sports_car", 0.61), ("tench", 0.09), ("sturgeon", 0.07)]
    )
    assert result.is_valid is False
    assert result.is_fish is False
    assert result.status == "rejected"


def test_dominant_but_uncertain_non_fish_label_cannot_pass():
    result = interpret_labels(
        [("coral_reef", 0.25), ("tench", 0.12), ("sturgeon", 0.06)]
    )
    assert result.is_valid is False
    assert result.status == "uncertain"
