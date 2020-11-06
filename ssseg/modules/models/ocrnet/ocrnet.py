'''
Function:
    define the ocrnet
Author:
    Zhenchao Jin
'''
import copy
import torch
import torch.nn as nn
import torch.nn.functional as F
from ...losses import *
from ...backbones import *
from .spatialocr import SpatialOCRModule
from .spatialgather import SpatialGatherModule


'''OCRNet'''
class OCRNet(nn.Module):
    def __init__(self, cfg, **kwargs):
        super(OCRNet, self).__init__()
        self.mode = kwargs.get('mode')
        assert self.mode in ['TRAIN', 'TEST']
        # parse align_corners, normalization layer and activation layer cfg
        align_corners = cfg.get('align_corners', True)
        normlayer_opts = cfg.get('normlayer_opts', {'type': 'syncbatchnorm2d', 'opts': {}})
        activation_opts = cfg.get('activation_opts', {'type': 'relu', 'opts': {'inplace': True}})
        if cfg['distributed']['is_on'] and 'syncbatchnorm' in normlayer_opts['type']: normlayer_opts.update({'type': 'distsyncbatchnorm'})
        self.align_corners = align_corners
        # build backbone
        backbone_cfg = copy.deepcopy(cfg['backbone'])
        backbone_cfg.update({'normlayer_opts': copy.deepcopy(normlayer_opts)})
        self.backbone_net = BuildBackbone(backbone_cfg)
        # build auxiliary decoder
        auxiliary_cfg = cfg['auxiliary']
        self.auxiliary_decoder = nn.Sequential(nn.Conv2d(auxiliary_cfg['in_channels'], auxiliary_cfg['out_channels'], kernel_size=3, stride=1, padding=1, bias=False),
                                               BuildNormalizationLayer(normlayer_opts['type'], (auxiliary_cfg['out_channels'], normlayer_opts['opts'])),
                                               BuildActivation(activation_opts['type'], **activation_opts['opts']),
                                               nn.Dropout2d(auxiliary_cfg['dropout']),
                                               nn.Conv2d(auxiliary_cfg['out_channels'], cfg['num_classes'], kernel_size=1, stride=1, padding=0))
        # build spatial gather module
        spatialgather_cfg = {
            'scale': cfg['spatialgather']['scale']
        }
        self.spatial_gather_net = SpatialGatherModule(**spatialgather_cfg)
        # build spatial ocr module
        spatialocr_cfg = {
            'in_channels': cfg['spatialocr']['in_channels'],
            'key_channels': cfg['spatialocr']['key_channels'],
            'out_channels': cfg['spatialocr']['out_channels'],
            'align_corners': align_corners,
            'normlayer_opts': normlayer_opts,
            'activation_opts': activation_opts,
        }
        self.spatial_ocr_net = SpatialOCRModule(**spatialocr_cfg)
        # build decoder
        decoder_cfg = cfg['decoder']
        self.decoder = nn.Sequential(nn.Dropout2d(decoder_cfg['dropout']),
                                     nn.Conv2d(decoder_cfg['in_channels'], cfg['num_classes'], kernel_size=1, stride=1, padding=0))
        # freeze normalization layer if necessary
        if cfg.get('is_freeze_normlayer', False): self.freezenormlayer()
    '''forward'''
    def forward(self, x, targets=None, losses_cfg=None):
        h, w = x.size(2), x.size(3)
        # feed to backbone network
        x1, x2, x3, x4 = self.backbone_net(x)
        # feed to auxiliary decoder
        preds_aux = self.auxiliary_decoder(x3)
        # feed to ocr module
        feats = F.interpolate(x4, size=preds_aux.size()[2:], mode='bilinear', align_corners=self.align_corners)
        context = self.spatial_gather_net(feats, preds_aux)
        features = self.spatial_ocr_net(feats, context)
        # feed to decoder
        preds = self.decoder(features)
        # return according to the mode
        if self.mode == 'TRAIN':
            preds = F.interpolate(preds, size=(h, w), mode='bilinear', align_corners=self.align_corners)
            preds_aux = F.interpolate(preds_aux, size=(h, w), mode='bilinear', align_corners=self.align_corners)
            loss_dict = self.calculateloss({'preds': preds, 'preds_aux': preds_aux}, targets, losses_cfg)
            return loss_dict
        return preds
    '''return all layers'''
    def alllayers(self):
        return {
                'backbone_net': self.backbone_net,
                'auxiliary_decoder': self.auxiliary_decoder,
                'spatial_gather_net': self.spatial_gather_net,
                'spatial_ocr_net': self.spatial_ocr_net,
                'decoder': self.decoder
            }
    '''freeze normalization layer'''
    def freezenormlayer(self):
        for module in self.modules():
            if type(module) in BuildNormalizationLayer(only_get_all_supported=True):
                module.eval()
    '''calculate losses'''
    @staticmethod
    def calculateloss(preds, targets, losses_cfg):
        supported_losses = {
            'celoss': CrossEntropyLoss,
            'sigmoidfocalloss': SigmoidFocalLoss,
        }
        targets_seg = targets['segmentation']
        # calculate the auxiliary loss
        aux_cfg = losses_cfg['auxiliary']
        loss_aux = 0
        preds_aux = preds['preds_aux'].permute((0, 2, 3, 1)).contiguous()
        for key, value in aux_cfg.items():
            assert key in supported_losses, 'unsupport auxiliary loss type %s...' % key
            loss_aux += supported_losses[key](preds=preds_aux.view(-1, preds_aux.size(3)),
                                              targets=targets_seg.view(-1),
                                              scale_factor=value['scale_factor'],
                                              **value['opts'])
        # calculate the classification loss
        cls_cfg = losses_cfg['classification']
        loss_cls = 0
        preds = preds['preds'].permute((0, 2, 3, 1)).contiguous()
        for key, value in cls_cfg.items():
            assert key in supported_losses, 'unsupport classification loss type %s...' % key
            loss_cls += supported_losses[key](preds=preds.view(-1, preds.size(3)), 
                                              targets=targets_seg.view(-1), 
                                              scale_factor=value['scale_factor'],
                                              **value['opts'])
        # return the losses
        loss_dict = {'loss_aux': loss_aux, 'loss_cls': loss_cls}
        return loss_dict