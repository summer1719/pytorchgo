# Author: Tao Hu <taohu620@gmail.com>

import torch.nn as nn
import torch.utils.model_zoo as model_zoo
import math
from pytorchgo.utils import logger
from pytorchgo.utils.pytorch_utils import model_summary

__all__ = [
    'VGG', 'vgg11', 'vgg11_bn', 'vgg13', 'vgg13_bn', 'vgg16', 'vgg16_bn',
    'vgg19_bn', 'vgg19',
]


model_urls = {
    'vgg11': 'https://download.pytorch.org/models/vgg11-bbd30ac9.pth',
    'vgg13': 'https://download.pytorch.org/models/vgg13-c768596a.pth',
    'vgg16': 'http://download.pytorch.org/models/vgg16-397923af.pth',# https cannot connect in China, so I choose to use http protocal
    'vgg19': 'https://download.pytorch.org/models/vgg19-dcbb9e9d.pth',
    'vgg11_bn': 'https://download.pytorch.org/models/vgg11_bn-6002323d.pth',
    'vgg13_bn': 'https://download.pytorch.org/models/vgg13_bn-abd245e5.pth',
    'vgg16_bn': 'https://download.pytorch.org/models/vgg16_bn-6c64b313.pth',
    'vgg19_bn': 'https://download.pytorch.org/models/vgg19_bn-c79401a0.pth',
}


class VGG(nn.Module):

    def __init__(self, features, num_classes=1000, init_weights=True):
        super(VGG, self).__init__()
        self.features = features
        self.classifier = nn.Sequential(
            nn.Linear(512 * 7 * 7, 4096),
            nn.ReLU(True),
            nn.Dropout(),
            nn.Linear(4096, 4096),
            nn.ReLU(True),
            nn.Dropout(),
            nn.Linear(4096, num_classes),
        )
        if init_weights:
            self._initialize_weights()

    def forward(self, x):
        x = self.features(x)
        x = x.view(x.size(0), -1)
        x = self.classifier(x)
        return x

    def _initialize_weights(self):
        for m in self.modules():
            if isinstance(m, nn.Conv2d):
                n = m.kernel_size[0] * m.kernel_size[1] * m.out_channels
                m.weight.data.normal_(0, math.sqrt(2. / n))
                if m.bias is not None:
                    m.bias.data.zero_()
            elif isinstance(m, nn.BatchNorm2d):
                m.weight.data.fill_(1)
                m.bias.data.zero_()
            elif isinstance(m, nn.Linear):
                m.weight.data.normal_(0, 0.01)
                m.bias.data.zero_()


def make_layers(cfg, batch_norm=False):
    layers = []
    in_channels = 3
    for v in cfg:
        if v == 'M':
            layers += [nn.MaxPool2d(kernel_size=2, stride=2)]
        else:
            conv2d = nn.Conv2d(in_channels, v, kernel_size=3, padding=1)
            if batch_norm:
                layers += [conv2d, nn.BatchNorm2d(v), nn.ReLU(inplace=True)]
            else:
                layers += [conv2d, nn.ReLU(inplace=True)]
            in_channels = v
    return nn.Sequential(*layers)


cfg = {
    'A': [64, 'M', 128, 'M', 256, 256, 'M', 512, 512, 'M', 512, 512, 'M'],
    'B': [64, 64, 'M', 128, 128, 'M', 256, 256, 'M', 512, 512, 'M', 512, 512, 'M'],
    'D': [64, 64, 'M', 128, 128, 'M', 256, 256, 256, 'M', 512, 512, 512, 'M', 512, 512, 512, 'M'],
    'E': [64, 64, 'M', 128, 128, 'M', 256, 256, 256, 256, 'M', 512, 512, 512, 512, 'M', 512, 512, 512, 512, 'M'],
}



def vgg11(pretrained=False, **kwargs):
    """VGG 11-layer model (configuration "A")

    Args:
        pretrained (bool): If True, returns a model pre-trained on ImageNet
    """
    if pretrained:
        kwargs['init_weights'] = False
    model = VGG(make_layers(cfg['A']), **kwargs)
    if pretrained:
        model.load_state_dict(model_zoo.load_url(model_urls['vgg11']))
    return model


