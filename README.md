# face_work
存放人脸相关代码, 包括:
- face_det 调用线上人脸检测
- mtcnn 人脸对齐

## 数据集
数据集从网络爬取, 一般是2x 人脸检测框的图片.   
注: 图片存放在以人名命名的文件夹中.

## 图片上传
upload_tool.py 将目录中的图片上传至bucket
```
$ python upload_tool.py -h
usage: upload [-h] --root-dir ROOT_DIR --bucket BUCKET --urllist URLLIST
              [--no-keep] [--thread THREAD] --config CONFIG

optional arguments:
  -h, --help           show this help message and exit
  --root-dir ROOT_DIR  待上传文件所在根目录
  --bucket BUCKET      上传bucket
  --urllist URLLIST    保存的urllist文件
  --no-keep            上传后是否保持原目录结构[默认True]
  --thread THREAD      并发数, 默认10
  --config CONFIG      ak sk 配置文件

其中:
config 文件
{
    "ak": "**",
    "sk": "**"
}
按需填入
```
上传完成后, 生成url列表文件.

## 人脸检测face_det
调用线上人脸检测api.
- Input : url list 文件, 每行一个url
- Output : 人脸检测结果, json, 每行一个json
```
$ python face_det.py -h
usage: face_det.py [-h] --urls URLS --log LOG [--num-thread NUM_THREAD]
                   [--config CONFIG]

face detection

optional arguments:
  -h, --help            show this help message and exit
  --urls URLS           url文件, 每行一个url
  --log LOG             检测结果
  --num-thread NUM_THREAD
                        线程数
  --config CONFIG       配置文件, 默认[det.conf]
```

## 人脸align和crop
mtcnn 人脸alignment, 并crop出112x112的人脸(与线上一致)
Input : 人脸检测json
Output : 112x112人脸图片, 可直接用于模型提特征
**注**: 若检出多张脸, 只处理一张.
```
> cd mtcnn_align

usage: main.py [-h] --det-json DET_JSON --save-dir SAVE_DIR --mtcnn-model-dir
               MTCNN_MODEL_DIR [--gpu-id GPU_ID]

face alignment by MTCNN

optional arguments:
  -h, --help            show this help message and exit
  --det-json DET_JSON   人脸检测结果(json)
  --save-dir SAVE_DIR   align+crop后人脸图片
  --mtcnn-model-dir MTCNN_MODEL_DIR
                        mtcnn模型根目录
  --gpu-id GPU_ID       gpi id
```
**注**: 若原url以人名为前缀, 那么保存到本地的112x112图片仍按同名文件夹存放, 例如:
```
原url : 
http://xxx/张三/0001.jpg
http://xxx/张三/0002.jpg

http://xxx/李四/0010.jpg
http://xxx/李四/0011.jpg

crop结果:
|-- 张三
|   |-- 0001.jpg
|   `-- 0002.jpg
|-- 李四
|   |-- 0010.jpg
|   `-- 0011.jpg
```
crop 后的人脸图片可直接用于线下模型提特征.
