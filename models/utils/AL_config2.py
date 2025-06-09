# Config for active learning
max_queried = 102
unlabeled = 'data/new/unlabeled'
labeled = 'data/new/train'
num_select = 100
num_select1 = 80
num_select2 = 60

# Config general
project = "/media/thang/New Volume/Active-learning-for-object-detection/"
weight = 'yolov5s.pt'
device = '0' # cpu or 0,1,...
name = 'gun'
exist_ok = 1


# Config for train model
config_model = 'models/yolo_gun.yaml'
config_data = 'data/gun.yaml'
batch_size = 4
epochs = 26
adam = 0
project_train = 'runs/train'

# Config for detection
source = 'data/new/unlabeled' # '0' for webcam
conf_thres = 0.25
iou_thres = 0.45
project_detect = 'runs/detect'
save_conf = 0