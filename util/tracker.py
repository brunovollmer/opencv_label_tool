import cv2 as cv

class RoiTracker:

    def __init__(self):
        self._initialized = False

    def init_tracker(self, frame, roi):
        self._tracker = cv.TrackerCSRT_create()

        if roi:

            ok = self._tracker.init(frame, tuple(roi))

            self._initialized = ok

            print("tracker initialized")

            return ok
        else:
            self._initialized = False
            return False

    def track(self, frame):
        ok, roi = self._tracker.update(frame)

        if ok:
            print("found roi: {}".format(roi))
            roi = list(map(int, roi))
            return roi

        return []

    def destroy_tracker(self):
        self._tracker = None
        self._initialized = False

    @property
    def initialized(self):
        return self._initialized