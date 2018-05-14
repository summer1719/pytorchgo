# README #

Code for Semantic Segmentation for Unsupervised Domain Adaptation

Prerequisites:

	Install pytorch (Version 0.2) and torchvision
	pip install  http://download.pytorch.org/whl/cu80/torch-0.2.0.post2-cp27-cp27mu-manylinux1_x86_64.whl
	Install fcn (pip install fcn)
	Install OpenCV (pip install opencv-python)

Datasets:

We will need two datasets for our experiments - SYNTHIA and CITYSCAPES. Please download the datasets into data folder from the following links

Please download SYNTHIA-RAND-CITYSCAPES subset of the SYNTHIA dataset.
	SYNTHIA: http://synthia-dataset.net/download-2/

	CITYSCAPES: https://www.cityscapes-dataset.com/

cd  into ./data, and run the following:

    ln -s /your-path/RAND_CITYSCAPES/ RAND_CITYSCAPES
    ln -s /your-path/cityscapes/ cityscapes

To run the code, go to code folder and run the following command:

	python run_script.py

This assumes that the data is downloaded and paths are set accordingly. Options can be modified directly in the train.py script.

Please change the dataroot path, and logdir path accordingly. This will run the code and save the models in logdir folder. 

To evaluate the trained model, run 

	python eval_cityscapes.py --dataroot [] --model\_file [] -- method []

## TODO

GTAV dataset preparation

    https://github.com/VisionLearningGroup/taskcv-2017-public/tree/master/segmentation
    
Cityscapes image should rescaled!!!