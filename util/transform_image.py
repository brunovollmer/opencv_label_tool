import numpy as np
import cv2 as cv

def resize_image(config, frame):
    width = config["width"]
    height = config["height"]
    dim = (width, height)

    resized_frame = cv.resize(frame, dim, interpolation = cv.INTER_AREA)

    return resized_frame
