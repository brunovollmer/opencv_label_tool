"""
RoiCreator Module
"""
import cv2 as cv
import numpy as np

class Rect:
    """
    Rect class.
    """

    def __init__(self):
        """
        Rect class constructor
        """

        self.x = None
        self.y = None
        self.w = None
        self.h = None

    def __str__(self):
        """
        Create a string respresentation of a Rect object.

        Returns:
            string -- string representation.
        """

        return "{}, {}, {}, {}".format(self.x, self.y, self.w, self.h)

    def to_array(self):
        """
        Return array representation of instance.

        Returns:
            list -- list/array representation of coordinates
        """

        return [self.x, self.y, self.w, self.h]

class DragRect:
    def __init__(self, id, color=(255, 255, 0)):
        self.id = id

        # outer boundaries of canvas
        self.canvas_boundaries = Rect()

        # current rectangle
        self.current_rect = Rect()

        # the distance in the x and y direction from the anchor point to the top-left and the bottom-right corner
        self.anchor = Rect()

        # Selection marker size
        self.marker_size = 4

        self.image = None

        self.used = False

        self.color = color

        # FLAGS

        # Rectangle already present
        self.active = False

        # Drag for rectangle resize in progress
        self.drag = False

        # Marker flags by positions
        self.TL = False
        self.TM = False
        self.TR = False
        self.LM = False
        self.RM = False
        self.BL = False
        self.BM = False
        self.BR = False
        self.hold = False


