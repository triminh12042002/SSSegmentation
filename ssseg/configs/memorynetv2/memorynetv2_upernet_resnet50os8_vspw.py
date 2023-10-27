'''memorynetv2_upernet_resnet50os8_vspw'''
import copy
from .base_cfg import SEGMENTOR_CFG
from .._base_ import DATASET_CFG_VSPW_512x512, DATALOADER_CFG_BS16


# deepcopy
SEGMENTOR_CFG = copy.deepcopy(SEGMENTOR_CFG)
# modify dataset config
SEGMENTOR_CFG['dataset'] = DATASET_CFG_VSPW_512x512.copy()
# modify dataloader config
SEGMENTOR_CFG['dataloader'] = DATALOADER_CFG_BS16.copy()
# modify scheduler config
SEGMENTOR_CFG['scheduler']['max_epochs'] = 240
SEGMENTOR_CFG['scheduler']['optimizer']['params_rules'] = {'backbone_net': dict(lr_multiplier=0.1, wd_multiplier=1.0)}
# modify other segmentor configs
SEGMENTOR_CFG['num_classes'] = 124
SEGMENTOR_CFG['backbone'] = {
    'type': 'ResNet', 'depth': 50, 'structure_type': 'resnet50conv3x3stem',
    'pretrained': True, 'outstride': 8, 'use_conv3x3_stem': True, 'selected_indices': (0, 1, 2, 3),
}
SEGMENTOR_CFG['head']['fpn'] = {
    'in_channels_list': [256, 512, 1024, 2048], 'feats_channels': 1024, 'out_channels': 512,
}
SEGMENTOR_CFG['head']['decoder'] = {
    'pr': {'in_channels': 512, 'out_channels': 512, 'dropout': 0.1},
    'cwi': {'in_channels': 512, 'out_channels': 512, 'dropout': 0.1},
    'cls': {'in_channels': 2560, 'out_channels': 512, 'dropout': 0.1, 'kernel_size': 3, 'padding': 1},
}
SEGMENTOR_CFG['head']['context_within_image']['is_on'] = True
SEGMENTOR_CFG['head']['context_within_image']['use_self_attention'] = False
SEGMENTOR_CFG['inference'] = {
    'mode': 'slide',
    'opts': {'cropsize': (512, 512), 'stride': (341, 341)}, 
    'tricks': {
        'multiscale': [1], 'flip': False, 'use_probs_before_resize': True
    }
}
SEGMENTOR_CFG['work_dir'] = 'memorynetv2_upernet_resnet50os8_vspw'
SEGMENTOR_CFG['logfilepath'] = 'memorynetv2_upernet_resnet50os8_vspw/memorynetv2_upernet_resnet50os8_vspw.log'
SEGMENTOR_CFG['resultsavepath'] = 'memorynetv2_upernet_resnet50os8_vspw/memorynetv2_upernet_resnet50os8_vspw_results.pkl'