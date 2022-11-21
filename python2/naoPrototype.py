# Imports
import time
import calendar
import requests
import os
import ast
# Python Image Library
from PIL import Image # works only in local env
from naoqi import ALProxy

# Connection settings
NAOIP = '192.168.8.105'
PORT = 9559
NAME = 'nao'
passwd = '19981'
BASE_API = 'http://172.22.0.1:5000/'

# Test
tts = 'ALTextToSpeech'
text = ALProxy(tts, NAOIP, PORT)
text.say('Test run')

# NAO picture config
camera = 1 # 0 = top camera, 1 = bottom camera
resolution = 3 # 0 = QQVGA, 1 = QVGA, 2 = VGA
colorSpace = 11 # http://doc.aldebaran.com/2-5/family/robots/video_robot.html#cameracolorspace-mt9m114


def takePicture(IP, PORT, camera, resolution, colorSpace, location):
  camProxy = ALProxy('ALVideoDevice', IP, PORT)
  videoClient = camProxy.subscribeCamera('python_client', camera, resolution, colorSpace, 5)
  naoImage = camProxy.getImageRemote(videoClient)
  camProxy.unsubscribe(videoClient)
  imageName = 'image_' + str(calendar.timegm(time.gmtime())) + '.png' # example: image_{time_stamp}.png
  im = Image.frombytes('RGB', (naoImage[0], naoImage[1]), naoImage[6]) # naoImage[0] = width, naoImage[1] = height, naoImage[6] = image data as ASCII char array
  im.save(location + os.sep + imageName, 'PNG')
  print('Image: ' + imageName + ' successfully saved @ ' + location)
  return imageName

naoImage = takePicture(NAOIP, PORT, camera, resolution, colorSpace, 'fileshare') # TODO set fileshare param to standard location 

# Filler
text.say('I hope you are having a good day.')

response_fr = requests.get(BASE_API + 'facerecognition/' + naoImage) # .get, .post
response_ed = requests.get(BASE_API + 'emotiondetection/' + naoImage)
result_ed = response_ed.json()
result_fr = ast.literal_eval(response_fr.json())
gender = str(result_ed[u'gender'])
emotion = str(result_ed[u'dominant_emotion'])
print(emotion, gender)
if result_fr['name'] == 'not found':
    text.say(
      'Nice to meet you, you look like a beautiful ' + gender \
      + 'and you seem to be ' + emotion \
      + 'May I ask for your Name?'
      )
    # say your name now: *insert SpeechToText
    # API Call addName
else:
    text.say(
      'Hey ' + result_fr['name'] + 'long time no see!'\
      + 'You look rather ' + emotion \
      + ' today.')

#Set action for known person
#text.say('Nice to meet you again.')
#text.say(name)
#text.say('Hope you are having a good day.')

#Get response from API for gender and mood


#Set action based on mood


#Take another picture to check if mood changed


#Emotion detection
