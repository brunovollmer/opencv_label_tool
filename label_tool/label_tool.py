"""
LabelTool Module
"""
import json
import cv2 as cv
import numpy as np

from label_tool.renderer import Renderer
from label_tool.roi_creator import RoiCreator
from util.tracker import RoiTracker
from util.custom_encoder import CustomEncoder

class LabelTool:
    """
    LabelTool class, which holds all functionality to label a given video with multiple rois.
    """

    def __init__(self, video_path, config_path, output_path, prev_results=False, image_func=None, classify=False):
        """
        LabelTool constructor.

        Arguments:
            video_path {string} -- path to video file
            config_path {string} -- path to config file
            output_path {string} -- path to output file

        Keyword Arguments:
            prev_results {bool} -- are previous results avaliable (with output_path as path) (default: {False})
            classify {bool} -- should classifier pre classify data (default: {False})
            image_func {python function} -- function that somehow converts the image (default: None)
        """

        self._prev_results = prev_results
        self._output_path = output_path

        self._image_func = image_func

        self._load_video(video_path)
        self._load_config(config_path)
        self._load_results(output_path)

        if classify:
            self._run_classifier()

    def _run_classifier(self):
        """
        "Pre-classify" the given video by running the classifier and saving the results.
        """

        # only import if classification is needed
        from util.classifier import Classifier

        classifier = Classifier()

        frame_counter = 0

        # iterate over all frames
        while self._video.isOpened():
            # get current frame
            ret, frame = self._video.read()

            # check if frame was read successfully
            if not ret:
                break

            # convert frame if self._image_func is set
            if self._image_func:
                frame = self._image_func(self._config, frame)

            rois = classifier.detect(frame)

            # save results
            self._results[frame_counter] = {"rois": rois, "event": None}

            frame_counter += 1

    def _load_config(self, path):
        """
        Load config file.

        Arguments:
            path {string} -- path to config file
        """

        with open(path, "r") as read_file:
            config = json.load(read_file)

        self._config = config
        self._events = config["events"]

    def _load_results(self, path):
        """
        Load previous results

        Arguments:
            path {string} -- path to previous results
        """

        # check if previous results are avaliable
        if self._prev_results:
            # try to open the file -> catch json errors
            try:
                # load results and convert all keys to int
                with open(path, "r") as read_file:
                    tmp_results = json.load(read_file)

                results = {}

                for key, value in tmp_results.items():
                    results[int(key)] = value

            except json.JSONDecodeError as exception:
                print(
                    "could not load json results. json exception: {}".format(exception))
                exit(1)

            print("loaded previous results")
        else:
            # no previous results avaliable -> save empty dict
            results = {}

        self._results = results

    def _load_video(self, path):
        """
        Load the input video from path with the help of OpenCV.
        Compute the general metrics for the video and save them:
        - fps
        - frame count
        - duration
        - width
        - height

        Arguments:
            path {string} -- path to video
        """
        self._video = cv.VideoCapture(path)
        self._video_fps = self._video.get(cv.CAP_PROP_FPS)
        self._video_frame_count = int(self._video.get(cv.CAP_PROP_FRAME_COUNT))
        self._video_duration = self._video_frame_count/self._video_fps
        self._video_width = int(self._video.get(cv.CAP_PROP_FRAME_WIDTH))
        self._video_height = int(self._video.get(cv.CAP_PROP_FRAME_HEIGHT))

        print("video path: {} \nframes: {} \nfps: {} \nduration: {}s".format(path, self._video_frame_count, round(self._video_fps, 2), round(self._video_duration, 2)))

    def _saveResults(self, results):
        """
        Save given results to output path.

        Arguments:
            results {dict} -- results of the labelling
        """

        with open(self._output_path, "w") as outfile:
            json.dump(results, outfile, cls=CustomEncoder)

        print("saved results in {} at current directory".format(self._output_path))

    def _write_text(self, image, text):
        """
        Write text in the given frame.

        Arguments:
            image {opencv image} -- input image
            text {string} -- text that should be written
        """

        font = cv.FONT_HERSHEY_SIMPLEX

        (text_width, text_height) = cv.getTextSize(
            text, font, fontScale=1, thickness=1)[0]

        # set the text start position
        text_offset_x = 10
        text_offset_y = image.shape[0]-10
        # make the coords of the box with a small padding of two pixels
        box_coords = ((text_offset_x + 2, text_offset_y + 2),
                     (text_offset_x + text_width - 2, text_offset_y - text_height - 2))

        cv.rectangle(image, box_coords[0],
                     box_coords[1], (255, 255, 255), cv.FILLED)

        cv.putText(image, text, (text_offset_x, text_offset_y),
                   font, 1, (0, 255, 0), 2, cv.LINE_AA)

    def run(self):
        """
        Run LabelTool.
        """

        # create renderer
        renderer = Renderer(self._video_fps)

        # create tracker
        tracker = RoiTracker()

        # initialize frame counter
        frame_counter = 0

        # iterate over all frames
        while self._video.isOpened():
            # get current frame
            ret, frame = self._video.read()

            # check if frame was read successfully
            if not ret:
                break

            # convert frame if self._image_func is set
            if self._image_func:
                frame = self._image_func(self._config, frame)

            # create roi creator for each frame
            roi_creator = RoiCreator(self._video_width, self._video_height, renderer.window_name)

            rois = []

            # check if there are prev. results in self._results for current frame
            if frame_counter in self._results:
                event = self._results[frame_counter].get("event", None)
                rois += self._results[frame_counter].get("rois", None)
            else:
                event = None

            print("current frame: {}, rois: {}, event: {}, playback speed: {} ms per frame".format(frame_counter, rois, event, renderer.current_speed))

            # check if there are some rois
            if rois:
                roi_creator.load_rois(rois, frame)

            # write current event in frame
            self._write_text(frame, "event: {}".format(event))

            # check mode of rendering and either create mousecallback for roi creation or draw found rois in frame
            if renderer.frame_by_frame:
                roi_creator.set_mouse_callback(frame)
            else:
                frame = roi_creator.draw_rois(frame)

            # render current frame
            renderer.current_frame = frame
            key = renderer.show_frame()

            # check, which action has to be performed
            if key == 99:
                # key: c
                self._video.set(cv.CAP_PROP_POS_FRAMES, 1)
                print("jumped to start of video")
                frame_counter = 0
            elif key == 113:
                # key: q
                break
            elif key == 32:
                # key: SPACE
                renderer.pause_play()
            elif key == 97:
                # key: a
                renderer.slower()
            elif key == 115:
                # key: s
                renderer.faster()
            elif key in [49, 50, 51, 52, 53, 54, 55, 56, 57]:
                tmpIndex = int(key) - 49
                if tmpIndex >= len(self._events):
                    print("invalid event key")
                else:
                    event = self._events[tmpIndex]
            elif key == 48:
                # key: v
                event = None
            elif key == 120:
                # key: x
                roi_creator.remove_current_roi()
            elif key == 112:
                # key: p
                if not tracker.initialized:
                    tracker.init_tracker(frame, roi_creator.get_current_roi())
                else:
                    tracker.destroy_tracker()

            # check if there are results
            if tracker.initialized:
                tracked_roi = tracker.track(frame)
                roi_creator.add_roi(tracked_roi, frame, color=(255, 255, 255))

            # get rois of roi_creator
            rois = roi_creator.get_rois()

            # save results for current frame
            if frame_counter in self._results:
                self._results[frame_counter] = {"rois": rois, "event": event}
            else:
                if rois or event is not None:
                    self._results[frame_counter] = {
                        "rois": rois, "event": event}

            # check which frame is next
            if key == 255 and not renderer.frame_by_frame:
                # key: NO KEY
                frame_counter += 1
            elif key == 110:
                # key: n
                if renderer.frame_by_frame and frame_counter > 0:
                    frame_counter -= 1
            elif key == 109:
                # key: m
                if renderer.frame_by_frame and frame_counter < self._video_frame_count:
                    frame_counter += 1

            # remove mousecallback if it was set for current frame
            if renderer.frame_by_frame:
                roi_creator.remove_mouse_callback()

            # set next frame
            self._video.set(cv.CAP_PROP_POS_FRAMES, frame_counter)

        # destroy video and opencv objects
        self._video.release()
        cv.destroyAllWindows()

        # finally save results
        self._saveResults(self._results)
