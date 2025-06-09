from AL_detect import AL_detect
import argparse
import logging
import os
from pathlib import Path
from AL_train import train
from warnings import warn
import torch.distributed as dist
import torch.utils.data
import yaml
from torch.utils.tensorboard import SummaryWriter
from general import increment_path, get_latest_run, check_file, check_git_status, set_logging
from torch_utils import select_device
import AL_config2 as config
from yolo import Model
from PIL import Image
from torchvision import transforms
logger = logging.getLogger(__name__)
from yolo import Detect
from PIL import Image
import torch
import numpy as np
import os
os.environ['NO_ALBUMENTATIONS_UPDATE'] = '1'

try:
    import wandb
except ImportError:
    wandb = None
    logger.info(
        "Install Weights & Biases for experiment logging via 'pip install wandb' (recommended)")


class Yolov5():
    model_type = 'Yolo version 5'

    def __init__(self):
        # 定义图像预处理操作
        self.transform = transforms.Compose([
            transforms.Resize((640, 640)),
            transforms.ToTensor(),
            transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225])
        ])
        # 其他初始化操作
        # self.model = torch.hub.load('ultralytics/yolov5', 'yolov5s', pretrained=True)
        self.model = torch.load('yolov5s.pt')
        self.device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
        model_path = 'yolov5s.pt'

        checkpoint = torch.load(model_path, map_location=self.device)
        self.model = checkpoint['model']  # 提取模型部分（根据实际情况调整）
        self.model.to(self.device).eval()  # 确保模型在推理模式下
        self.transform = transforms.Compose([
            transforms.Resize((640, 640)),  # 根据模型的输入大小调整
            transforms.ToTensor(),
        ])
    def train(self, ep = 0):
        parser = argparse.ArgumentParser()
        parser.add_argument('--weights', type=str, default=config.weight, help='initial weights path')
        parser.add_argument('--cfg', type=str, default=config.config_model, help='models/yolov5s.yaml path')
        parser.add_argument('--data', type=str, default=config.config_data, help='data.yaml path')
        parser.add_argument('--hyp', type=str, default='data/hyp.scratch.yaml', help='hyperparameters path')
        parser.add_argument('--epochs', type=int, default=config.epochs)
        parser.add_argument('--batch-size', type=int, default=config.batch_size, help='total batch size for all GPUs')
        parser.add_argument('--img-size', nargs='+', type=int, default=[640, 640], help='[train, test] image sizes')
        parser.add_argument('--rect', action='store_true', help='rectangular training')
        parser.add_argument('--resume', nargs='?', const=True, default=False, help='resume most recent training')
        parser.add_argument('--nosave', action='store_true', help='only save final checkpoint')
        parser.add_argument('--notest', action='store_true', help='only test final epoch')
        parser.add_argument('--noautoanchor', action='store_true', help='disable autoanchor check')
        # parser.add_argument('--noautoanchor', type=bool, default=True, help='disable autoanchor check')
        parser.add_argument('--evolve', action='store_true', help='evolve hyperparameters')
        # parser.add_argument('--evolve', type = bool, default = False, help='evolve hyperparameters')
        parser.add_argument('--bucket', type=str, default='', help='gsutil bucket')
        parser.add_argument('--cache-images', action='store_true', help='cache images for faster training')
        parser.add_argument('--image-weights', action='store_true', help='use weighted image selection for training')
        parser.add_argument('--device', default=config.device, help='cuda device, i.e. 0 or 0,1,2,3 or cpu') # using GPU 0
        parser.add_argument('--multi-scale', action='store_true', help='vary img-size +/- 50%%')
        parser.add_argument('--single-cls', action='store_true', help='train multi-class data as single-class')
        # parser.add_argument('--adam', action='store_true', help='use torch.optim.Adam() optimizer')
        parser.add_argument('--adam', type=int, default=config.adam, help='use torch.optim.Adam() optimizer') # using Adam optimizer
        parser.add_argument('--sync-bn', action='store_true', help='use SyncBatchNorm, only available in DDP mode')
        parser.add_argument('--local_rank', type=int, default=-1, help='DDP parameter, do not modify')
        parser.add_argument('--log-imgs', type=int, default=16, help='number of images for W&B logging, max 100')
        parser.add_argument('--log-artifacts', action='store_true', help='log artifacts, i.e. final trained model')
        parser.add_argument('--workers', type=int, default=8, help='maximum number of dataloader workers')
        parser.add_argument('--project', default=config.project_train, help='save to project/name')
        parser.add_argument('--name', default=config.name, help='save to project/name')
        # parser.add_argument('--exist-ok', action='store_true', help='existing project/name ok, do not increment')
        parser.add_argument('--exist-ok', type=int, default=config.exist_ok, help='existing project/name ok, do not increment')
        opt = parser.parse_args()

        # Set DDP variables
        opt.total_batch_size = opt.batch_size
        opt.world_size = int(os.environ['WORLD_SIZE']) if 'WORLD_SIZE' in os.environ else 1
        opt.global_rank = int(os.environ['RANK']) if 'RANK' in os.environ else -1
        set_logging(opt.global_rank)
        if opt.global_rank in [-1, 0]:
            check_git_status()

        # Resume
        if opt.resume:  # resume an interrupted run
            ckpt = opt.resume if isinstance(opt.resume, str) else get_latest_run()  # specified or most recent path
            assert os.path.isfile(ckpt), 'ERROR: --resume checkpoint does not exist'
            with open(Path(ckpt).parent.parent / 'opt.yaml') as f:
                opt = argparse.Namespace(**yaml.load(f, Loader=yaml.FullLoader))  # replace
            opt.cfg, opt.weights, opt.resume = '', ckpt, True
            logger.info('Resuming training from %s' % ckpt)
        else:
            # opt.hyp = opt.hyp or ('hyp.finetune.yaml' if opt.weights else 'hyp.scratch.yaml')
            opt.data, opt.cfg, opt.hyp = check_file(opt.data), check_file(opt.cfg), check_file(opt.hyp)  # check files
            assert len(opt.cfg) or len(opt.weights), 'either --cfg or --weights must be specified'
            opt.img_size.extend([opt.img_size[-1]] * (2 - len(opt.img_size)))  # extend to 2 sizes (train, test)
            opt.name = 'evolve' if opt.evolve else opt.name
            opt.save_dir = increment_path(Path(opt.project) / opt.name, exist_ok=opt.exist_ok | opt.evolve)  # increment run

        # DDP mode
        device = select_device(opt.device, batch_size=opt.batch_size)
        if opt.local_rank != -1:
            assert torch.cuda.device_count() > opt.local_rank
            torch.cuda.set_device(opt.local_rank)
            device = torch.device('cuda', opt.local_rank)
            dist.init_process_group(backend='nccl', init_method='env://')  # distributed backend
            assert opt.batch_size % opt.world_size == 0, '--batch-size must be multiple of CUDA device count'
            opt.batch_size = opt.total_batch_size // opt.world_size

        # Hyperparameters
        with open(opt.hyp) as f:
            hyp = yaml.load(f, Loader=yaml.FullLoader)  # load hyps
            if 'box' not in hyp:
                warn('Compatibility: %s missing "box" which was renamed from "giou" in %s' %
                    (opt.hyp, 'https://github.com/ultralytics/yolov5/pull/1120'))
                hyp['box'] = hyp.pop('giou')

        # Train
        logger.info(opt)
        if not opt.evolve:
            tb_writer = None  # init loggers
            if opt.global_rank in [-1, 0]:
                logger.info(f'Start Tensorboard with "tensorboard --logdir {opt.project}", view at http://localhost:6006/')
                tb_writer = SummaryWriter(opt.save_dir)  # Tensorboard
            train(hyp, opt, device, tb_writer, wandb, ep)

    def extract_features(self, image_path):
        # 加载图像并进行预处理
        image = Image.open(image_path).convert('RGB')
        image_tensor = self.transform(image).unsqueeze(0) # 增加batch维度
        image_tensor = image_tensor.to(self.device)

        # 提取特征
        if next(self.model.parameters()).dtype == torch.float16:
            image_tensor = image_tensor.half()

        with torch.no_grad():
            results = self.model(image_tensor)  # 获取模型输出
        result_tensor = results[0]  # 获取 tuple 中的第一个 Tensor
            # 处理输出
        feature_vector = result_tensor.flatten().cpu().numpy()
        features_matrix = np.array(feature_vector)
        return features_matrix
    def detect(self):
        parser = argparse.ArgumentParser()
        parser.add_argument('--weights', nargs='+', type=str, default=config.weight, help='model.pt path(s)')
        parser.add_argument('--source', type=str, default=config.source, help='source')  # file/folder, 0 for webcam
        parser.add_argument('--img-size', type=int, default=640, help='inference size (pixels)')
        parser.add_argument('--conf-thres', type=float, default=config.conf_thres, help='object confidence threshold')
        parser.add_argument('--iou-thres', type=float, default=config.iou_thres, help='IOU threshold for NMS')
        parser.add_argument('--device', default=config.device, help='cuda device, i.e. 0 or 0,1,2,3 or cpu')
        parser.add_argument('--save-conf', type=int, default=config.save_conf, help='save confidences in --save-txt labels')
        parser.add_argument('--classes', nargs='+', type=int, help='filter by class: --class 0, or --class 0 2 3')
        parser.add_argument('--augment', action='store_true', help='augmented inference')
        parser.add_argument('--agnostic-nms', action='store_true', help='class-agnostic NMS')
        opt = parser.parse_args()

        with torch.no_grad():
            result = AL_detect(opt)
        return result


if __name__ == '__main__':
    model = Yolov5()
    model.detect()
