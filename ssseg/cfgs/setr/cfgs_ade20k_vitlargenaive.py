'''define the config file for ade20k and ViT-Large'''
from .base_cfg import *


# modify dataset config
DATASET_CFG = DATASET_CFG.copy()
DATASET_CFG['train'].update(
    {
        'type': 'ade20k',
        'rootdir': 'data/ADE20k',
    }
)
DATASET_CFG['test'].update(
    {
        'type': 'ade20k',
        'rootdir': 'data/ADE20k',
    }
)
# modify dataloader config
DATALOADER_CFG = DATALOADER_CFG.copy()
# modify optimizer config
OPTIMIZER_CFG = OPTIMIZER_CFG.copy()
OPTIMIZER_CFG.update(
    {
        'max_epochs': 130
    }
)
# modify losses config
LOSSES_CFG = LOSSES_CFG.copy()
# modify model config
MODEL_CFG = MODEL_CFG.copy()
MODEL_CFG.update(
    {
        'num_classes': 150,
        'decoder': {
            'in_channels': 1024,
            'out_channels': 256,
            'dropout': 0,
            'num_convs': 1,
            'scale_factor': 4,
        },
        'auxiliary': [
            {'in_channels': 1024, 'out_channels': 256, 'dropout': 0, 'num_convs': 2, 'scale_factor': 4},
            {'in_channels': 1024, 'out_channels': 256, 'dropout': 0, 'num_convs': 2, 'scale_factor': 4},
            {'in_channels': 1024, 'out_channels': 256, 'dropout': 0, 'num_convs': 2, 'scale_factor': 4},
        ],
    }
)
# modify inference config
INFERENCE_CFG = INFERENCE_CFG.copy()
# modify common config
COMMON_CFG = COMMON_CFG.copy()
COMMON_CFG['train'].update(
    {
        'backupdir': 'setrnaive_vitlarge_ade20k_train',
        'logfilepath': 'setrnaive_vitlarge_ade20k_train/train.log',
    }
)
COMMON_CFG['test'].update(
    {
        'backupdir': 'setrnaive_vitlarge_ade20k_test',
        'logfilepath': 'setrnaive_vitlarge_ade20k_test/test.log',
        'resultsavepath': 'setrnaive_vitlarge_ade20k_test/setrnaive_vitlarge_ade20k_results.pkl'
    }
)