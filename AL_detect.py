import sys
import time

import torch
from tqdm import tqdm  # 导入 tqdm 库

from models.experimental import attempt_load
from utils.datasets import LoadImages
from utils.general import check_img_size, non_max_suppression, scale_coords, xyxy2xywh
from utils.torch_utils import select_device, time_synchronized


def AL_detect(opt):
    # 检测图像
    # 权重文件、检测数据源、使用的图像大小
    weights, source, imgsz = opt.weights, opt.source, opt.img_size

    # 初始化
    device = select_device(opt.device)
    half = device.type != 'cpu'

    # 加载模型
    model = attempt_load(weights=weights, map_location=device)
    imgsz = check_img_size(imgsz, s=model.stride.max())  # 检查图像大小
    if half:
        model.half()  # 转为 FP16
    dataset = LoadImages(source, img_size=imgsz)

    # 获取类别名称和颜色
    names = model.module.names if hasattr(model, 'module') else model.names

    # 执行推理
    t0 = time.time()
    img = torch.zeros((1, 3, imgsz, imgsz), device=device)  # 初始化图像
    _ = model(img.half() if half else img) if device.type != 'cpu' else None  # 执行一次推理

    result = {}

    # 使用 tqdm 创建进度条
    total_images = len(dataset)  # 总图像数量
    progress_bar = tqdm(total=total_images, desc="Processing", unit="image", dynamic_ncols=True)

    # 遍历所有图像
    for path, img, im0s, vid_cap in dataset:
        img = torch.from_numpy(img).to(device)
        img = img.half() if half else img.float()  # uint8 转为 fp16/32
        # 图像归一化处理
        img /= 255.0  # 0 - 255 转为 0.0 - 1.0
        if img.ndimension() == 3:
            img = img.unsqueeze(0)

        # 推理
        t1 = time_synchronized()
        pred = model(img, augment=opt.augment)[0]

        # 应用 NMS (非最大抑制)
        pred = non_max_suppression(pred, opt.conf_thres, opt.iou_thres, classes=opt.classes, agnostic=opt.agnostic_nms)
        t2 = time_synchronized()

        # 处理检测结果
        result[path] = []

        for i, det in enumerate(pred):  # 每个图像的检测结果
            p, s, im0, frame = path, '', im0s, getattr(dataset, 'frame', 0)
            s += '%gx%g ' % img.shape[2:]  # 输出图像尺寸
            gn = torch.tensor(im0.shape)[[1, 0, 1, 0]]  # 归一化增益 whwh

            if len(det):
                # 将边框从 img_size 缩放到 im0 大小
                det[:, :4] = scale_coords(img.shape[2:], det[:, :4], im0.shape).round()

                # 将框的信息保存到文件
                for *xyxy, conf, cls in reversed(det):
                    xywh = (xyxy2xywh(torch.tensor(xyxy).view(1, 4)) / gn).view(-1).tolist()  # 归一化 xywh
                    x, y, w, h = xywh
                    data = {"class": cls.item(), "box": [x, y, w, h], "conf": conf.item()}
                    result[path].append(data)

        # 更新进度条
        progress_bar.update(1)

    progress_bar.close()  # 关闭进度条

    # 移除总时间打印
    return result
