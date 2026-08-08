from tjm_project import config

def test_prompt_includes_variations():
    """Ensure the vision prompt instructs the model to handle sizes and themes."""
    assert "small, medium, or large" in config.NOTEPAD_ICON_PROMPT.lower()
    assert "light or dark" in config.NOTEPAD_ICON_PROMPT.lower()