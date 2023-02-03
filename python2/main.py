'''
MAIN SCRIPT
'''

# Imports:
import requests
import os
import ast
import time
from naoqi import ALProxy
from scipy.io.wavfile import write
from csv import writer
from dialog import Dialog  # custom dialogs
from functions import Functions  # custom functions

# Connection settings:
# Change this, when u are in a different network!
NAOIP = '192.168.0.242' 
PORT = 9559
NAME = "nao"
PASSWD = "19981"
BASE_API = 'http://192.168.0.213:5000'

# Proxies
# Proxy for Text2Speech 
TEXTPROXY = ALProxy('ALTextToSpeech', NAOIP, PORT)
TEXTPROXY.setParameter("speed", 85) #talk slower 0-100

POSTUREPROXY = ALProxy('ALRobotPosture', NAOIP, PORT) #Posture proxy
MOTIONPROXY = ALProxy('ALMotion', NAOIP, PORT) # Motion proxy
SOUNDPROXY = ALProxy("ALAudioPlayer", NAOIP, PORT) # Play sound on NAO
MANAGERPROXY = ALProxy("ALBehaviorManager", NAOIP, PORT) # Behavior proxy


#Set path to fileshare --> dynamic
fileshare = os.path.join(os.getcwd(), 'fileshare')
images_folder = os.path.join(fileshare, 'images')
runs = os.path.join(fileshare, 'runs.csv')

# default for data storing 
data_save_approval = True

# NAO picture config
camera = 0 # 0 = top camera, 1 = bottom camera
resolution = 3 # 0 = QQVGA, 1 = QVGA, 2 = VGA
colorSpace = 11 # http://doc.aldebaran.com/2-5/family/robots/video_robot.html#cameracolorspace-mt9m114


##########################
# START OF CONVERSATION #
##########################
time.sleep(3) # Time sleep 3 seconds
TEXTPROXY.say(Dialog.welcome)# welcome speech from Dialog.py

result_ed, naoImage = Functions.emotionDetectionWithPic(NAOIP, PORT, BASE_API, TEXTPROXY, camera, resolution, colorSpace, images_folder) #make picture and emotion detection

response_fr = requests.get(BASE_API + '/facerecognition/' + naoImage) #API Call for face recognition
result_fr = ast.literal_eval(response_fr.json()) # cast result
gender = str(result_ed[u'gender']) # get gender from user
emotion_before_action = str(result_ed[u'dominant_emotion']) # get emotion from user
img_id = result_fr['img_id'] # get img_id

# Unknown User:
if result_fr['name'] == 'not_found':
    TEXTPROXY.say(Dialog.name_question(gender)) # Ask for User name
    name_of_user = Functions.get_and_save_name(NAOIP, PORT, PASSWD, NAME, TEXTPROXY) #get user name
    data_save_approval = Functions.data_saving(NAOIP, PORT, BASE_API, PASSWD, NAME, TEXTPROXY, name_of_user, naoImage, data_save_approval) # get user approval

# Known User:
else:
    name_of_user = result_fr['name'] # get name of user
    TEXTPROXY.say(Dialog.greeting_known_person(name_of_user, emotion_before_action)) # Dialog 
    data_save_approval = Functions.delete_user(NAOIP, PORT, BASE_API, PASSWD, NAME, TEXTPROXY, name_of_user, img_id, data_save_approval) # When user said yes picture will be deleted
    
print('\nUser approved storing data: ' + str(data_save_approval))
user_numeric_emotion = Functions.manual_emotion(NAOIP, PORT, PASSWD, NAME, TEXTPROXY, name_of_user) # Manual emotion recognition // 0-10

#Set action based on mood
Functions.action(MOTIONPROXY, POSTUREPROXY, SOUNDPROXY, MANAGERPROXY, TEXTPROXY, user_numeric_emotion, emotion_before_action, name_of_user) #NAO makes an action

# Take another picture to check if mood changed
result_ed, naoImage = Functions.emotionDetectionWithPic(NAOIP, PORT, BASE_API, TEXTPROXY, camera, resolution, colorSpace, images_folder) # make new picture

emotion_after_action = str(result_ed[u'dominant_emotion']) # store result

Functions.emotionchange(emotion_before_action, emotion_after_action, TEXTPROXY) # NAO say sth

print('emotion before action: ' + emotion_before_action + ' emotion after action: ' +  emotion_after_action + ' manual emotion rating: ' + str(user_numeric_emotion))

# save data
if data_save_approval == True:
    add = [emotion_before_action, emotion_after_action, user_numeric_emotion, gender]
    with open(runs, 'a') as f_object:
        writer_object = writer(f_object)
        writer_object.writerow(add)
        f_object.close()

# Clean session after every sucsessful session
requests.get(BASE_API + '/cleansession')