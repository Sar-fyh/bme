
from sklearn.neighbors import kneighbors_graph
from sklearn.metrics import pairwise_distances
import numpy as np
import time
import shutil
import sys
import os
import math
import AL_config2 as config
from AL_yolov51 import Yolov5
import matplotlib.pyplot as plt
sys.path.append(r'C://system//system//1//models')
from matplotlib import rcParams
from shutil import copyfile
from sklearn.cluster import MiniBatchKMeans
from sampling_def import SamplingMethod
from tqdm import tqdm
import cv2
rcParams['font.sans-serif'] = ['Arial']
rcParams['font.family'] = 'sans-serif'
#import albumentations as A
import warnings
from scipy.sparse import SparseEfficiencyWarning
from sklearn.neighbors import kneighbors_graph
from scipy.spatial.distance import cdist
import numpy as np
from scipy.sparse import lil_matrix
import heapq
# 忽略 SparseEfficiencyWarning
warnings.filterwarnings('ignore', category=SparseEfficiencyWarning)
from tqdm import tqdm  # 导入 tqdm 用于进度条
import numpy as np
from sklearn.neighbors import kneighbors_graph
from scipy.spatial.distance import cdist
from scipy.sparse import lil_matrix


from sklearn.neighbors import kneighbors_graph
import heapq
import numpy as np

class GraphDensitySampler:
    def __init__(self, X):
        self.X = X
        self.flat_X = self.flatten_X()
        self.gamma = 1. / self.X.shape[1]
        self.compute_graph_density()

    def flatten_X(self):
        return self.X.reshape(self.X.shape[0], -1)

    def compute_graph_density(self, n_neighbor=10):

        connect = kneighbors_graph(self.flat_X, n_neighbor, p=1)
        neighbors = connect.nonzero()
        inds = zip(neighbors[0], neighbors[1])

        for entry in inds:
            i, j = entry
            distance = pairwise_distances(self.flat_X[[i]], self.flat_X[[j]], metric='manhattan')
            weight = np.exp(-distance[0, 0] * self.gamma)
            connect[i, j] = weight
            connect[j, i] = weight
        self.connect = connect
        self.graph_density = np.zeros(self.X.shape[0])
        for i in range(self.X.shape[0]):
            self.graph_density[i] = connect[i, :].sum() / (connect[i, :] > 0).sum()

    def select_by_density(self, num_select):
        return np.argsort(-self.graph_density)[:num_select]
def calculate_entropy(predictions):
    entropy = 0
    for cls_conf in predictions:
        prob = cls_conf['conf']
        if prob > 0:
            entropy -= prob * math.log(prob)
    return entropy


def UncertaintySamplingEntropy(num_select, result):
    entropy_dict = {}
    for image_path, predictions in result.items():
        entropy_dict[image_path] = calculate_entropy(predictions)
    return sorted(entropy_dict, key=entropy_dict.get, reverse=True)[:num_select]


def read_image_paths_from_txt(txt_file_path):
    with open(txt_file_path, 'r') as file:
        image_paths = [line.strip() for line in file.readlines()]
    return image_paths

class InformativeClusterDiverseSampler(SamplingMethod):
    def __init__(self, X, y, seed, selected_results):
        self.name = 'informative_and_diverse'
        self.X = X
        self.flat_X = self.flatten_X()
        self.y = y
        self.selected_results = selected_results  # 将 selected_results 存储为实例属性
        self.n_clusters = len(list(set(y)))
        self.cluster_model = MiniBatchKMeans(n_clusters=self.n_clusters)
        self.cluster_data()
        self.seed = seed  # 确保 seed 只传递一次
        np.random.seed(self.seed)  # 设置随机种子，确保可复现

    def flatten_X(self):
        return self.X.reshape(self.X.shape[0], -1)

    def cluster_data(self):
        self.cluster_model.fit(self.flat_X)
        unique, counts = np.unique(self.cluster_model.labels_, return_counts=True)
        self.cluster_prob = counts / sum(counts)
        self.cluster_labels = self.cluster_model.labels_

    def select_batch_(self, model, already_selected, N, **kwargs):
        try:
            confidences = []
            # 使用 tqdm 显示进度条，遍历 selected_results
            for i, (image_path, predictions) in tqdm(enumerate(self.selected_results.items()),
                                                      total=len(self.selected_results),
                                                      desc="Processing images"):
                if i not in already_selected:
                    # 计算图像的平均置信度
                    avg_conf = np.mean([pred['conf'] for pred in predictions])
                    confidences.append((i, avg_conf))
                    img_size = "640x640"
                    num_objects = len(predictions)  # 假设每个预测结果代表一个检测到的对象
                    # 通过 tqdm 打印图像的路径、尺寸，以及检测到的对象数量
                    #print(f"image {i+1}/{len(self.selected_results)} {image_path}: 640x640 {len(predictions)}")
            # 按置信度升序排序（低置信度优先）
            rank_ind = [x[0] for x in sorted(confidences, key=lambda x: x[1])]

        except Exception as e:
            print(f"Error: {str(e)}")
            return []

        # 确保索引在合法范围内
        rank_ind = [i for i in rank_ind if i < len(self.cluster_labels)]

        new_batch_cluster_counts = [0 for _ in range(self.n_clusters)]
        new_batch = []
        for i in rank_ind:
            if len(new_batch) == N:
                break
            label = self.cluster_labels[i]
            if new_batch_cluster_counts[label] / N < self.cluster_prob[label]:
                new_batch.append(i)
                new_batch_cluster_counts[label] += 1

        n_slot_remaining = N - len(new_batch)
        batch_filler = list(set(rank_ind) - set(already_selected) - set(new_batch))
        batch_filler = [i for i in batch_filler if i < len(self.cluster_labels)]  # 再次确保合法索引
        new_batch.extend(batch_filler[0:n_slot_remaining])
        return new_batch


    def to_dict(self):
        output = {}
        output['cluster_membership'] = self.cluster_labels
        return output



