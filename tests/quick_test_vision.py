from tjm_project import vision

# crop_path = a real screenshot/quadrant PNG containing e.g. the Recycle Bin
result = vision.locate_icon_in_crop("path/to/some_crop.png", "the Recycle Bin icon")
print(result)  # should return (x, y) if found, None if not