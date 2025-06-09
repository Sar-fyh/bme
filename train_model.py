import os

import AL_config2 as config
from AL_yolov51 import Yolov5
from shutil import copyfile

class ModelTrainer:
    def __init__(self, model):
        self.model = model
        self.ep = 1

    def run(self):
        while True:
            print(f"开始训练模型，第 {self.ep} 轮训练...")
            self.model.train(self.ep)
            if os.path.exists(config.weight):
                os.remove(config.weight)
            copyfile(os.path.join(config.project_train, config.name, 'weights', 'best.pt'), config.weight)
            self.ep += config.epochs
            # 这里可以添加停止训练的条件，例如根据训练轮数或性能指标

if __name__ == '__main__':
    trainer = ModelTrainer(model=Yolov5())
    trainer.run()