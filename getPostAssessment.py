from PIL import Image
from io import BytesIO
import cv2
from imageai.Detection import ObjectDetection
from sklearn.preprocessing import MultiLabelBinarizer
import pandas as pd
from tqdm.notebook import tqdm
tqdm.pandas()

import plotly.express as px
from sklearn.feature_extraction.text import TfidfVectorizer

from instascrape import Profile
from collections import defaultdict
from googletrans import Translator
import requests
import numpy as np
import os
import pickle
import sys

def createDetector(model='models/yolo.h5'):
    """
    The function creates an object detector based on a model

    Input:
    model (str):  path to a pretrained h5 model

    Output:
    imageai.Detection.ObjectDetection object

    """
    detector = ObjectDetection()
    if 'yolo' in model:
        detector.setModelTypeAsYOLOv3()
    elif 'resnet' in model:
        detector.setModelTypeAsRetinaNet()
    execution_path = os.getcwd()
    detector.setModelPath( os.path.join(execution_path , model))# "resnet50_coco_best_v2.1.0.h5"))
    detector.loadModel()
    return detector

def getObjects(url, detector):
    """
    The function returns a dictionary of the objects with probabilities detected on the image from url
    based on a given model.

    input:
    idx (int): id of an image. Is used for tracking purposes only.
    url (str): url with an image
    model (str): path to a pre-trained object detection model

    output:
    dict: a dictionary of the objects with probabilities detected on the image from url
    based on a given model.

    """

    try:
        pth = "imageTemporary.jpg"
        response = requests.get(url)
        img = Image.open(BytesIO(response.content))
        img.save(pth)
#

        detections = detector.detectObjectsFromImage(input_image=pth, output_image_path=pth)
#                                                      output_image_path=os.path.join(execution_path ,
#                                                                                     "imagenew.jpg"))
        return detections
    except:
        return None

def getColorData(imagePath, n = 10):
    """
    The function returns a dataframe with binned color histograms as columns

    Input:
    imagePath (str): image URL or path
    n (int):         number of bins

    Output:
    pandas dataframe

    """
    response = requests.get(imagePath)
    img = Image.open(BytesIO(response.content))
    img.save('imageTemporary.jpg')
    pth = "imageTemporary.jpg"
    img = cv2.imread("imageTemporary.jpg")
    color = ('b','g','r')
    dfC = pd.DataFrame()
    for i,col in enumerate(color):
        hist = cv2.calcHist([img],[i],None,[n],[0,256])
        for j, x in enumerate(hist):
            s = np.sum(hist)
            colname = f'{col}_{j}'
#                 dfC['id'] = row['id']
#                dfC['image128'] = [cv2.resize(img,(128,128))]
            dfC[colname]=x/s
    return dfC


def predictImageLikes(model,
                      imgUrl,
                      captionText = '',
                      numOfTaggedUsers=0,
                      numOfHashtags = None,
                      uploadDayOfWeek = 3,
                      numOfFollowers=None):
    """
    The function returns an approximate amount of likes based on the pos properties

    Input:
    model (sklearn model):     fitted model with predict method

    imagepath (str):           image path or URL

    captionText (str):         caption text for the post with hashtags (if present),
                               default: ''

    numOfHashtags (int):       number of hashtags, if None - calculates from the captionText,
                               default: None

    numOfTaggedUsers (int):    number of tagged accounts,
                               default: 0

    uploadDayOfWeek (int):     week day number of the planned post upload,
                               default: 3 (wednesday)

    numOfFollowers (int):      current number of followers,
                               if None - relative score is returned, else absolute number of expected likes,
                               default: None


    Output:
    float:                     relative (if numOfFollowers is None) or absolute
                               (multiplied by numOfFollowers) value of expected likes
    """
    columnsToFeed = ['imageRatio','numOfHashtags','numOfTaggedUsers','lenOfCaption','uploadDayOfWeek',
                     'airplane','apple','backpack','bear','bed','bench','bicycle','bird','boat','book',
                     'bottle','bowl','broccoli','bus','cake','car','cat','cell phone','chair','clock',
                     'couch','cow','cup','dining table','dog','donut','elephant','fire hydrant','fork',
                     'frisbee','giraffe','handbag','horse','hot dog','keyboard','kite','knife','laptop',
                     'microwave','motorcycle','mouse','orange','oven','person','pizza','potted plant',
                     'refrigerator','remote','sandwich','sheep','sink','skateboard','skis','spoon',
                     'sports ball','stop sign','suitcase','surfboard','teddy bear','tennis racket','tie',
                     'toilet','traffic light','train','truck','tv','umbrella','vase','wine glass','zebra',
                     'b_0','b_1','b_2','b_3','b_4','b_5','b_6','b_7','b_8','b_9','g_0','g_1','g_2','g_3',
                     'g_4','g_5','g_6','g_7','g_8','g_9','r_0','r_1','r_2','r_3','r_4','r_5','r_6','r_7',
                     'r_8','r_9','weightedLikes','logWeightedLikes']

    objectsList = columnsToFeed[5:-32]

    response = requests.get(imgUrl)
    img = Image.open(BytesIO(response.content))
    width, height = img.size
    imageRatio = img.size[0]/img.size[1]
    print('imageRatio:', imageRatio)

    df = getColorData(imgUrl)
    df['imageRatio'] = imageRatio
    print('imageRatio:', imageRatio)

    if numOfHashtags==None:
        numOfHashtags = len(captionText.split('#'))-1
        df['numOfHashtags'] = numOfHashtags
    else:
        df['numOfHashtags'] = numOfHashtags
    print('numOfHashtags:', numOfHashtags)

    df['numOfTaggedUsers'] = len(captionText.split('@'))-1 + numOfTaggedUsers
    print('numOfTaggedUsers:', numOfTaggedUsers)

    lenOfCaption = len(captionText)
    df['lenOfCaption'] = lenOfCaption
    print('lenOfCaption:', lenOfCaption)

    df['uploadDayOfWeek'] = uploadDayOfWeek
    print('uploadDayOfWeek:', uploadDayOfWeek)

    detectedObjects = getObjects(imgUrl, createDetector())
    presentObjects = []
    for obj in detectedObjects:
        if obj['percentage_probability']>=0.8:
            presentObjects.append(obj['name'])
    presentObjects = list(set(presentObjects))
    print('presentObjects:', presentObjects)

    for obj in objectsList:
        if obj in presentObjects:
            df[obj]=[1]
        else:
            df[obj]=[0]
    df = df[columnsToFeed[:-2]]

    if numOfFollowers!=None:
        return np.exp(model.predict(df))*numOfFollowers[0]
    else:
        return np.exp(model.predict(df))[0]


if __name__ == "__main__":
    filename = 'models/xgbr_1.pkl'
    model = pickle.load(open(filename, 'rb'))
    print(predictImageLikes(model,
                          imgUrl=sys.argv[1],
                          captionText =sys.argv[2]))
