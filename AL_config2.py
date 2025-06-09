# Config for active learning

max_queried = 2
unlabeled = 'C://system//system//1//data//new//unlabeled'
labeled = 'C://system//system//1//data//new//train'
num_select = 20
num_select1 = 15
num_select2 = 10

# Config general
project = "C://system//system//1"
weight = 'yolov5s.pt'
device = '0' # cpu or 0,1,...
name = 'gun'
exist_ok = 1


# Config for train model
config_model = 'models/yolo_gun.yaml'
config_data = 'data/gun.yaml'
batch_size = 1
epochs = 1
adam = 0
project_train = 'runs/train'

# Config for detection
source = 'C://system//system//1//data//new//unlabeled' # '0' for webcam
conf_thres = 0.25
iou_thres = 0.45
project_detect = 'runs/detect'
save_conf = 0