def vgg11_bn(pretrained=False, **kwargs):
    """VGG 11-layer model (configuration "A") with batch normalization

    Args:
        pretrained (bool): If True, returns a model pre-trained on ImageNet
    """
    if pretrained:
        kwargs['init_weights'] = False
    model = VGG(make_layers(cfg['A'], batch_norm=True), **kwargs)
    if pretrained:
        model.load_state_dict(model_zoo.load_url(model_urls['vgg11_bn']))
    return model


def vgg13(pretrained=False, **kwargs):
    """VGG 13-layer model (configuration "B")

    Args:
        pretrained (bool): If True, returns a model pre-trained on ImageNet
    """
    if pretrained:
        kwargs['init_weights'] = False
    model = VGG(make_layers(cfg['B']), **kwargs)
    if pretrained:
        model.load_state_dict(model_zoo.load_url(model_urls['vgg13']))
    return model


def vgg13_bn(pretrained=False, **kwargs):
    """VGG 13-layer model (configuration "B") with batch normalization

    Args:
        pretrained (bool): If True, returns a model pre-trained on ImageNet
    """
    if pretrained:
        kwargs['init_weights'] = False
    model = VGG(make_layers(cfg['B'], batch_norm=True), **kwargs)
    if pretrained:
        model.load_state_dict(model_zoo.load_url(model_urls['vgg13_bn']))
    return model


def vgg16(pretrained=False, **kwargs):
    """VGG 16-layer model (configuration "D")

    Args:
        pretrained (bool): If True, returns a model pre-trained on ImageNet
    """
    if pretrained:
        kwargs['init_weights'] = False
    model = VGG(make_layers(cfg['D']), **kwargs)
    if pretrained:
        model.load_state_dict(model_zoo.load_url(model_urls['vgg16']))
    return model


def vgg16_bn(pretrained=False, **kwargs):
    """VGG 16-layer model (configuration "D") with batch normalization

    Args:
        pretrained (bool): If True, returns a model pre-trained on ImageNet
    """
    if pretrained:
        kwargs['init_weights'] = False
    model = VGG(make_layers(cfg['D'], batch_norm=True), **kwargs)
    if pretrained:
        model.load_state_dict(model_zoo.load_url(model_urls['vgg16_bn']))
    return model


def vgg19(pretrained=False, **kwargs):
    """VGG 19-layer model (configuration "E")

    Args:
        pretrained (bool): If True, returns a model pre-trained on ImageNet
    """
    if pretrained:
        kwargs['init_weights'] = False
    model = VGG(make_layers(cfg['E']), **kwargs)
    if pretrained:
        model.load_state_dict(model_zoo.load_url(model_urls['vgg19']))
    return model


def vgg19_bn(pretrained=False, **kwargs):
    """VGG 19-layer model (configuration 'E') with batch normalization

    Args:
        pretrained (bool): If True, returns a model pre-trained on ImageNet
    """
    if pretrained:
        kwargs['init_weights'] = False
    model = VGG(make_layers(cfg['E'], batch_norm=True), **kwargs)
    if pretrained:
        model.load_state_dict(model_zoo.load_url(model_urls['vgg19_bn']))
    return model

class FCN(nn.Module):

    def __init__(self, features, init_weights=True):
        super(FCN, self).__init__()
        self.features = features
        if init_weights:
            self._initialize_weights()


    def forward(self, x):
        x = self.features(x)
        return x

    def _initialize_weights(self):
        for m in self.modules():
            if isinstance(m, nn.Conv2d):
                n = m.kernel_size[0] * m.kernel_size[1] * m.out_channels
                m.weight.data.normal_(0, math.sqrt(2. / n))
                if m.bias is not None:
                    m.bias.data.zero_()
            elif isinstance(m, nn.BatchNorm2d):
                m.weight.data.fill_(1)
                m.bias.data.zero_()
            elif isinstance(m, nn.Linear):
                m.weight.data.normal_(0, 0.01)
                m.bias.data.zero_()


