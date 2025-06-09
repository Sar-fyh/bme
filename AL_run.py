"""
主动学习算法
要求：
    - 已标记样本集合 L
    - 未标记样本集合 U
    - 初始化模型 f0
    - 主动学习指标 v
算法：
1. 将 U 分成批次
2. 设定 f <- f0
3. 如果 U 不为空或未满足停止条件：
    - 使用模型 f 对所有 U 的批次计算得分
    - 选择 U 中得分最高的批次作为 U_best
    - 为 U_best 分配标签（人工）
    - 使用已标记样本集合 L 和 (U_best, Y_best) 训练模型 f
    - 更新 U = U - U_best
    - 更新 L = L + (U_best, y_best)
"""

from torch.cuda.memory import reset_accumulated_memory_stats
from AL_yolov51 import Yolov5
import AL_config2 as config
import glob
import os
from shutil import copyfile, move
import io
import copy
import random
import shutil
import os
os.environ['KMP_DUPLICATE_LIB_OK']='TRUE'
def RandomSelect(num_select, result):
    return random.sample(result.keys(), num_select)

def UncertaintySamplingBinary(num_select, result, typ):
    """
    result =
        {"<图片链接>":
            [
                {"class": cls.item(), "box": [x,y,w,h], "conf": conf.item(),
                ...
            ],
        ...
        }
    """
    probas = {}
    if typ == 'sum':
        for item, lst_dic in result.items():
            conf = 0
            for dic in lst_dic:
                conf += (1.0 - dic["conf"])
            probas[item] = conf
    elif typ == 'avg':
        for item, lst_dic in result.items():
            conf = 0
            for dic in lst_dic:
                conf += (1.0 - dic["conf"])
            probas[item] = conf/len(lst_dic)
    elif typ == 'max':
        for item, lst_dic in result.items():
            conf = 0
            for dic in lst_dic:
                conf = max(conf, 1.0 - dic["conf"])
            probas[item] = conf
    return sorted(probas, key=probas.get, reverse=True)[:num_select]


class ActiveLearning(object):
    def __init__(self, model):
        self.model = model
        self.num_select = config.num_select
        self.type = 'max' # 'avg' , 'max', 'sum'

    def run(self):
        # 查询次数
        queried = 33
        ep = 66
        # 如果未达到最大查询次数，则继续查询
        while queried < config.max_queried:
            print("第 {} 次查询".format(queried))
            # 预测未标记样本中的所有图片
            result = self.model.detect()

            # 创建新文件夹
            new_folder_path = 'C://system//system//1//data//new//AL_serve'
            if not os.path.exists(new_folder_path):
                os.makedirs(new_folder_path)

            # 选择得分最高的 k 张图片
            # 使用不确定性抽样
            if len(result) >= self.num_select:
                # U_best = RandomSelect(self.num_select, result)
                U_best = UncertaintySamplingBinary(self.num_select, result, self.type)  # 使用不确定性抽样
                print(U_best)

                # 将选定的文件复制到新文件夹中
                for image_path in U_best:
                    shutil.copy(image_path, os.path.join(new_folder_path, os.path.basename(image_path)))

                # 为选定的文件分配标签（人工）
                # 遍历所有选定的文件
                for f in U_best:
                    # 移动图片文件到标记文件夹
                    move(f, f.replace("unlabeled", "labeled"))
                    # 在标记文件夹中创建标签文件
                    type_file = f.split('.')[-1]
                    copyfile(f.replace("unlabeled", "gun").replace(type_file, 'txt'),
                             f.replace("unlabeled", "labeled").replace(type_file, 'txt'))

                # 将已标记文件添加到训练数据集
                with open('data/new/train.txt', "a") as f:
                    for file_name in U_best:
                        f.write(file_name.replace("unlabeled", "labeled") + '\n')

                # 训练模型
                self.model.train(ep)

                ####################### 加载 ########################
                # 删除旧的权重文件
                if os.path.exists(config.weight):
                    os.remove(config.weight)

                # 更新新的权重文件
                copyfile(os.path.join(config.project_train, config.name, 'weights', 'best.pt'), config.weight)

                queried += 1
                ep += config.epochs
            else:
                print("未标记文件数量不足 {} 个".format(self.num_select))
                break

if __name__ == '__main__':
    bot = ActiveLearning(model=Yolov5())
    bot.run()
