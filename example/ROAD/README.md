
## Dann

[https://github.com/pumpikano/tf-dann](https://github.com/pumpikano/tf-dann)


## result

|arch|result|
|---|----|
|train.distill.full.diff2d|first epoch can reach 19|
reborn.vgg16.nofakeforG|epoch8:1,terminated|
reborn.vgg16.lr1e-4|epoch4=1,terminated|
reborn.vgg16.reverse.lr1e-4|epoch16:=8,terminated|
reborn.vgg16.lr1e-5.w1_10_1.sm_bugfix.class16|epoch26=18,up and down, terminated|
reborn.vgg16.**lr1e-4**.w1_10_1.sm_bugfix.class16.adapSegnet_DC.standardGAN.1024x512|epoch10=20,up and down,terminated|reborn.vgg16.**lr1e-4**.w1_10_1.sm_bugfix.class16.adapSegnet_DC.1024x512|epoch10=22,terminated|
reborn.vgg16.lr1e-5.w1_10_1.sm_bugfix.class16.adapSegnet_DC.standardGAN.1024x512|largest=28, but is unstable, terminated|

|arch|1024x512 mIoU|2048x1024 mIoU|
|---|----|----|
|reborn.vgg16.lr1e-5.w1_10_1.sm_bugfix.totalconfusion|22|17.82
reborn.vgg16.lr1e-4.w1_10_1.sm_bugfix.class16.adapSegnet_DC.standardGAN.1024x512|23.93|20.57|
reborn.vgg16.lr1e-5.w1_10_1.sm_bugfix.class16.adapSegnet_DC.standardGAN.1024x512|28.45|19.72|
reborn.vgg16.lr1e-5.w1_10_1.sm_bugfix.class16.adapSegnet_DC.1024x512.sgd|30.57|26.18|
reborn.vgg16.lr1e-5.w1_10_1.sm_bugfix.class16.adapSegnet_DC.1024x512.wgan|29.70|27.45|
reborn.vgg16.lr1e-5.w1_10_1.sm_bugfix.class16.adapSegnet_DC.1024x512.wgan.d_mse|28.54|28.21|
reborn.vgg16.lr1e-5.w1_10_1.sm_bugfix.class16.adapSegnet_DC.1024x512.wgan.d_mse.dstep1|30.95|28.88|
reborn2||26.28|
reborn2.lr1e-5_lr1e-4||24.7
reborn2.lr1e-5_lr1e-4.deeplabv2||epoch1=5%,terminated
|reborn2.best.deeplabv2_fix.epoch25.py|epoch2=4%,terminated|
reborn2.best||**29.7**
reborn2.best.1_10_10||epoch1=9.8,final 16.36|
reborn2.best.1_10_10.uniform_data||epoch1=6,terminated|
reborn2.best.2sgd|epoch2=4%,terminated
reborn2.best.1_5_1|epoch6,largest=27%,terminated|
reborn2.best.1_10_1.uniform_data|epoch3=38,run out|
reborn2.best.feat_distill|epoch4=28.1,run out|

