
import rosbag
import cv_bridge
import cv2
import numpy as np
import os
import sys
import shutil
from tqdm import tqdm
import argparse


class Bag2Video(object):
    """Generates videos from every sensor_msgs/Image topic
    """

    def __init__(self, bag_path):
        """Initalized with ROS bag path

        Parameters
        ----------
        bag_path : [string]
            [ROS bag path]
        """
        self.bag = rosbag.Bag(bag_path)
        self.topic_list = {}

    @property
    def topics_info(self):
        """return a dictionary of topics : [frequency, number of messages] 

        Returns
        -------
        [dict]
            [topic name as a key and info as value]
        """
        if len(self.topic_list) == 0:
            self._generate_topics_info()
        return self.topic_list

    def _generate_topics_info(self):
        """parse the bag to get topics info
        """
        x = self.bag.get_type_and_topic_info()[1]
        for key in x.keys():
            if x[key][0] == 'sensor_msgs/Image':
                self.topic_list[key] = (np.ceil(x[key][-1]), x[key][1])

    def process(self):
        """Process the bag topics and save video files
        """
        if len(self.topic_list) == 0:
            self._generate_topics_info()
        files_names = []
        bridge = cv_bridge.CvBridge()
        for key in self.topic_list.keys():
            name = key
            file_name = (name.replace("/", "_")+".avi")[1:]
            files_names.append(file_name)
            x = next(self.bag.read_messages(name))
            img = bridge.imgmsg_to_cv2(x.message)
            width = img.shape[1]
            height = img.shape[0]
            fps = self.topic_list[name][0]
            msgs_count = self.topic_list[name][1]
            print("\n---------------- Generting ----------------------")
            print("File name: " + file_name)
            print("Frame Size: " + str((width, height)))
            print("FPS: " + str(fps))
            print("Messages Count: " + str(msgs_count))
            sys.stdout.flush()
            codec = cv2.VideoWriter_fourcc('M', 'J', 'P', 'G')
            if len(img.shape) == 2:
                out = cv2.VideoWriter(
                    file_name, codec, fps, (width, height), 0)
            else:
                out = cv2.VideoWriter(file_name, codec, fps, (width, height))

            with tqdm(total=msgs_count) as pbar:
                for topic, msg, t in self.bag.read_messages(topics=[name]):
                    img = bridge.imgmsg_to_cv2(msg)
                    out.write(np.uint8(img))
                    pbar.update(1)
            out.release()
            del(out)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description='Extract videos from ROS bag files.')
    parser.add_argument('--bag', '-b', action='store', default=None,
                        help='ROS bag path.')
    args = parser.parse_args()
    bag_video = Bag2Video(args.bag)
    bag_video.process()