class ActiveLearning:
    def __init__(self, model, txt_file_path):
        self.model = model
        self.num_select = config.num_select
        self.txt_file_path = txt_file_path
        self.num_select1 = config.num_select1
        self.num_select2 = config.num_select2

    def extract_features_from_txt(self):
        image_paths = read_image_paths_from_txt(self.txt_file_path)
        unlabeled_features = np.array([self.model.extract_features(img) for img in image_paths])
        #print(unlabeled_features)
        return unlabeled_features


    def run(self):
        queried = 1
        ep = 1
        while queried < config.max_queried:
            print("第 {} 次查询".format(queried))
            result = self.model.detect()
            print("特征提取完成")


            new_folder_path = r'C://system//system//1//data//new//AL_serve'
            if not os.path.exists(new_folder_path):
                os.makedirs(new_folder_path)

            if len(result) >= self.num_select2:
                image_paths = list(result.keys())  # 获取所有图像路径

                # 使用不确定性采样策略
                print("开始不确定性采样...")
                U_best = UncertaintySamplingEntropy(self.num_select2, {img: result[img] for img in image_paths})
                # 从 result 中提取出 U_best 中包含的图像路径对应的检测数据
                selected_results = {img: result[img] for img in U_best}  # 提取出U_best中图像路径的检测数据
                selected_features = np.array([self.model.extract_features(img) for img in U_best])
                print(f"不确定性采样完成，选择了 {len(U_best)} 张图像。")




                # 复制选择的图像文件
                for image_path in U_best:
                    shutil.copy(image_path, os.path.join(new_folder_path, os.path.basename(image_path)))

                for image_path in U_best:
                    shutil.copy(image_path, os.path.join(folder_path_t, os.path.basename(image_path)))
                if not os.path.exists(txt_new_folder_path):
                    os.makedirs(txt_new_folder_path)


                # 将对应的txt文件复制到目标文件夹
                for image_path in U_best:
                    # 获取图像文件的基本文件名（不带扩展名）
                    base_name = os.path.basename(image_path)
                    txt_file_name = os.path.splitext(base_name)[0] + '.txt'  # 假设txt文件与图像文件同名，扩展名为 .txt

                    # 构建txt文件的源路径和目标路径
                    txt_source_path = os.path.join(txt_folder_path, txt_file_name)
                    txt_target_path = os.path.join(txt_new_folder_path, txt_file_name)

                    # 检查源文件是否存在，再进行复制
                    if os.path.exists(txt_source_path):
                        shutil.copy(txt_source_path, txt_target_path)
                    else:
                        print(f"Warning: {txt_file_name} does not exist in the source folder.")


                # 更新 train.txt 文件
                with open(r'C://system//system//1//data//new//train.txt', "a") as f:
                    for file_name in U_best:
                        # 替换路径中的反斜杠为正斜杠
                        file_name = file_name.replace("\\", "/")  # 这行确保反斜杠被替换为正斜杠，/
                        f.write(file_name.replace("unlabeled", "train") + '\n')

                for image_path in U_best:

                    # 删除原文件夹中的图像文件
                    if os.path.exists(image_path):
                        os.remove(image_path)

                # 更新 txt 文件路径内容
                #print("更新未标记数据列表...")
                remaining_files = [
                    os.path.join(root, file)
                    for root, _, files in os.walk(
                        r'C://system//system//1//data//new//unlabeled')
                    for file in files if file.endswith(('.jpg', '.png'))
                ]
                #print(f"找到的未标记文件: {remaining_files}")
                with open(self.txt_file_path, 'w') as txt_file:
                    for file in remaining_files:
                        txt_file.write(file + '\n')

                print(f"开始训练模型，第 {ep} 轮训练...")

                self.model.train(ep)
                if os.path.exists(config.weight):
                    os.remove(config.weight)

                copyfile(os.path.join(config.project_train, config.name, 'weights', 'best.pt'), config.weight)
                queried += 1
                ep += config.epochs

            else:
                print("未标记文件数量不足 {} 个".format(self.num_select))
                break

if __name__ == '__main__':
    txt_file_path = r'C://system//system//1//data//new//unlabeledpc.txt'
    folder_path_t = r'C://system//system//1//data//new//train'
    txt_folder_path = r'C://system//system//1//data//new//txt_all'  # 源txt文件夹路径
    txt_new_folder_path = r'C://system//system//1//data//new//train'  # 目标txt文件夹路径
    bot = ActiveLearning(model=Yolov5(), txt_file_path=txt_file_path)
    bot.run()


