import argparse
import os

from label_tool.label_tool import LabelTool
from util.transform_image import resize_image

def check_file(path):
    return os.path.isfile(path)

def main():

    parser = argparse.ArgumentParser(description='label a given video. if video is paused, use mouse to draw rois\n\ncontrols of the editor:\na: slower replay\ns: faster replay\nq: EXIT\nSPACE: pause or start\nn: (if pause) go to previous frame\nm: (if pause) go to next frame\n1: go to first frame\nc: car_in event\nv: car_out event\nd: delete event\nx: delete roi', formatter_class=argparse.RawTextHelpFormatter)

    parser.add_argument('path', type=str, help='path to video file')
    parser.add_argument('config', type=str, help="path to config json")
    parser.add_argument('-o', '--output', type=str, default="labels.json",
                        help='output json file name. default: ./labels.json')
    parser.add_argument('-c', '--classify', action="store_true", default=False)

    args = parser.parse_args()

    path = args.path
    output_path = args.output
    config_path = args.config
    classify = args.classify

    # check if config and video exist
    if not check_file(path):
        print("input video does not exist")
        exit(1)

    if not check_file(config_path):
        print("config file does not exist")
        exit(1)

    label_tool = LabelTool(path, config_path, output_path, prev_results=check_file(
        output_path), image_func=resize_image, classify=classify)

    label_tool.run()


if __name__ == "__main__":
    main()
