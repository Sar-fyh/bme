from sklearn.neighbors import kneighbors_graph
from sklearn.metrics import pairwise_distances
import numpy as np
import shutil
import os
import math
import AL_config2 as config
from AL_yolov51 import Yolov5
from sampling_def import SamplingMethod
from tqdm import tqdm
import warnings
from scipy.sparse import SparseEfficiencyWarning
from sklearn.cluster import MiniBatchKMeans


# 忽略 SparseEfficiencyWarning
warnings.filterwarnings('ignore', category=SparseEfficiencyWarning)

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
        self.selected_results = selected_results
        self.n_clusters = len(list(set(y)))
        self.cluster_model = MiniBatchKMeans(n_clusters=self.n_clusters)
        self.cluster_data()
        self.seed = seed
        np.random.seed(self.seed)

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
            for i, (image_path, predictions) in tqdm(enumerate(self.selected_results.items()),
                                                      total=len(self.selected_results),
                                                      desc="Processing images"):
                if i not in already_selected:
                    avg_conf = np.mean([pred['conf'] for pred in predictions])
                    confidences.append((i, avg_conf))
            rank_ind = [x[0] for x in sorted(confidences, key=lambda x: x[1])]
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
            batch_filler = [i for i in batch_filler if i < len(self.cluster_labels)]
            new_batch.extend(batch_filler[0:n_slot_remaining])
            return new_batch
        except Exception as e:
            print(f"Error: {str(e)}")
            return []

    def to_dict(self):
        output = {}
        output['cluster_membership'] = self.cluster_labels
        return output

class ImageExtractor:
    def __init__(self, model, txt_file_path):
        self.model = model
        self.num_select = config.num_select
        self.txt_file_path = txt_file_path
        self.num_select1 = config.num_select1
        self.num_select2 = config.num_select2

    def extract_features_from_txt(self):
        image_paths = read_image_paths_from_txt(self.txt_file_path)
        unlabeled_features = np.array([self.model.extract_features(img) for img in image_paths])
        return unlabeled_features

    def run(self):
        print(f"读取到的 max_queried 为 {config.max_queried}")
        queried = 0
        while queried < config.max_queried:
            print("第 {} 次查询".format(queried+1))
            result = self.model.detect()
            print("特征提取完成")

            new_folder_path = r'C://system//system//1//data//new//AL_serve'
            if not os.path.exists(new_folder_path):
                os.makedirs(new_folder_path)

            if len(result) >= self.num_select2:
                image_paths = list(result.keys())

                print("开始不确定性采样...")
                U_best = UncertaintySamplingEntropy(self.num_select2, {img: result[img] for img in image_paths})
                selected_results = {img: result[img] for img in U_best}
                selected_features = np.array([self.model.extract_features(img) for img in U_best])
                print(f"不确定性采样完成，选择了 {len(U_best)} 张图像。")

                for image_path in U_best:
                    shutil.copy(image_path, os.path.join(new_folder_path, os.path.basename(image_path)))

                folder_path_t = r'C://system//system//1//data//new//train'
                for image_path in U_best:
                    shutil.copy(image_path, os.path.join(folder_path_t, os.path.basename(image_path)))

                txt_folder_path = r'C://system//system//1//data//new//txt_all'
                txt_new_folder_path = r'C://system//system//1//data//new//train'
                if not os.path.exists(txt_new_folder_path):
                    os.makedirs(txt_new_folder_path)

                for image_path in U_best:
                    base_name = os.path.basename(image_path)
                    txt_file_name = os.path.splitext(base_name)[0] + '.txt'
                    txt_source_path = os.path.join(txt_folder_path, txt_file_name)
                    txt_target_path = os.path.join(txt_new_folder_path, txt_file_name)
                    if os.path.exists(txt_source_path):
                        shutil.copy(txt_source_path, txt_target_path)
                    else:
                        print(f"Warning: {txt_file_name} does not exist in the source folder.")

                with open(r'C://system//system//1//data//new//train.txt', "a") as f:
                    for file_name in U_best:
                        file_name = file_name.replace("\\", "/")
                        f.write(file_name.replace("unlabeled", "train") + '\n')

                for image_path in U_best:
                    if os.path.exists(image_path):
                        os.remove(image_path)

                remaining_files = [
                    os.path.join(root, file)
                    for root, _, files in os.walk(
                        r'C://system//system//1//data//new//unlabeled')
                    for file in files if file.endswith(('.jpg', '.png'))
                ]
                with open(self.txt_file_path, 'w') as txt_file:
                    for file in remaining_files:
                        txt_file.write(file + '\n')

                queried += 1
            else:
                print("未标记文件数量不足 {} 个".format(self.num_select))
                break

if __name__ == '__main__':
    txt_file_path = r'C://system//system//1//data//new//unlabeledpc.txt'
    extractor = ImageExtractor(model=Yolov5(), txt_file_path=txt_file_path)
    extractor.run()