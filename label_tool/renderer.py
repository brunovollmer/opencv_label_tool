"""
Renderer Module
"""
import cv2 as cv

class Renderer:
    """
    Renderer Class which handles the rendering of the different frames with functionality
    regarding speed and pause/play.
    """

    def __init__(self, fps):
        """
        Renderer Class constructor.

        Arguments:
            fps {int} -- fps of current video
        """

        self._current_frame = None
        self._window_name = "OpenCV Renderer"
        self._frame_by_frame = True
        self._current_speed = int((1 / int(fps)) * 1000)

        # already create named frame for the mousecallbacks
        cv.namedWindow(self._window_name)


    def show_frame(self):
        """
        Show current frame.

        Raises:
            ValueError: Current frame is none.

        Returns:
            int -- key code of pressed key
        """

        if self._current_frame is None:
            raise ValueError("current frame is none")

        if self._frame_by_frame:
            key = cv.waitKey(0)
        else:
            cv.imshow(self._window_name, self._current_frame)
            key = cv.waitKey(self._current_speed) & 0xFF

        return key

    def pause_play(self):
        """
        Pause or play the video.
        """

        self._frame_by_frame ^= True

    def slower(self):
        """
        Make the video slower until a certain threshold.
        """

        if self._current_speed * 2 <= 5000:
            self._current_speed = int(self._current_speed * 2)

    def faster(self):
        """
        Make the video faster until a certain threshold.
        """

        if self._current_speed / 2 >= 1:
            self._current_speed = int(self._current_speed / 2)
        else:
            self._current_speed = 1

    @property
    def current_speed(self):
        """
        Current speed getter.

        Returns:
            int -- current speed
        """

        return self._current_speed

    @current_speed.setter
    def current_speed(self, val):
        """
        Current speed  setter.

        Arguments:
            val {int} -- new speed
        """

        if val > 1 and val < 5000:
            self._current_speed = val

    @property
    def current_frame(self):
        """
        Current frame getter.

        Returns:
            opencv image -- current frame
        """

        return self._current_frame

    @current_frame.setter
    def current_frame(self, frame):
        """
        Current frame setter

        Arguments:
            frame {opencv image} -- new frame
        """

        self._current_frame = frame

    @property
    def window_name(self):
        """
        Window name getter.

        Returns:
            string -- current window name
        """

        return self._window_name

    @property
    def frame_by_frame(self):
        """
        Play state getter.

        Returns:
            bool -- current play state
        """

        return self._frame_by_frame

    @frame_by_frame.setter
    def frame_by_frame(self, playstate):
        """
        Play state setter.

        Arguments:
            playstate {bool} -- new play state
        """

        self._frame_by_frame = playstate
