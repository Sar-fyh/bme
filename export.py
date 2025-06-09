"""将 YOLOv5 *.pt 模型导出为 ONNX 和 TorchScript 格式

用法:
    $ export PYTHONPATH="$PWD" && python models/export.py --weights ./weights/yolov5s.pt --img 640 --batch 1
"""
import argparse
import sys
import time
import torch
import argparse
import chardet
from experimental import attempt_load
sys.path.append(r'/models')  # 为了在子目录中运行 '$ python *.py' 文件
sys.path.append(r'/models/utils')
import torch
import torch.nn as nn
from experimental import attempt_load
from utils.activations import Hardswish, SiLU
from utils.general import set_logging, check_img_size
import common

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--weights', type=str, default='C://system//system//1//runs//train//gun//weights//best.pt', help='权重路径')  # yolov5/models/ 中的路径
    parser.add_argument('--img-size', nargs='+', type=int, default=[640, 640], help='图片尺寸')  # 高度、宽度
    parser.add_argument('--batch-size', type=int, default=1, help='批处理大小')
    opt = parser.parse_args()
    opt.img_size *= 2 if len(opt.img_size) == 1 else 1  # 扩展
    print(opt)
    set_logging()
    t = time.time()

    # 加载 PyTorch 模型
    model = attempt_load(opt.weights, map_location=torch.device('cpu'))  # 加载 FP32 模型
    try:
        labels = model.names
    except UnicodeDecodeError:
        detected_encoding = None
        for label in model.names:
            if isinstance(label, bytes):
                result = chardet.detect(label)
                detected_encoding = result['encoding']
                break
        if detected_encoding:
            try:
                labels = [label.decode(detected_encoding) if isinstance(label, bytes) else label for label in
                          model.names]
            except Exception as e:
                print(f"使用检测到的编码 {detected_encoding} 解码失败: {e}")
                labels = []
        else:
            print("无法检测到编码信息")
            labels = []

    print(labels)

    # 检查
    gs = int(max(model.stride))  # 网格大小（最大步长）
    opt.img_size = [check_img_size(x, gs) for x in opt.img_size]  # 确保 img_size 是 gs 的倍数

    # 输入
    img = torch.zeros(opt.batch_size, 3, *opt.img_size)  # 图片大小(1,3,320,192) 检测

    # 更新模型
    for k, m in model.named_modules():
        m._non_persistent_buffers_set = set()  # 与 pytorch 1.6.0 兼容
        if isinstance(m, common.Conv):  # 分配导出友好的激活函数
            if isinstance(m.act, nn.Hardswish):
                m.act = Hardswish()
            elif isinstance(m.act, nn.SiLU):
                m.act = SiLU()
        # elif isinstance(m, models.yolo.Detect):
        #     m.forward = m.forward_export  # 分配 forward（可选）
    model.model[-1].export = True  # 设置 Detect() 层的 export=True
    y = model(img)  # 干扰运行

    # TorchScript 导出
    try:
        print('\n开始使用 torch %s 导出 TorchScript...' % torch.__version__)
        f = opt.weights.replace('.pt', '.torchscript.pt')  # 文件名
        ts = torch.jit.trace(model, img)
        ts.save(f)
        print('TorchScript 导出成功，保存为 %s' % f)
    except Exception as e:
        print('TorchScript 导出失败：%s' % e)

    # ONNX 导出
    try:
        import onnx

        print('\n开始使用 onnx %s 导出 ONNX...' % onnx.__version__)
        f = opt.weights.replace('.pt', '.onnx')  # 文件名
        torch.onnx.export(model, img, f, verbose=False, opset_version=12, input_names=['images'],
                          output_names=['classes', 'boxes'] if y is None else ['output'])

        # 检查
        onnx_model = onnx.load(f)  # 加载 onnx 模型
        onnx.checker.check_model(onnx_model)  # 检查 onnx 模型
        # print(onnx.helper.printable_graph(onnx_model.graph))  # 打印可读性更好的模型
        print('ONNX 导出成功，保存为 %s' % f)
    except Exception as e:
        print('ONNX 导出失败：%s' % e)

    # CoreML 导出
    try:
        import coremltools as ct

        print('\n开始使用 coremltools %s 导出 CoreML...' % ct.__version__)
        # 从 torchscript 转换模型并根据 detect.py 进行像素缩放
        model = ct.convert(ts, inputs=[ct.ImageType(name='image', shape=img.shape, scale=1 / 255.0, bias=[0, 0, 0])])
        f = opt.weights.replace('.pt', '.mlmodel')  # 文件名
        model.save(f)
        print('CoreML 导出成功，保存为 %s' % f)
    except Exception as e:
        print('CoreML 导出失败：%s' % e)

    # 完成
    print('\n导出完成（%.2fs）。使用 https://github.com/lutzroeder/netron 进行可视化。' % (time.time() - t))
