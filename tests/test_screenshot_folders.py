from pathlib import Path
from unittest.mock import patch, MagicMock
from tjm_project import screen_utils

@patch("pyautogui.screenshot")
def test_screenshot_folder_structure(mock_screenshot, tmp_path):
    """Ensure screenshots are named correctly in the target directory."""
    # Mock the image object
    mock_img = MagicMock()
    mock_img.size = (1920, 1080)
    mock_screenshot.return_value = mock_img
    
    # Test full screen capture
    full_path = screen_utils.capture_screen(save_dir=tmp_path)
    assert full_path.name == "full.png"
    assert full_path.parent == tmp_path
    mock_img.save.assert_called_with(full_path)
    
    # Test slicing
    with patch("PIL.Image.open") as mock_open:
        mock_full_img = MagicMock()
        mock_open.return_value = mock_full_img
        
        mock_crop = MagicMock()
        mock_full_img.crop.return_value = mock_crop
        
        paths = screen_utils.slice_into_quadrants(full_path, save_dir=tmp_path)
        
        assert len(paths) == 4
        assert paths[0].name == "top_left.png"
        assert paths[3].name == "bottom_right.png"
        assert mock_crop.save.call_count == 4