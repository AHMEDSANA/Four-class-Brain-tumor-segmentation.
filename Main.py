# -*- coding: utf-8 -*-
"""Training of Axis1.ipynb

Automatically generated by Colaboratory.

Original file is located at
    https://colab.research.google.com/drive/18_X2k6liqJEu5r1RPP7skab-ZvwUl-lu
"""

import random
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
#%matplotlib inline
#import tensorflow as tf
import keras.backend as K
import keras
avg_sens = [0,0,0,0]
avg_spec = [0,0,0,0]

from keras.models import Model, load_model
#from keras.layers import Input, BatchNormalization, Activation, Dense, Dropout,Maximum
#from keras.layers.core import Lambda, RepeatVector, Reshape
#from keras.layers.convolutional import Conv2D, Conv2DTranspose,Conv3D,Conv3DTranspose
#from keras.layers.pooling import MaxPooling2D, GlobalMaxPool2D,MaxPooling3D
#from keras.layers.merge import concatenate, add
#from keras.callbacks import EarlyStopping, ModelCheckpoint, ReduceLROnPlateau
from keras.optimizers import Adam
#from keras.preprocessing.image import ImageDataGenerator, array_to_img, img_to_array, load_img

#from skimage.io import imread, imshow, concatenate_images
#from skimage.transform import resize

def standardize(image):

  standardized_image = np.zeros(image.shape)

  #
  
      # iterate over the `z` dimension
  for z in range(image.shape[2]):
      # get a slice of the image 
      # at channel c and z-th dimension `z`
      image_slice = image[:,:,z]

      # subtract the mean from image_slice
      centered = image_slice - np.mean(image_slice)
      
      # divide by the standard deviation (only if it is different from zero)
      if(np.std(centered)!=0):
          centered = centered/np.std(centered) 

      # update  the slice of standardized image
      # with the scaled centered and scaled image
      standardized_image[:, :, z] = centered

  ### END CODE HERE ###

  return standardized_image


def dice_coef(y_true, y_pred, epsilon=0.00001):
    """
    Dice = (2*|X & Y|)/ (|X|+ |Y|)
         =  2*sum(|A*B|)/(sum(A^2)+sum(B^2))
    ref: https://arxiv.org/pdf/1606.04797v1.pdf
    
    """
    axis = (0,1,2)
    dice_numerator = 2. * K.sum(y_true * y_pred, axis=axis) + epsilon
    dice_denominator = K.sum(y_true*y_true, axis=axis) + K.sum(y_pred*y_pred, axis=axis) + epsilon
    return K.mean((dice_numerator)/(dice_denominator))

def dice_coef_loss(y_true, y_pred):
    return 1-dice_coef(y_true, y_pred)

def compute_class_sens_spec(pred, label, class_num):
    """
    Compute sensitivity and specificity for a particular example
    for a given class.
    Args:
        pred (np.array): binary arrary of predictions, shape is
                         (num classes, height, width, depth).
        label (np.array): binary array of labels, shape is
                          (num classes, height, width, depth).
        class_num (int): number between 0 - (num_classes -1) which says
                         which prediction class to compute statistics
                         for.
    Returns:
        sensitivity (float): precision for given class_num.
        specificity (float): recall for given class_num
    """

    # extract sub-array for specified class
    class_pred = pred[:,:,:,class_num]
    class_label = label[:,:,:,class_num]

    ### START CODE HERE (REPLACE INSTANCES OF 'None' with your code) ###
    
    # compute true positives, false positives, 
    # true negatives, false negatives
    tp = np.sum((class_pred == 1) & (class_label == 1))
    tn = np.sum((class_pred == 0) & (class_label == 0))
    fp = np.sum((class_pred == 1) & (class_label == 0))
    fn = np.sum((class_pred == 0) & (class_label == 1))

    # compute sensitivity and specificity
    sensitivity = tp / (tp + fn)
    specificity = tn / (tn + fp)

    ### END CODE HERE ###

    return sensitivity, specificity


def get_sens_spec_df(pred, label):
    patch_metrics = pd.DataFrame(
        columns = ['Nothing',
                    'Edema', 
                   'Non-Enhancing Tumor', 
                   'Enhancing Tumor'], 
        index = ['Sensitivity',
                 'Specificity'])
    
    for i, class_name in enumerate(patch_metrics.columns):
        sens, spec = compute_class_sens_spec(pred, label, i)
        avg_sens[i] += sens
        avg_spec[i] += spec
        patch_metrics.loc['Sensitivity', class_name] = round(sens,4)
        patch_metrics.loc['Specificity', class_name] = round(spec,4)

    #return patch_metrics



import os
model_axis1 = load_model('/content/drive/MyDrive/models/2dincr_4class_axis1.h5',custom_objects = {'dice_coef_loss' : dice_coef_loss , 'dice_coef' : dice_coef})
model_axis2 = load_model('/content/drive/MyDrive/models/2dincr_4class_axis2.h5',custom_objects = {'dice_coef_loss' : dice_coef_loss , 'dice_coef' : dice_coef})
model_axis3 = load_model('/content/drive/MyDrive/models/2dincr_4class_axis3.h5',custom_objects = {'dice_coef_loss' : dice_coef_loss , 'dice_coef' : dice_coef})





path = '/content/drive/MyDrive/BRATS2018TRAIN/HGG'
all_images = os.listdir(path)
#print(len(all_images))
all_images.sort()
data = np.zeros((240,240,155,4))
image_data2=np.zeros((240,240,155))



