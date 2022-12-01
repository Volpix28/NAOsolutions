# Imports
import time
import calendar
import requests
import os
import ast
import speech_recognition as sr
# Python Image Library
from PIL import Image # works only in local env
from naoqi import ALProxy
from scipy.io.wavfile import write

#Costum dialogs
from dialog import Dialog
Dialog = Dialog()

#costum functions
from functions import Functions
Functions = Functions()


# Connection settings
NAOIP = '192.168.0.242'
PORT = 9559
NAME = "nao"
passwd = "19981"
BASE_API = 'http://192.168.0.213:5000'

# Test
tts = 'ALTextToSpeech'
text = ALProxy(tts, NAOIP, PORT)
text.setParameter("speed", 80)


# NAO picture config
camera = 0 # 0 = top camera, 1 = bottom camera
resolution = 3 # 0 = QQVGA, 1 = QVGA, 2 = VGA
colorSpace = 11 # http://doc.aldebaran.com/2-5/family/robots/video_robot.html#cameracolorspace-mt9m114

##########################
# START OF CONVERSATION #
##########################

text.say(Dialog.welcome)
naoImage = Functions.takePicture(NAOIP, PORT, camera, resolution, colorSpace, 'fileshare/images') 
time.sleep(2)
response_ed = requests.get(BASE_API + '/emotiondetection/' + naoImage)
result_ed = ast.literal_eval(response_ed.json())
while result_ed['dominant_emotion'] == 'face_not_found':
    # TO-DO: delete old naoImage from fileshare
    text.say('Face not found.')
    naoImage = Functions.takePicture(NAOIP, PORT, camera, resolution, colorSpace, 'fileshare/images')
    response_ed = requests.get(BASE_API + '/emotiondetection/' + naoImage)
    result_ed = ast.literal_eval(response_ed.json())
    
response_fr = requests.get(BASE_API + '/facerecognition/' + naoImage)
result_fr = ast.literal_eval(response_fr.json())
gender = str(result_ed[u'gender'])
emotion = str(result_ed[u'dominant_emotion'])

if result_fr['name'] == 'not_found':
    text.say(Dialog.name_question(gender))
    name = Functions.get_and_save_name(NAOIP, PORT)
    img_id = result_fr['img_id']
    requests.get(BASE_API + '/addname/' + name + '/' + naoImage)
else:
    name = result_fr['name']
    img_id = result_fr['img_id']
    text.say(Dialog.greeting_known_person(name, emotion))
    Functions.delete_user(name, img_id)

manual_emotion_rating = Functions.manual_emotion(name)

#Set action based on mood
Functions.action(manual_emotion_rating, emotion)

# Line below needed?
# text.say('Let me take another picture so I can see if your mood changed.')

#Take another picture to check if mood changed
#Change variable names or no need?
naoImage = Functions.takePicture(NAOIP, PORT, camera, resolution, colorSpace, 'fileshare/images') 

#Emotion detection
response_ed = requests.get(BASE_API + '/emotiondetection/' + naoImage)
result_ed = ast.literal_eval(response_ed.json())
while result_ed['dominant_emotion'] == 'face_not_found':
    # TO-DO: delete old naoImage from fileshare
    text.say('Face not found.')
    naoImage = Functions.takePicture(NAOIP, PORT, camera, resolution, colorSpace, 'fileshare/images')
    response_ed = requests.get(BASE_API + '/emotiondetection/' + naoImage)
    result_ed = ast.literal_eval(response_ed.json())

emotion2 = str(result_ed[u'dominant_emotion'])

print('emotion before action: ' + emotion + ' emotion after action: ' +  emotion2 + ' manual emotion rating: ' + str(manual_emotion_rating))

Functions.emotionchange(emotion, emotion2)



#DELETE USER?


