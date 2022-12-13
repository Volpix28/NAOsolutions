import requests
import os
import ast
from naoqi import ALProxy
from scipy.io.wavfile import write
from dialog import Dialog  # custom dialogs
from functions import Functions  # custom functions


# Connection settings
NAOIP = '192.168.8.105'
PORT = 9559
NAME = "nao"
PASSWD = "19981"
BASE_API = 'http://192.168.8.120:5000'

# Proxy
TEXTPROXY = ALProxy('ALTextToSpeech', NAOIP, PORT)
TEXTPROXY.setParameter("speed", 80)

POSTUREPROXY = ALProxy('ALRobotPosture', NAOIP, PORT)
MOTIONPROXY = ALProxy('ALMotion', NAOIP, PORT)

fileshare = os.path.join(os.getcwd(), 'fileshare')
images_folder = os.path.join(fileshare, 'images')

# NAO picture config
camera = 0 # 0 = top camera, 1 = bottom camera
resolution = 3 # 0 = QQVGA, 1 = QVGA, 2 = VGA
colorSpace = 11 # http://doc.aldebaran.com/2-5/family/robots/video_robot.html#cameracolorspace-mt9m114

##########################
# START OF CONVERSATION #
##########################

TEXTPROXY.say(Dialog.welcome)
result_ed, naoImage = Functions.emotionDetectionWithPic(NAOIP, PORT, BASE_API, TEXTPROXY, camera, resolution, colorSpace, images_folder)
    
response_fr = requests.get(BASE_API + '/facerecognition/' + naoImage)
result_fr = ast.literal_eval(response_fr.json())
print(result_fr)
gender = str(result_ed[u'gender'])
emotion = str(result_ed[u'dominant_emotion'])

if result_fr['name'] == 'not_found':
    TEXTPROXY.say(Dialog.name_question(gender))
    name_of_user = Functions.get_and_save_name(NAOIP, PORT, PASSWD, NAME, TEXTPROXY)
    img_id = result_fr['img_id']
    requests.get(BASE_API + '/addname/' + name_of_user + '/' + naoImage)
else:
    name_of_user = result_fr['name']
    img_id = result_fr['img_id']
    TEXTPROXY.say(Dialog.greeting_known_person(name_of_user, emotion))
    Functions.delete_user(NAOIP, PORT, BASE_API, PASSWD, NAME, TEXTPROXY, name_of_user, img_id)

manual_emotion_rating = Functions.manual_emotion(NAOIP, PORT, PASSWD, NAME, TEXTPROXY, name_of_user)

#Set action based on mood
Functions.action(MOTIONPROXY, POSTUREPROXY, TEXTPROXY, manual_emotion_rating, emotion, name_of_user)

# Line below needed?
# TEXTPROXY.say('Let me take another picture so I can see if your mood changed.')

#Take another picture to check if mood changed
result_ed, naoImage = Functions.emotionDetectionWithPic(NAOIP, PORT, BASE_API, TEXTPROXY, camera, resolution, colorSpace, images_folder)

emotion2 = str(result_ed[u'dominant_emotion'])

print('emotion before action: ' + emotion + ' emotion after action: ' +  emotion2 + ' manual emotion rating: ' + str(manual_emotion_rating))



#Convert emotions to integers
#Write function to save emotions before and after action and manual emotion rating into a file

Functions.emotionchange(emotion, emotion2, TEXTPROXY)

#DELETE USER?