import nibabel as nib
mean_loss = 0
mean_accu = 0
for image_num in range(180,210):
    data = np.zeros((240,240,155,4))
    #print(epochs)
    print("Entering Image" , image_num)

# data preprocessing starts here

    x = all_images[image_num]
    #print(x)
    folder_path = path + '/' + x;
    modalities = os.listdir(folder_path)
    modalities.sort()
    #data = []
    w = 0
    for j in range(len(modalities)):
      image_path = folder_path + '/' + modalities[j]
      if not(image_path.find('seg.nii') == -1):
        img = nib.load(image_path);
        image_data2 = img.get_data()
        image_data2 = np.asarray(image_data2)
        #print("Entered ground truth")
      else:
        img = nib.load(image_path);
        image_data = img.get_data()
        image_data = np.asarray(image_data)
        image_data = standardize(image_data)
        data[:,:,:,w] = image_data
        #print("Entered modality")
        w = w+1
        
    image_data2[image_data2 == 4] = 3
    image_data2 = keras.utils.to_categorical(image_data2, num_classes = 4)

    data_axis1=data
    data_axis2=np.moveaxis(data,1,0)
    data_axis3=np.moveaxis(data,2,0)


    Y_hat_axis1 = model_axis1.predict(x=data_axis1)
    Y_hat_axis2 = model_axis2.predict(x=data_axis2)
    Y_hat_axis3 = model_axis3.predict(x=data_axis3)
        
    Y_hat_axis2 = np.moveaxis(Y_hat_axis2,0,1)
    Y_hat_axis3 = np.moveaxis(Y_hat_axis3,0,2)

    Y_hat_average = np.maximum(np.maximum(Y_hat_axis1,Y_hat_axis2),Y_hat_axis3)/3
    dice_acc=K.eval(dice_coef(Y_hat_average,image_data2))
    dice_loss=1- dice_acc
    print(dice_acc)

    Y_hat_average_onehot = np.argmax(Y_hat_average,axis = -1)
    Y_hat_average_onehot = keras.utils.to_categorical(Y_hat_average_onehot,num_classes=4)

    get_sens_spec_df(Y_hat_average_onehot,image_data2)

    mean_loss += dice_loss
    mean_accu += dice_acc
    
print()
print("Mean Dice Loss" , mean_loss/30)
print("Mean Dice Coefficient(Accuracy)" , mean_accu/30)
print()
print("Mean Sensitivity for class 0" , avg_sens[0]/30)
print("Mean Specificity for class 0" , avg_spec[0]/30)
print()
print("Mean Sensitivity for class 1" , avg_sens[1]/30)
print("Mean Specificity for class 1" , avg_spec[1]/30)
print()
print("Mean Sensitivity for class 2" , avg_sens[2]/30)
print("Mean Specificity for class 2" , avg_spec[2]/30)
print()
print("Mean Sensitivity for class 3" , avg_sens[3]/30)
print("Mean Specificity for class 3" , avg_spec[3]/30)
print()
        

import nibabel as nib
x = all_images[208]
print("Results on image number 203")
folder_path = path + '/' + x;
modalities = os.listdir(folder_path)
modalities.sort()
data = np.zeros((240,240,155,4))
#data = []
w = 0
for j in range(len(modalities)):
  #print(modalities[j])

  image_path = folder_path + '/' + modalities[j]
  if not(image_path.find('seg.nii') == -1):
    img = nib.load(image_path);
    image_data2 = img.get_data()
    image_data2 = np.asarray(image_data2)
    print("Entered ground truth")
  else:
    img = nib.load(image_path);
    image_data = img.get_data()
    image_data = np.asarray(image_data)
    image_data = standardize(image_data)
    data[:,:,:,w] = image_data
    print("Entered modality")
    w = w+1
    
    
image_data2[image_data2 == 4] = 3

data_axis1=data
data_axis2=np.moveaxis(data,1,0)
data_axis3=np.moveaxis(data,2,0)

image_data2_axis1=image_data2
image_data2_axis2=np.moveaxis(image_data2,1,0)
image_data2_axis3=np.moveaxis(image_data2,2,0)

Y_hat_axis1 = model_axis1.predict(x=data_axis1)
Y_hat_axis2 = model_axis2.predict(x=data_axis2)
Y_hat_axis3 = model_axis3.predict(x=data_axis3)

Y_hat_axis2 = np.moveaxis(Y_hat_axis2,0,1)
Y_hat_axis3 = np.moveaxis(Y_hat_axis3,0,2)

Y_hat_average = np.maximum(np.maximum(Y_hat_axis1,Y_hat_axis2),Y_hat_axis3)/3

Y_hat_average_onehot = np.argmax(Y_hat_average,axis = -1)


import matplotlib.pyplot as plt
#import matplotlib.pyplot as plt
img = data[:,:,75,0]
imgplot = plt.imshow(img)
plt.title('Flair Modality 75th slice alon')
plt.savefig('Flair')
plt.show()

img2 = image_data2[:,:,75]
imgplot2 = plt.imshow(img2)
plt.title('Ground Truth of 75th slice')
plt.savefig('Ground_Truth')
plt.show()

img3 = Y_hat_average_onehot[:,:,75]
imgplot3 = plt.imshow(img3)
plt.title('Our Segmentation -> 75th slice')
plt.savefig('Our Segmentation')
plt.show()