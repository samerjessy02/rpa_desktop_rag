from tjm_project import screen_utils, config

def test_guardrails_reject_out_of_bounds_local():
    """Local coordinates exceeding quadrant width/height should be rejected."""
    assert screen_utils.local_to_global(0, config.QUAD_WIDTH + 10, 50) is None
    assert screen_utils.local_to_global(0, 50, config.QUAD_HEIGHT + 10) is None

def test_guardrails_reject_out_of_bounds_global():
    """Resulting global coordinates exceeding screen width/height should be rejected."""
    # Bottom right quadrant (index 3) offset + a large local value
    assert screen_utils.local_to_global(3, config.QUAD_WIDTH, config.QUAD_HEIGHT + 1) is None

def test_guardrails_accept_valid_coords():
    """Valid coordinates should map correctly."""
    assert screen_utils.local_to_global(0, 100, 100) == (100, 100)
    assert screen_utils.local_to_global(3, 10, 10) == (config.QUAD_WIDTH + 10, config.QUAD_HEIGHT + 10)