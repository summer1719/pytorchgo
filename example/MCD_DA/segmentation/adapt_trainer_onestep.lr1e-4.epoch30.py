from __future__ import division

import os

import torch
import tqdm
from PIL import Image
from tensorboard_logger import configure, log_value
from torch.autograd import Variable
from torch.utils import data
from torchvision.transforms import Compose, Normalize, ToTensor
from argmyparse import add_additional_params_to_args, fix_img_shape_args, get_da_mcd_training_parser
from datasets import ConcatDataset, get_dataset, check_src_tgt_ok
from loss import CrossEntropyLoss2d, get_prob_distance_criterion
from models.model_util import get_models, get_optimizer
from transform import ReLabel, ToLabel, Scale, RandomSizedCrop, RandomHorizontalFlip, RandomRotation
from util import mkdir_if_not_exist, save_dic_to_json, check_if_done, save_checkpoint, adjust_learning_rate, \
    get_class_weight_from_file, set_debugger_org_frc
import argparse
from pytorchgo.utils import logger
import numpy as np


# from visualize import LinePlotter
# set_debugger_org_frc() #TODO interesting tool
#parser = get_da_mcd_training_parser()
torch.backends.cudnn.benchmark=True
parser = argparse.ArgumentParser(description='PyTorch Segmentation Adaptation')
parser.add_argument('--savename', type=str, default="normal", help="save name(Do NOT use '-')")
parser.add_argument('--base_outdir', type=str, default='train_output',
                    help="base output dir")
parser.add_argument('--epochs', type=int, default=30,
                    help='number of epochs to train (default: 10)')
parser.add_argument("--max_iter", type=int, default=5000)  # Iter per epoch

# ---------- Define Network ---------- #
parser.add_argument('--net', type=str, default="drn_d_38", help="network structure",
                    choices=['fcn', 'psp', 'segnet', 'fcnvgg',
                             "drn_c_26", "drn_c_42", "drn_c_58", "drn_d_22",
                             "drn_d_38", "drn_d_54", "drn_d_105"])
parser.add_argument('--res', type=str, default='50', metavar="ResnetLayerNum",
                    choices=["18", "34", "50", "101", "152"], help='which resnet 18,50,101,152')
parser.add_argument("--is_data_parallel", action="store_true",
                    help='whether you use torch.nn.DataParallel')

# ---------- Hyperparameters ---------- #
parser.add_argument('--opt', type=str, default="sgd", choices=['sgd', 'adam'],
                    help="network optimizer")
parser.add_argument('--lr', type=float, default=1e-4,
                    help='learning rate (default: 0.001)')
parser.add_argument("--adjust_lr", action="store_true",
                    help='whether you change lr')
parser.add_argument('--momentum', type=float, default=0.9,
                    help='momentum sgd (default: 0.9)')
parser.add_argument('--weight_decay', type=float, default=2e-5,
                    help='weight_decay (default: 2e-5)')
parser.add_argument('--batch_size', type=int, default=1,
                    help="batch_size")

# ---------- Optional Hyperparameters ---------- #
parser.add_argument('--augment', action="store_true",
                    help='whether you use data-augmentation or not')

# ---------- Input Image Setting ---------- #
parser.add_argument("--input_ch", type=int, default=3,
                    choices=[1, 3, 4])
parser.add_argument('--train_img_shape', default=(1024, 512), nargs=2, metavar=("W", "H"),
                    help="W H")

# ---------- Whether to Resume ---------- #
parser.add_argument("--resume", type=str, default=None, metavar="PTH.TAR",
                    help="model(pth) path")
parser.add_argument('--src_dataset', type=str, default='synthia', choices=["gta", "city", "city16", "synthia"])
parser.add_argument('--tgt_dataset', type=str, default='city16', choices=["gta", "city", "city16", "synthia"])
parser.add_argument('--src_split', type=str, default='train',
                    help="which split('train' or 'trainval' or 'val' or something else) is used ")
