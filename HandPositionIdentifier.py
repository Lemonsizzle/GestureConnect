import pickle
import pandas as pd
import numpy as np
import torch
import torch.nn as nn
import torch.nn.functional as F


class Net(nn.Module):
    def __init__(self):
        super(Net, self).__init__()
        self.fc1 = nn.Linear(20, 128)
        self.fc1 = nn.Linear(20, 128)
        self.fc2 = nn.Linear(128, 64)
        self.fc3 = nn.Linear(64, 4)

    def forward(self, x):
        x = F.relu(self.fc1(x))
        x = F.relu(self.fc2(x))
        x = self.fc3(x)
        return x


class HPI:
    def __init__(self):
        self.modelFile = "model.pkl"
        self.model = pickle.load(open(self.modelFile, 'rb'))
        self.columns = ['thumb_cmc_dist', 'thumb_mcp_dist',
                        'thumb_dip_dist', 'thumb_tip_dist',
                        'index_cmc_dist', 'index_mcp_dist',
                        'index_dip_dist', 'index_tip_dist',
                        'middle_dip_dist', 'middle_tip_dist',
                        'middle_cmc_dist', 'middle_mcp_dist',
                        'ring_cmc_dist', 'ring_mcp_dist',
                        'ring_dip_dist', 'ring_tip_dist',
                        'pinky_cmc_dist', 'pinky_mcp_dist',
                        'pinky_dip_dist', 'pinky_tip_dist']

    def identify(self, data):
        df = pd.DataFrame(np.array(data).reshape(1, -1), columns=self.columns)
        prediction = self.model.predict(df)
        probability = self.model.predict_proba(df)
        if probability.max() < 0.3:
            prediction = "N//A"
        return prediction


if __name__ == '__main__':
    HPI()
