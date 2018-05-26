#!/usr/bin/env python
import torch
import argparse
import os
import os.path as osp
import numpy as np
from torch.autograd import Variable
import torchfcn
import tqdm
import json
from PIL import Image
from os.path import join
import cv2
from datetime import datetime
import copy

def fast_hist(a, b, n):
    k = (a >= 0) & (a < n)
    return np.bincount(n * a[k].astype(int) + b[k], minlength=n ** 2).reshape(n, n)

def per_class_iu(hist):
    return np.diag(hist) / (hist.sum(1) + hist.sum(0) - np.diag(hist))

def label_mapping(input, mapping):
    output = np.copy(input)
    for ind in range(len(mapping)):
        output[input == mapping[ind][0]] = mapping[ind][1]
    return np.array(output, dtype=np.int64)

def compute_mIoU(pred_imgs, gt_imgs, json_path):
    """
    Function to compute mean IoU
    Args:
    	pred_imgs: Predictions obtained using our Neural Networks
    	gt_imgs: Ground truth label maps
    	json_path: Path to cityscapes_info.json file
    Returns:
    	Mean IoU score
    """
    
    with open(json_path, 'r') as fp:
      info = json.load(fp)
    num_classes = np.int(info['classes'])
    print('Num classes', num_classes)
    name_classes = np.array(info['label'], dtype=np.str)
    hist = np.zeros((num_classes, num_classes))
    
    for ind in range(len(gt_imgs)):
        pred = pred_imgs[ind]
        label = gt_imgs[ind]
        if len(label.flatten()) != len(pred.flatten()):
            print('Skipping: len(gt) = {:d}, len(pred) = {:d}, {:s}, {:s}'.format(len(label.flatten()), len(pred.flatten()), gt_imgs[ind], pred_imgs[ind]))
            continue
        hist += fast_hist(label.flatten(), pred.flatten(), num_classes)
        if ind > 0 and ind % 10 == 0:
            print('{:d} / {:d}: {:0.2f}'.format(ind, len(gt_imgs), 100*np.nanmean(per_class_iu(hist))))
    
    mIoUs = per_class_iu(hist)
    for ind_class in range(num_classes):
        print('===>' + name_classes[ind_class] + ':\t' + str(round(mIoUs[ind_class] * 100, 2)))
    print('===> mIoU: ' + str(round(np.nanmean(mIoUs) * 100, 2)))
    return mIoUs

def transform_label(label_orig, sz):
    """
    Function to transform the predictions obtained to original size of cityscapes labels
    """
    label = copy.deepcopy(label_orig)
    label = Image.fromarray(label.squeeze().astype(np.uint8))
    label = label.resize( (sz[0],sz[1]),Image.NEAREST)
    label = np.array(label, dtype=np.int32)
    return label

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--dataroot', default='/home/hutao/lab/pytorchgo/example/LSD-seg/data', help='Path to source dataset')
    parser.add_argument('--model_file',default='train_log/train.class16/model_best.pth.tar', help='Model path')
    parser.add_argument('--gpu', type=int, default=4)
    parser.add_argument('--method', default='LSD', help="Method to use for training | LSD, sourceonly")
    args = parser.parse_args()

    os.environ['CUDA_VISIBLE_DEVICES'] = str(args.gpu)
    #torch.cuda.set_device(args.gpu)

    model_file = args.model_file

    n_class = 19
    print("n_class: {}".format(n_class))

    image_size=[640, 320]
    dset = 'cityscapes'
    val_loader = torch.utils.data.DataLoader(
        torchfcn.datasets.CityScapes(dset, args.dataroot,class_num = n_class,  split='val', transform=True, image_size=image_size),
        batch_size=1, shuffle=False)
    
    # Defining and loading model

    if args.method == 'sourceonly':
        model = torchfcn.models.FCN8s_sourceonly(n_class=n_class)
    elif args.method == 'LSD':
        model = torchfcn.models.FCN8s_LSD(n_class=n_class)
    else:
        raise ValueError('Invalid argument for method specified - Should be LSD or sourceonly')
        	
    if torch.cuda.is_available():
        model = model.cuda()
    print('==> Loading %s model file: %s' %
          (model.__class__.__name__, model_file))
    
    model_data = torch.load(args.model_file)
    try:
        model.load_state_dict(model_data)
    except Exception:
        model.load_state_dict(model_data['model_state_dict'])
    model.eval()

    # Evaluation
    print("best_mean_iu: {}".format(model_data['best_mean_iu']))
    
    print('==> Evaluating with CityScapes validation')
    visualizations = []
    from tensorpack.utils.stats import MIoUStatistics
    stat = MIoUStatistics(n_class)

    label_trues, label_preds = [], []
    for batch_idx, (data, target) in tqdm.tqdm(enumerate(val_loader),
                                               total=len(val_loader),
                                               ncols=80, leave=False):
        if torch.cuda.is_available():
            data, target = data.cuda(), target.cuda()
        data, target = Variable(data, volatile=True), Variable(target)
        target_np = target.data.cpu().numpy()
        if args.method == 'sourceonly':
            score = model(data)
        elif args.method == 'LSD':
            score, __, __, __ = model(data)
        lbl_pred = score.data.max(1)[1].cpu().numpy()[:, :, :].squeeze()

        if dset == 'cityscapes':
            lbl_pred_new = transform_label(lbl_pred, (2048,1024))

        label_trues.append(target.data.cpu().numpy().squeeze())
        label_preds.append(lbl_pred_new.squeeze())
        stat.feed(label_preds[-1], label_trues[-1])

    print("tensorpack mIoU16: {}".format(np.sum(stat.IoU)/16))
    print("tensorpack mean_accuracy: {}".format(stat.mean_accuracy))
    print("tensorpack accuracy: {}".format(stat.accuracy))

    # Computing mIoU
    json_path = osp.join(args.dataroot, 'cityscapes_info.json')
    compute_mIoU(label_preds, label_trues, json_path)

if __name__ == '__main__':
    main()
