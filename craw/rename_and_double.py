# -*- coding: utf-8 -*-

# 1. 将图片按md5值rename
# 2. 将原图resize到 100x100. 保持目录结构

import os
import hashlib
import datetime
import argparse

def parse_args():
    parser = argparse.ArgumentParser(description='rename and double.')
    parser.add_argument('--imgdir', dest='imgdir', type=str,
        help="源图片目录, 可包含子目录")

    return parser.parse_args()

def rename_md5(img_dir):
    all_imgs_list = []
    for root, _, files in os.walk(img_dir):
        img_list = [os.path.join(root, file) for file in files
                    if not(file.startswith('.') or 
                       file in "__MACOS")]
        all_imgs_list.extend(img_list)

    for img in all_imgs_list:
        with open(img, 'r') as f:
            md5_obj = hashlib.md5()
            md5_obj.update(f.read())
            hash_str = md5_obj.hexdigest()
            newname = os.path.join('/'.join(img.split('/')[:-1]),
                                   'img-' + hash_str + '.' + img.split('.')[-1])
            os.rename(img, newname)
            print("rename ok: %s ---> %s" % (img, newname))

def reshape(src_dir, dst_dir):
    """
    将src_dir中的图片resize到100x100, 保存到dst_dir
    保持目录结构不变
    """
    if not os.path.exists(src_dir):
        print("%s doesn\'t exist" % src_dir)
        return
    pass


if __name__ == "__main__":
    args = parse_args()
    print("step1 --> md5 rename...")
    # rename_md5(args.imgdir)
    print('rename done.')
    print('step2 --> reshape...')
    reshape(args.imgdir)
    print('reshape done.')

