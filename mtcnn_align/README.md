# mtcnn face align
执行人脸对齐并裁剪
- input: 人脸检测json结果, 包含人脸的图片
- output: 对齐后的人脸图片

## 文件结构
- matlab_cp2tform.py 计算转换矩阵
- mtcnn_aligner.py mtcnn计算5点关键点
- fx_warp_and_crop_face.py 计算人脸参考点, 计算变换矩阵, 执行对齐和crop
- face_align.py 封装FaceAligner类