parser.add_argument('--tgt_split', type=str, default='train',
                    help="which split('train' or 'trainval' or 'val' or something else) is used ")
parser.add_argument('--method', type=str, default="MCD", help="Method Name")
parser.add_argument('--num_k', type=int, default=4,
                    help='how many steps to repeat the generator update')
parser.add_argument("--num_multiply_d_loss", type=int, default=1)
parser.add_argument('--d_loss', type=str, default="diff",
                    choices=['mysymkl', 'symkl', 'diff'],
                    help="choose from ['mysymkl', 'symkl', 'diff']")
parser.add_argument('--uses_one_classifier', action="store_true",
                    help="adversarial dropout regularization")

parser.add_argument('--add_bg_loss', action="store_true",
                    help="adversarial dropout regularization")

parser.add_argument('--gpu', type=str,default='4',
                    help="adversarial dropout regularization")



logger.auto_set_dir()

args = parser.parse_args()
args = add_additional_params_to_args(args)
args = fix_img_shape_args(args)
check_src_tgt_ok(args.src_dataset, args.tgt_dataset)

weight = torch.ones(args.n_class)

if not args.add_bg_loss:
    weight[args.n_class - 1] = 0  # Ignore background loss

os.environ["CUDA_DEVICE_ORDER"] = "PCI_BUS_ID"
os.environ['CUDA_VISIBLE_DEVICES'] = args.gpu

args.start_epoch = 0
resume_flg = True if args.resume else False
start_epoch = 0
if args.resume:
    print("=> loading checkpoint '{}'".format(args.resume))
    if not os.path.exists(args.resume):
        raise OSError("%s does not exist!" % args.resume)

    indir, infn = os.path.split(args.resume)

    old_savename = args.savename
    args.savename = infn.split("-")[0]
    print ("savename is %s (original savename %s was overwritten)" % (args.savename, old_savename))

    checkpoint = torch.load(args.resume)
    start_epoch = checkpoint["epoch"]
    args = checkpoint['args']
    # -------------------------------------- #
    model_g, model_f1, model_f2 = get_models(net_name=args.net, res=args.res, input_ch=args.input_ch,
                                             n_class=args.n_class, method=args.method,
                                             is_data_parallel=args.is_data_parallel)
    optimizer_g = get_optimizer(model_g.parameters(), lr=args.lr, momentum=args.momentum, opt=args.opt,
                                weight_decay=args.weight_decay)
    optimizer_f = get_optimizer(list(model_f1.parameters()) + list(model_f2.parameters()), lr=args.lr, opt=args.opt,
                                momentum=args.momentum, weight_decay=args.weight_decay)

    model_g.load_state_dict(checkpoint['g_state_dict'])
    model_f1.load_state_dict(checkpoint['f1_state_dict'])
    if not args.uses_one_classifier:
        model_f2.load_state_dict(checkpoint['f2_state_dict'])
    optimizer_g.load_state_dict(checkpoint['optimizer_g'])
    optimizer_f.load_state_dict(checkpoint['optimizer_f'])
    print("=> loaded checkpoint '{}'".format(args.resume))

else:
    model_g, model_f1, model_f2 = get_models(net_name=args.net, res=args.res, input_ch=args.input_ch,
                                             n_class=args.n_class,
                                             method=args.method, uses_one_classifier=args.uses_one_classifier,
                                             is_data_parallel=args.is_data_parallel)
    optimizer_g = get_optimizer(model_g.parameters(), lr=args.lr, momentum=args.momentum, opt=args.opt,
                                weight_decay=args.weight_decay)
    optimizer_f = get_optimizer(list(model_f1.parameters()) + list(model_f2.parameters()), opt=args.opt,
                                lr=args.lr, momentum=args.momentum, weight_decay=args.weight_decay)
if args.uses_one_classifier:
    print ("f1 and f2 are same!")
    model_f2 = model_f1

mode = "%s-%s2%s-%s_%sch" % (args.src_dataset, args.src_split, args.tgt_dataset, args.tgt_split, args.input_ch)
if args.net in ["fcn", "psp"]:
    model_name = "%s-%s-%s-res%s" % (args.method, args.savename, args.net, args.res)
