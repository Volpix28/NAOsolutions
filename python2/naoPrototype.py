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
text.say('Testrun')

def takePicture(IP, PORT, camera, resolution, colorSpace): # see takePictureNew - matthias
  '''
  First get an image from Nao, then show it on the screen with PIL.
  '''
  camProxy = ALProxy('ALVideoDevice', IP, PORT)
  videoClient = camProxy.subscribeCamera('python_client', 0, resolution, colorSpace, 5)
  t0 = time.time()

  # Get a camera image.
  # image[6] contains the image data passed as an array of ASCII chars.
  naoImage = camProxy.getImageRemote(videoClient)
  t1 = time.time()
  
  # Time the image transfer.
  print('acquisition delay ', t1-t0)
  camProxy.unsubscribe(videoClient)

  # Now we work with the image returned and save it as a PNG  using ImageDraw package.

 
  # Get the image size and pixel array.
  imageWidth = naoImage[0]
  imageHeight = naoImage[1]
  array = naoImage[6]


  # Create a PIL Image from our pixel array.
  im = Image.frombytes('RGB', (imageWidth, imageHeight), array)

  # Save the image.
  current_GMT = time.gmtime()

  time_stamp = calendar.timegm(current_GMT)
  time_stamp = str(time_stamp)
  
  global imName
  imName = r'image_' + time_stamp + r'.png'
  im.save('fileshare' + os.sep + imName, 'PNG') #Save files with continuative numbers


# TODO: needs to be tested with NAO - matthias
def takePictureNew(IP, PORT, camera, resolution, colorSpace, location): # missing camera argument in original function - matthias
  camProxy = ALProxy('ALVideoDevice', IP, PORT)
  videoClient = camProxy.subscribeCamera('python_client', camera, resolution, colorSpace, 5)
  naoImage = camProxy.getImageRemote(videoClient)
  camProxy.unsubscribe(videoClient)
  imageName = 'image_' + str(calendar.timegm(time.gmtime())) + '.png' # example: image_{time_stamp}.png
  im = Image.frombytes('RGB', (naoImage[0], naoImage[1]), naoImage[6]) # naoImage[0] = width, naoImage[1] = height, naoImage[6] = image data in ASCII char array
  im.save(location + os.sep + imageName, 'PNG')
  print('Image: ' + imageName + ' successfully saved @ ' + location)
  return imageName

# naoImage = takePictureNew(NAOIP, PORT, camera, resolution, colorSpace, pathToFileshare)
  
camera = 1 # 0 = top camera, 1 = bottom camera
resolution = 3 # 0 = QQVGA, 1 = QVGA, 2 = VGA
colorSpace = 11 # http://doc.aldebaran.com/2-5/family/robots/video_robot.html#cameracolorspace-mt9m114
naoImage = takePicture(NAOIP, PORT, camera, resolution, colorSpace)


#Filler
text.say('I hope you are having a good day.')

response_fr = requests.get(BASE_API + 'facerecognition/' + imName) # .get, .post
response_ed = requests.get(BASE_API + 'emotiondetection/' + imName)
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
