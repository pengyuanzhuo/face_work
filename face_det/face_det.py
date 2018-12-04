# -*- coding: utf-8 -*-
# 多线程调用线上fecex-detect服务
# 默认线程10

import json
import requests
import argparse
from ava_auth import AuthFactory
from concurrent.futures import ThreadPoolExecutor
from concurrent.futures import as_completed

def parse_args():
    parser = argparse.ArgumentParser(description='face detection')
    parser.add_argument('--urls', type=str, required=True,
                        help='url文件, 每行一个url')
    parser.add_argument('--log', type=str, required=True,
                        help='检测结果')
    parser.add_argument('--num-thread', type=int, default=10,
                        help='线程数')
    parser.add_argument('--config', type=str, default='./det.conf',
                        help="配置文件, 默认[det.conf]")
    args = parser.parse_args()
    return args

def load_config(config_file):
    with open(config_file, 'r') as f:
        conf = json.load(f)
    return conf


def token_gen(ak,sk):
    factory = AuthFactory(ak,sk)
    fauth = factory.get_qiniu_auth
    token = fauth()
    return token

def url_gen(url_file):
    """
    每行一个url
    """
    urls = []
    with open(url_file, 'r') as f:
        for line in f:
            urls.append(line.strip())
    return urls

"""
def url_gen(json_file):
    urls = []
    with open(json_file, 'r') as f:
        for line in f:
            line = json.loads(line.strip())
            url = line['url']
            urls.append(url)
    return urls
"""

def request(img_url, token):
    # res = {'url':img_url,'det':[]}
    res = None
    request_url = 'http://argus.atlab.ai/v1/face/detect'
    headers = {"Content-Type": "application/json"}
    body = json.dumps({"data": {"uri": img_url}})
    try:
        r = requests.post(request_url, data=body,timeout=15, headers=headers, auth=token)
    except requests.RequestException:
        raise
    else:
        if r.status_code == 200:
            r = r.json()
            if r['code'] == 0 and r['result']['detections'] is not None:
                res = r['result']['detections']
            else:
                raise Exception("No face")
                # res = []
        else:
            raise Exception('http err --> %d'%r.status_code)
    return res

def face_det(img_urls, log, ak, sk, num_thread=10):
    """
    multithread face detect
    Args:
    -----
    img_urls : list of url
    log : face det log json file
    num_thread : num thread

    Return:
    ------
    res_list : list of result
        [{'url':'xxx',
          'det':[{},{},...]}]
    """
    token = token_gen(ak, sk)
    with open(log,'w') as f_log:
        with ThreadPoolExecutor(max_workers=num_thread) as exe:
            future_tasks = {exe.submit(request, url, token): url for url in img_urls}
            all_url = len(future_tasks)
            count = 1
            for task in as_completed(future_tasks):
                if task.done():
                    url = future_tasks[task]
                    print('fece det %d/%d'%(count,all_url))
                    count += 1
                    try:
                        det = task.result()
                    except Exception as e:
                        print('%s ---> %s'%(url, e))
                        det = []
                    res = {}
                    res['url'] = url
                    res['det'] = det
                    f_log.write(json.dumps(res))
                    f_log.write('\n')

if __name__ == "__main__":
    args = parse_args()
    conf = load_config(args.config)
    ak = conf['ak']
    sk = conf['sk']

    url_list = url_gen(args.urls)
    face_det(url_list, args.log, ak, sk, args.num_thread)
    print("Done.")