else:
    model_name = "%s-%s-%s" % (args.method, args.savename, args.net)

outdir = os.path.join(args.base_outdir, mode)

# Create Model Dir
pth_dir = os.path.join(outdir, "pth")
mkdir_if_not_exist(pth_dir)

# Create Model Dir and  Set TF-Logger
tflog_dir = os.path.join(outdir, "tflog", model_name)
mkdir_if_not_exist(tflog_dir)
configure(tflog_dir, flush_secs=5)

# Save param dic
if resume_flg:
    json_fn = os.path.join(args.outdir, "param-%s_resume.json" % model_name)
else:
    json_fn = os.path.join(outdir, "param-%s.json" % model_name)
check_if_done(json_fn)
save_dic_to_json(args.__dict__, json_fn)

train_img_shape = tuple([int(x) for x in args.train_img_shape])
img_transform_list = [
    Scale(train_img_shape, Image.BILINEAR),
    ToTensor(),
    Normalize([.485, .456, .406], [.229, .224, .225])
]
if args.augment:
    aug_list = [
        RandomRotation(),
        # RandomVerticalFlip(), # non-realistic
        RandomHorizontalFlip(),
        RandomSizedCrop()
    ]
    img_transform_list = aug_list + img_transform_list

img_transform = Compose(img_transform_list)

label_transform = Compose([
    Scale(train_img_shape, Image.NEAREST),
    ToLabel(),
    #ReLabel(255, args.n_class - 1),  # Last Class is "Void" or "Background" class
])

src_dataset = get_dataset(dataset_name=args.src_dataset, split=args.src_split, img_transform=img_transform,
                          label_transform=label_transform, test=False, input_ch=args.input_ch)

tgt_dataset = get_dataset(dataset_name=args.tgt_dataset, split=args.tgt_split, img_transform=img_transform,
                          label_transform=label_transform, test=False, input_ch=args.input_ch)

train_loader = torch.utils.data.DataLoader(
    ConcatDataset(
        src_dataset,
        tgt_dataset
    ),
    batch_size=args.batch_size, shuffle=True,
    pin_memory=True)

#weight = get_class_weight_from_file(n_class=args.n_class, weight_filename=args.loss_weights_file,add_bg_loss=args.add_bg_loss)

if torch.cuda.is_available():
    model_g.cuda()
    model_f1.cuda()
    model_f2.cuda()
    weight = weight.cuda()

#criterion = CrossEntropyLoss2d(weight)
criterion = CrossEntropyLoss2d()
criterion_d = get_prob_distance_criterion(args.d_loss)