class RoiCreator:
    def __init__(self, width, height, window_name):
        self._width = width
        self._height = height
        self._window_name = window_name

        self._rois = []

        self._current_roi = DragRect(len(self._rois))
        self._init_roi()
        self._rois.append(self._current_roi)

        self._results_loaded = False

    def set_mouse_callback(self, frame):
        cv.setMouseCallback(self._window_name, self._drag_roi, frame)
        if  self._results_loaded:
               self._draw(self._current_roi)
        else:
            cv.imshow(self._window_name, frame)

    def remove_mouse_callback(self):
        cv.setMouseCallback(self._window_name, lambda *args : None)

    def get_current_roi(self):
        return self._current_roi.current_rect.to_array()

    def remove_current_roi(self):
        if self._rois:
            self._rois.pop()

            if self._rois:
                self._current_roi = self._rois[-1]
            else:
                self._current_roi = DragRect(len(self._rois))
                self._init_roi()
                self._rois.append(self._current_roi)

    def load_rois(self, rois, frame):
        # delete initial rois
        self._rois = []
        self._current_roi = None

        for r in rois:
            self._current_roi = DragRect(len(self._rois))
            self._current_roi.used = True
            self._init_roi()

            self._current_roi.current_rect.x = r[0]
            self._current_roi.current_rect.y = r[1]
            self._current_roi.current_rect.w = r[2]
            self._current_roi.current_rect.h = r[3]

            self._current_roi.image = frame

            self._rois.append(self._current_roi)

        self._current_roi.active = True

        self._results_loaded = True

    def add_roi(self, roi, frame, color=(255, 255, 0)):
        self._current_roi = DragRect(len(self._rois))
        self._current_roi.used = True
        self._init_roi()

        self._current_roi.current_rect.x = roi[0]
        self._current_roi.current_rect.y = roi[1]
        self._current_roi.current_rect.w = roi[2]
        self._current_roi.current_rect.h = roi[3]

        self._current_roi.color = (255, 255, 0)

        self._current_roi.image = frame

        self._rois.append(self._current_roi)

        self._current_roi.active = True

    def get_rois(self):
        roi_coords = [r.current_rect.to_array() for r in self._rois if r.used]

        self._rois = []
        self._current_roi = None

        return roi_coords

    def draw_rois(self, frame):
        tmp_frame = frame.copy()

        for r in self._rois:

            color = (255, 255, 0)
            cv.rectangle(tmp_frame, (r.current_rect.x, r.current_rect.y), (r.current_rect.x + r.current_rect.w,r.current_rect.y + r.current_rect.h), color, 2)

        return tmp_frame


    def _init_roi(self):
        # Limit the selection box to the canvas
        self._current_roi.canvas_boundaries.x = 0
        self._current_roi.canvas_boundaries.y = 0
        self._current_roi.canvas_boundaries.w = self._width
        self._current_roi.canvas_boundaries.h = self._height

        # Set rect to zero width and height
        self._current_roi.current_rect.x = 0
        self._current_roi.current_rect.y = 0
        self._current_roi.current_rect.w = 0
        self._current_roi.current_rect.h = 0

    def _drag_roi(self, event, x, y, flags, frame):
        self._current_roi.image = frame

        if x < self._current_roi.canvas_boundaries.x:
            x = self._current_roi.canvas_boundaries.x

        if y < self._current_roi.canvas_boundaries.y:
            y = self._current_roi.canvas_boundaries.y

        if x > (self._current_roi.canvas_boundaries.x + self._current_roi.canvas_boundaries.w - 1):
            x = self._current_roi.canvas_boundaries.x + self._current_roi.canvas_boundaries.w - 1

        if y > (self._current_roi.canvas_boundaries.y + self._current_roi.canvas_boundaries.h - 1):
            y = self._current_roi.canvas_boundaries.y + self._current_roi.canvas_boundaries.h - 1

        if event == cv.EVENT_LBUTTONDOWN:
            self._mouse_down(x, y, self._current_roi)

        if event == cv.EVENT_LBUTTONUP:
            self._mouse_up(x, y, self._current_roi)

        if event == cv.EVENT_MOUSEMOVE:
            self._mouse_move(x, y, self._current_roi)

        if event == cv.EVENT_LBUTTONDBLCLK:
            self._mouse_double_click(x, y, self._current_roi)

    def _point_in_rect(self, pX, pY, rX, rY, rW, rH):
        if rX <= pX <= (rX + rW) and rY <= pY <= (rY + rH):
            return True
        else:
            return False

    def _new_roi(self):
        self._current_roi = DragRect(len(self._rois))
        self._init_roi()

        self._rois.append(self._current_roi)

    def _mouse_double_click(self, e_x, e_y, drag_obj):
        # remove current roi to avoid double click bug
        if sum(self._current_roi.current_rect.to_array()) == 0:
            self._rois.pop()
            self._current_roi = self._rois[-1]

        for r in self._rois:
            if self._point_in_rect(e_x, e_y, r.current_rect.x, r.current_rect.y, r.current_rect.w, r.current_rect.h):
                self._current_roi = r
                self._current_roi.active = True

    def _mouse_down(self, e_x, e_y, drag_obj):
        if drag_obj.active:

            if self._point_in_rect(e_x, e_y, drag_obj.current_rect.x - drag_obj.marker_size,
                        drag_obj.current_rect.y - drag_obj.marker_size,
                        drag_obj.marker_size * 2, drag_obj.marker_size * 2):
                drag_obj.TL = True
                return

            if self._point_in_rect(e_x, e_y, drag_obj.current_rect.x + drag_obj.current_rect.w - drag_obj.marker_size,
                        drag_obj.current_rect.y - drag_obj.marker_size,
                        drag_obj.marker_size * 2, drag_obj.marker_size * 2):
                drag_obj.TR = True
                return

            if self._point_in_rect(e_x, e_y, drag_obj.current_rect.x - drag_obj.marker_size,
                        drag_obj.current_rect.y + drag_obj.current_rect.h - drag_obj.marker_size,
                        drag_obj.marker_size * 2, drag_obj.marker_size * 2):
                drag_obj.BL = True
                return

            if self._point_in_rect(e_x, e_y, drag_obj.current_rect.x + drag_obj.current_rect.w - drag_obj.marker_size,
                        drag_obj.current_rect.y + drag_obj.current_rect.h - drag_obj.marker_size,
                        drag_obj.marker_size * 2, drag_obj.marker_size * 2):
                drag_obj.BR = True
                return


            if self._point_in_rect(e_x, e_y, drag_obj.current_rect.x + drag_obj.current_rect.w / 2 - drag_obj.marker_size,
                        drag_obj.current_rect.y - drag_obj.marker_size,
                        drag_obj.marker_size * 2, drag_obj.marker_size * 2):
                drag_obj.TM = True
                return

            if self._point_in_rect(e_x, e_y, drag_obj.current_rect.x + drag_obj.current_rect.w / 2 - drag_obj.marker_size,
                        drag_obj.current_rect.y + drag_obj.current_rect.h - drag_obj.marker_size,
                        drag_obj.marker_size * 2, drag_obj.marker_size * 2):
                drag_obj.BM = True
                return

            if self._point_in_rect(e_x, e_y, drag_obj.current_rect.x - drag_obj.marker_size,
                        drag_obj.current_rect.y + drag_obj.current_rect.h / 2 - drag_obj.marker_size,
                        drag_obj.marker_size * 2, drag_obj.marker_size * 2):
                drag_obj.LM = True
                return

            if self._point_in_rect(e_x, e_y, drag_obj.current_rect.x + drag_obj.current_rect.w - drag_obj.marker_size,
                        drag_obj.current_rect.y + drag_obj.current_rect.h / 2 - drag_obj.marker_size,
                        drag_obj.marker_size * 2, drag_obj.marker_size * 2):
                drag_obj.RM = True
                return

            # This has to be below all of the other conditions
            if self._point_in_rect(e_x, e_y, drag_obj.current_rect.x, drag_obj.current_rect.y, drag_obj.current_rect.w, drag_obj.current_rect.h):
                drag_obj.anchor.x = e_x - drag_obj.current_rect.x
                drag_obj.anchor.w = drag_obj.current_rect.w - drag_obj.anchor.x
                drag_obj.anchor.y = e_y - drag_obj.current_rect.y
                drag_obj.anchor.h = drag_obj.current_rect.h - drag_obj.anchor.y
                drag_obj.hold = True

                return

            self._new_roi()
            return


        else:
            drag_obj.current_rect.x = e_x
            drag_obj.current_rect.y = e_y
            drag_obj.drag = True
            drag_obj.active = True
            return

    def _mouse_move(self, e_x, e_y, drag_obj):
        if drag_obj.drag & drag_obj.active:
            drag_obj.current_rect.w = e_x - drag_obj.current_rect.x
            drag_obj.current_rect.h = e_y - drag_obj.current_rect.y
            self._draw(drag_obj)
            drag_obj.used = True

            return

        if drag_obj.hold:
            drag_obj.current_rect.x = e_x - drag_obj.anchor.x
            drag_obj.current_rect.y = e_y - drag_obj.anchor.y

            if drag_obj.current_rect.x < drag_obj.canvas_boundaries.x:
                drag_obj.current_rect.x = drag_obj.canvas_boundaries.x

            if drag_obj.current_rect.y < drag_obj.canvas_boundaries.y:
                drag_obj.current_rect.y = drag_obj.canvas_boundaries.y

            if (drag_obj.current_rect.x + drag_obj.current_rect.w) > (drag_obj.canvas_boundaries.x + drag_obj.canvas_boundaries.w - 1):
                drag_obj.current_rect.x = drag_obj.canvas_boundaries.x + drag_obj.canvas_boundaries.w - 1 - drag_obj.current_rect.w

            if (drag_obj.current_rect.y + drag_obj.current_rect.h) > (drag_obj.canvas_boundaries.y + drag_obj.canvas_boundaries.h - 1):
                drag_obj.current_rect.y = drag_obj.canvas_boundaries.y + drag_obj.canvas_boundaries.h - 1 - drag_obj.current_rect.h


            self._draw(drag_obj)
            return

        if drag_obj.TL:
            drag_obj.current_rect.w = (drag_obj.current_rect.x + drag_obj.current_rect.w) - e_x
            drag_obj.current_rect.h = (drag_obj.current_rect.y + drag_obj.current_rect.h) - e_y
            drag_obj.current_rect.x = e_x
            drag_obj.current_rect.y = e_y
            self._draw(drag_obj)
            return

        if drag_obj.BR:
            drag_obj.current_rect.w = e_x - drag_obj.current_rect.x
            drag_obj.current_rect.h = e_y - drag_obj.current_rect.y
            self._draw(drag_obj)
            return

        if drag_obj.TR:
            drag_obj.current_rect.h = (drag_obj.current_rect.y + drag_obj.current_rect.h) - e_y
            drag_obj.current_rect.y = e_y
            drag_obj.current_rect.w = e_x - drag_obj.current_rect.x
            self._draw(drag_obj)
            return

        if drag_obj.BL:
            drag_obj.current_rect.w = (drag_obj.current_rect.x + drag_obj.current_rect.w) - e_x
            drag_obj.current_rect.x = e_x
            drag_obj.current_rect.h = e_y - drag_obj.current_rect.y
            self._draw(drag_obj)
            return


        if drag_obj.TM:
            drag_obj.current_rect.h = (drag_obj.current_rect.y + drag_obj.current_rect.h) - e_y
            drag_obj.current_rect.y = e_y
            self._draw(drag_obj)
            return

        if drag_obj.BM:
            drag_obj.current_rect.h = e_y - drag_obj.current_rect.y
            self._draw(drag_obj)
            return

        if drag_obj.LM:
            drag_obj.current_rect.w = (drag_obj.current_rect.x + drag_obj.current_rect.w) - e_x
            drag_obj.current_rect.x = e_x
            self._draw(drag_obj)
            return

        if drag_obj.RM:
            drag_obj.current_rect.w = e_x - drag_obj.current_rect.x
            self._draw(drag_obj)
            return

    def _mouse_up(self, e_x, e_y, drag_obj):

        drag_obj.drag = False
        self._disable_resize_buttons(drag_obj)
        self._straighten_up_rect(drag_obj)

        if drag_obj.current_rect.w == 0 or drag_obj.current_rect.h == 0:
            drag_obj.active = False


        self._draw(drag_obj)

    def _draw(self, drag_obj):
        tmp = drag_obj.image.copy()

        for r in self._rois:
            if r.used:
                if r.id == self._current_roi.id:
                    color = (0, 255, 0)
                    self._draw_select_markers(tmp, r, color)
                else:
                    color = (255, 255, 0)

                cv.rectangle(tmp, (r.current_rect.x, r.current_rect.y), (r.current_rect.x + r.current_rect.w,r.current_rect.y + r.current_rect.h), color, 2)

        cv.imshow(self._window_name, tmp)

    def _disable_resize_buttons(self, drag_obj):
        drag_obj.TL = drag_obj.TM = drag_obj.TR = False
        drag_obj.LM = drag_obj.RM = False
        drag_obj.BL = drag_obj.BM = drag_obj.BR = False
        drag_obj.hold = False

    def _straighten_up_rect(self, drag_obj):
        if drag_obj.current_rect.w < 0:
            drag_obj.current_rect.x = drag_obj.current_rect.x + drag_obj.current_rect.w
            drag_obj.current_rect.w = -drag_obj.current_rect.w

        if drag_obj.current_rect.h < 0:
            drag_obj.current_rect.y = drag_obj.current_rect.y + drag_obj.current_rect.h
            drag_obj.current_rect.h = -drag_obj.current_rect.h

    def _draw_select_markers(self, image, drag_obj, color):

        # Top-Left
        cv.rectangle(image, (int(drag_obj.current_rect.x - drag_obj.marker_size),int(drag_obj.current_rect.y - drag_obj.marker_size)), (int(drag_obj.current_rect.x - drag_obj.marker_size + drag_obj.marker_size * 2),int(drag_obj.current_rect.y - drag_obj.marker_size + drag_obj.marker_size * 2)), color, 2)

        # Top-Rigth
        cv.rectangle(image, (int(drag_obj.current_rect.x + drag_obj.current_rect.w - drag_obj.marker_size),int(drag_obj.current_rect.y - drag_obj.marker_size)),(int(drag_obj.current_rect.x + drag_obj.current_rect.w - drag_obj.marker_size + drag_obj.marker_size * 2),int(drag_obj.current_rect.y - drag_obj.marker_size + drag_obj.marker_size * 2)),color, 2)

        # Bottom-Left
        cv.rectangle(image, (int(drag_obj.current_rect.x - drag_obj.marker_size),int(drag_obj.current_rect.y + drag_obj.current_rect.h - drag_obj.marker_size)),(int(drag_obj.current_rect.x - drag_obj.marker_size + drag_obj.marker_size * 2),int(drag_obj.current_rect.y + drag_obj.current_rect.h - drag_obj.marker_size + drag_obj.marker_size * 2)),color, 2)

        # Bottom-Right
        cv.rectangle(image, (int(drag_obj.current_rect.x + drag_obj.current_rect.w - drag_obj.marker_size),int(drag_obj.current_rect.y + drag_obj.current_rect.h - drag_obj.marker_size)),(int(drag_obj.current_rect.x + drag_obj.current_rect.w - drag_obj.marker_size + drag_obj.marker_size * 2),int(drag_obj.current_rect.y + drag_obj.current_rect.h - drag_obj.marker_size + drag_obj.marker_size * 2)),color, 2)

        # Top-Mid
        cv.rectangle(image, (int(drag_obj.current_rect.x + drag_obj.current_rect.w / 2 - drag_obj.marker_size),int(drag_obj.current_rect.y - drag_obj.marker_size)),(int(drag_obj.current_rect.x + drag_obj.current_rect.w / 2 - drag_obj.marker_size + drag_obj.marker_size * 2),int(drag_obj.current_rect.y - drag_obj.marker_size + drag_obj.marker_size * 2)),color, 2)

        # Bottom-Mid
        cv.rectangle(image, (int(drag_obj.current_rect.x + drag_obj.current_rect.w / 2 - drag_obj.marker_size),int(drag_obj.current_rect.y + drag_obj.current_rect.h - drag_obj.marker_size)),(int(drag_obj.current_rect.x + drag_obj.current_rect.w / 2 - drag_obj.marker_size + drag_obj.marker_size * 2),int(drag_obj.current_rect.y + drag_obj.current_rect.h - drag_obj.marker_size + drag_obj.marker_size * 2)),color, 2)

        # Left-Mid
        cv.rectangle(image, (int(drag_obj.current_rect.x - drag_obj.marker_size),int(drag_obj.current_rect.y + drag_obj.current_rect.h / 2 - drag_obj.marker_size)),(int(drag_obj.current_rect.x - drag_obj.marker_size + drag_obj.marker_size * 2),int(drag_obj.current_rect.y + drag_obj.current_rect.h / 2 - drag_obj.marker_size + drag_obj.marker_size * 2)),color, 2)

        # Right-Mid
        cv.rectangle(image, (int(drag_obj.current_rect.x + drag_obj.current_rect.w - drag_obj.marker_size),int(drag_obj.current_rect.y + drag_obj.current_rect.h / 2 - drag_obj.marker_size)),(int(drag_obj.current_rect.x + drag_obj.current_rect.w - drag_obj.marker_size + drag_obj.marker_size * 2),int(drag_obj.current_rect.y + drag_obj.current_rect.h / 2 - drag_obj.marker_size + drag_obj.marker_size * 2)),color, 2)