def VGG16_LargeFoV(class_num, image_size, pretrained=False,  **kwargs):
    #https://github.com/DrSleep/tensorflow-deeplab-lfov/blob/master/deeplab_lfov/model.py

    if pretrained:
        kwargs['init_weights'] = False

    # All convolutional and pooling operations are applied using kernels of size 3x3;
    # padding is added so that the output of the same size as the input.

    layers = []
    #'D': [64, 64, 'M', 128, 128, 'M', 256, 256, 256, 'M', 512, 512, 512, 'M', 512, 512, 512, 'M'],
    layers += [nn.Conv2d(3, 64, kernel_size=3, padding=1), nn.ReLU(inplace=True)]
    layers += [nn.Conv2d(64, 64, kernel_size=3, padding=1), nn.ReLU(inplace=True)]
    layers += [nn.MaxPool2d(kernel_size=2, stride=2)]
    layers += [nn.Conv2d(64, 128, kernel_size=3, padding=1), nn.ReLU(inplace=True)]
    layers += [nn.Conv2d(128, 128, kernel_size=3, padding=1), nn.ReLU(inplace=True)]
    layers += [nn.MaxPool2d(kernel_size=2, stride=2)]
    layers += [nn.Conv2d(128, 256, kernel_size=3, padding=1), nn.ReLU(inplace=True)]
    layers += [nn.Conv2d(256, 256, kernel_size=3, padding=1), nn.ReLU(inplace=True)]
    layers += [nn.Conv2d(256, 256, kernel_size=3, padding=1), nn.ReLU(inplace=True)]
    layers += [nn.MaxPool2d(kernel_size=2, stride=2)]
    layers += [nn.Conv2d(256, 512, kernel_size=3, padding=1), nn.ReLU(inplace=True)]
    layers += [nn.Conv2d(512, 512, kernel_size=3, padding=1), nn.ReLU(inplace=True)]
    layers += [nn.Conv2d(512, 512, kernel_size=3, padding=1), nn.ReLU(inplace=True)]
    layers += [nn.MaxPool2d(kernel_size=2, stride=1)]
    layers += [nn.Conv2d(512, 512, kernel_size=3, dilation=2, padding=1), nn.ReLU(inplace=True)]
    layers += [nn.Conv2d(512, 512, kernel_size=3, dilation=2, padding=1), nn.ReLU(inplace=True)]
    layers += [nn.Conv2d(512, 512, kernel_size=3, dilation=2, padding=1), nn.ReLU(inplace=True)]
    layers += [nn.MaxPool2d(kernel_size=2, stride=1)]
    layers += [nn.Conv2d(512, 1024, kernel_size=3,dilation=12,padding=1), nn.ReLU(inplace=True), nn.Dropout2d()]#todo dropout

    layers += [nn.Conv2d(1024, 1024, kernel_size=3, dilation=1, padding=1), nn.ReLU(inplace=True), nn.Dropout2d()]  # todo dropout

    layers += [nn.Conv2d(1024, class_num, kernel_size=3, dilation=1, padding=1)]

    layers += [nn.Upsample(size=image_size, mode='bilinear')]

    vgg_input = nn.Sequential(*layers)

    model = FCN(vgg_input, **kwargs)

    if pretrained:
        saved_state_dict = model_zoo.load_url(model_urls['vgg16'])
        logger.info("dictionary weight: {}".format(saved_state_dict.keys()))
        new_params = model.state_dict().copy()
        for weight_key in saved_state_dict:
            # classifier.0.bias
            i_parts = weight_key.split('.')
            if i_parts[0] == 'classifier':
                continue
            elif i_parts[0] == 'features':
                new_params[weight_key] = saved_state_dict[weight_key]
                logger.info("loading weight from pretrained dictionary: {}".format(weight_key))
            else:
                raise
            # print i_parts
        model.load_state_dict(new_params)

    logger.info("deeplabv1 model structure: {}".format(model))
    model_summary(model)
    return model

# The DeepLab-LargeFOV model can be represented as follows:
## input -> [conv-relu](dilation=1, channels=64) x 2 -> [max_pool](stride=2)
##       -> [conv-relu](dilation=1, channels=128) x 2 -> [max_pool](stride=2)
##       -> [conv-relu](dilation=1, channels=256) x 3 -> [max_pool](stride=2)
##       -> [conv-relu](dilation=1, channels=512) x 3 -> [max_pool](stride=1)
##       -> [conv-relu](dilation=2, channels=512) x 3 -> [max_pool](stride=1) -> [avg_pool](stride=1)
##       -> [conv-relu](dilation=12, channels=1024) -> [dropout]
##       -> [conv-relu](dilation=1, channels=1024) -> [dropout]
##       -> [conv-relu](dilation=1, channels=21) -> [pixel-wise softmax loss].