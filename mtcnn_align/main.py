#!/usr/bin/env python
# -*- coding: utf-8 -*-

import urllib
import numpy as np
import cv2
import os
import sys
import json
import argparse
import math 
reload(sys)
sys.setdefaultencoding("utf-8")
os.environ['GLOG_minloglevel'] = '2'  # suppress log

from mtcnn_aligner import MtcnnAligner
from face_aligner import FaceAligner
from fx_warp_and_crop_face import get_reference_facial_points, warp_and_crop_face


output_size = (112, 112)
default_square = True
inner_padding_factor = 0
outer_padding = (0, 0)

reference_5pts = get_reference_facial_points(output_size,
                                            inner_padding_factor,
                                            outer_padding,
                                            default_square)

def parse_args():
    parser = argparse.ArgumentParser(description='face alignment by MTCNN')
    parser.add_argument('--det-json', type=str, required=True,
                        help='人脸检测结果(json)')
    parser.add_argument('--save-dir', type=str, required=True,
                        help='align+crop后人脸图片')
    parser.add_argument('--mtcnn-model-dir', type=str, required=True,
                        help='mtcnn模型根目录')
    parser.add_argument('--gpu-id', type=int, default=0,
                        help='gpi id')
    args = parser.parse_args()
    return args

def _pull_img(url):
    """
    从网络流读取图片
    Args:
    ----
    url: 图片url

    Return:
    ------
    img: 图片
         若读取失败, img=None
    """
    try:
        res = urllib.urlopen(url)
        # res = urllib.request.urlopen(url)
        img = np.asarray(bytearray(res.read()), dtype='uint8')
        img = cv2.imdecode(img, cv2.IMREAD_COLOR)
    except Exception as e:
        print("Excerption: %s --> %s" % (url, e))
        img = None
    return img


def main():
    args = parse_args()
    det_json = args.det_json
    save_dir = args.save_dir
    model_dir = args.mtcnn_model_dir
    gpu_id = args.gpu_id

    aligner = FaceAligner(model_dir, gpu_id=gpu_id)

    index = 0
    with open(det_json, "r") as f:
        for line in f:
            index += 1
            print("Processing img %d" % index)
            line = json.loads(line.strip())

            # 一个url对应一个pts
            url = str(line["url"])
            if not line['det']:
                continue
            pts = line['det'][0]['boundingBox']['pts']

            # 图片以人名为前缀, 若无, 则为neg
            name = str(url.split('/')[-2])
            img_name = url.split('/')[-1]

            sub_save_dir = os.path.join(save_dir, name)
            if not os.path.exists(sub_save_dir):
                os.makedirs(sub_save_dir)

            img = _pull_img(url)
            if img is None:
                continue

            # 只crop一张脸
            face_chip = aligner.get_face_chips(img, [pts])

            save_name = os.path.join(sub_save_dir, img_name)
            cv2.imwrite(save_name, face_chip[0])

if __name__ == "__main__":
    main()
