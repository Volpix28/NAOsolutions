#Imports
import time
import calendar
import time
import requests
BASE = "http://192.168.32.1:5000/"

# Python Image Library
from PIL import Image #works only in local env
from naoqi import ALProxy

#Connection settings
NAOIP = '192.168.8.105'
PORT = 9559
NAME = "nao"
passwd = "19981"

## TEST
tts = 'ALTextToSpeech'
text = ALProxy(tts, NAOIP, PORT)
text.say("Testrun")

def takePicture(IP, PORT,camera,resolution, colorSpace):
  """
  First get an image from Nao, then show it on the screen with PIL.
  """
  camProxy = ALProxy("ALVideoDevice", IP, PORT)
  videoClient = camProxy.subscribeCamera("python_client",0, resolution, colorSpace, 5)
  t0 = time.time()

  # Get a camera image.
  # image[6] contains the image data passed as an array of ASCII chars.
  naoImage = camProxy.getImageRemote(videoClient)
  t1 = time.time()
  
  # Time the image transfer.
  print "acquisition delay ", t1 - t0
  camProxy.unsubscribe(videoClient)

  # Now we work with the image returned and save it as a PNG  using ImageDraw
  # package.

 
  # Get the image size and pixel array.
  imageWidth = naoImage[0]
  imageHeight = naoImage[1]
  array = naoImage[6]


  # Create a PIL Image from our pixel array.
  im = Image.frombytes("RGB", (imageWidth, imageHeight), array)

  # Save the image.
  current_GMT = time.gmtime()

  time_stamp = calendar.timegm(current_GMT)
  time_stamp = str(time_stamp)
  
  global imName
  imName = r'image_' + time_stamp + r'.png'
  im.save("images/" + imName, "PNG") #Save files with continuative numbers
 

  
camera = 0 # 0 = top camera, 1 = bottom camera
resolution = 3 # 0 = QQVGA, 1 = QVGA, 2 = VGA
colorSpace = 11 # http://doc.aldebaran.com/2-5/family/robots/video_robot.html#cameracolorspace-mt9m114
naoImage = takePicture(NAOIP, PORT,camera,resolution, colorSpace)


#Filler
text.say("I hope you are having a good day.")

#Get response from API if it's a new or known person
#response = requests.get(BASE + "video/2", {})
#print(response.json())

#Set action for new person
#Name recognition

#Set action for known person
#text.say("Nice to meet you again.")
#text.say(name)
#text.say("Hope you are having a good day.")

#Get response from API for gender and mood


#Set action based on mood


#Take another picture to check if mood changed


#Emotion detection