model_g.train()
model_f1.train()
model_f2.train()
for epoch in range(start_epoch, args.epochs):
    d_loss_per_epoch = 0
    c_loss_per_epoch = 0
    for ind, batch_data in tqdm.tqdm(enumerate(train_loader)):
        source, target = batch_data
        src_imgs, src_lbls = Variable(source[0]), Variable(source[1])
        tgt_imgs = Variable(target[0])

        if torch.cuda.is_available():
            src_imgs, src_lbls, tgt_imgs = src_imgs.cuda(), src_lbls.cuda(), tgt_imgs.cuda()

        # update generator and classifiers by source samples
        optimizer_g.zero_grad()
        optimizer_f.zero_grad()
        loss = 0
        d_loss = 0
        imgs = torch.cat((src_imgs, tgt_imgs), 0)
        outputs = model_g(src_imgs)

        outputs1 = model_f1(outputs)
        outputs2 = model_f2(outputs)

        c_loss = criterion(outputs1, src_lbls)
        c_loss += criterion(outputs2, src_lbls)
        c_loss.backward(retain_graph=True)
        lambd = 1.0
        model_f1.set_lambda(lambd)
        model_f2.set_lambda(lambd)
        outputs = model_g(tgt_imgs)
        outputs1 = model_f1(outputs, reverse=True)
        outputs2 = model_f2(outputs, reverse=True)
        loss = - criterion_d(outputs1, outputs2)
        loss.backward()
        optimizer_f.step()
        optimizer_g.step()

        d_loss = -loss.data[0]
        d_loss_per_epoch += d_loss
        c_loss = c_loss.data[0]
        c_loss_per_epoch += c_loss
        if ind % 100 == 0:
            print("iter [%d] DLoss: %.6f CLoss: %.4f Lambd: %.4f" % (ind, d_loss, c_loss, lambd))

        if ind > args.max_iter:
            break

    print("Epoch [%d] DLoss: %.4f CLoss: %.4f" % (epoch, d_loss_per_epoch, c_loss_per_epoch))

    log_value('c_loss', c_loss_per_epoch, epoch)
    log_value('d_loss', d_loss_per_epoch, epoch)
    log_value('lr', args.lr, epoch)

    if args.adjust_lr:
        args.lr = adjust_learning_rate(optimizer_g, args.lr, args.weight_decay, epoch, args.epochs)
        args.lr = adjust_learning_rate(optimizer_f, args.lr, args.weight_decay, epoch, args.epochs)

    checkpoint_fn = os.path.join(pth_dir, "%s-%s.pth.tar" % (model_name, epoch + 1))
    args.start_epoch = epoch + 1
    save_dic = {
        'epoch': epoch + 1,
        'args': args,
        'g_state_dict': model_g.state_dict(),
        'f1_state_dict': model_f1.state_dict(),
        'optimizer_g': optimizer_g.state_dict(),
        'optimizer_f': optimizer_f.state_dict(),
    }
    if not args.uses_one_classifier:
        save_dic['f2_state_dict'] = model_f2.state_dict()

    save_checkpoint(save_dic, is_best=False, filename=checkpoint_fn)


def proceed_test(model_g,model_f1,model_f2, quick_test=1e10):
    logger.info("proceed test on cityscapes val set...")
    model_g.eval()
    model_f1.eval()
    model_f2.eval()

    val_img_transform = Compose([
        Scale(train_img_shape, Image.BILINEAR),
        ToTensor(),
        Normalize([.485, .456, .406], [.229, .224, .225]),

    ])
    val_label_transform = Compose([Scale(train_img_shape, Image.BILINEAR),
                               # ToTensor()
                               ])

    test_img_shape = (2048, 1024)

    target_loader = data.DataLoader(tgt_dataset = get_dataset(dataset_name="city16", split="val",
        img_transform=val_img_transform,label_transform=val_label_transform, test=True, input_ch=3),
                                    batch_size=1, pin_memory=True)

    from tensorpack.utils.stats import MIoUStatistics
    stat = MIoUStatistics(args.n_class)

    for index, (origin_imgs, labels, paths) in tqdm(enumerate(target_loader)):
        if index > quick_test: break
        path = paths[0]
        # if index > 10: break

        imgs = Variable(origin_imgs)
        if torch.cuda.is_available():
            imgs = imgs.cuda()

        feature = model_g(imgs)
        outputs = model_f1(feature)

        if args.use_f2:
            outputs += model_f2(feature)


        pred = outputs[0, :].data.max(0)[1].cpu()

        img = Image.fromarray(np.uint8(pred.numpy()))
        img = img.resize(test_img_shape, Image.NEAREST)
        feed_predict = np.squeeze(np.uint8(pred.numpy()))
        feed_label = np.squeeze(np.asarray(labels.numpy()))
        print np.unique(feed_predict)
        print np.unique(feed_label)

        stat.feed(feed_predict, feed_label)




    print("=>mIoU :{}".format(stat.mIoU))
    logger.info("tensorpack mIoU: {}".format(stat.mIoU))
    logger.info("tensorpack mean_accuracy: {}".format(stat.mean_accuracy))
    logger.info("tensorpack accuracy: {}".format(stat.accuracy))
    model_g.train()
    model_f1.train()
    model_f2.train()