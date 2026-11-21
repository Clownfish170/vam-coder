"""Line formatter"""


def emit(data):
    return "~".join(str(x) for x in data)
