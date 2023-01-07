import requests
import os
import ast
from naoqi import ALProxy
from scipy.io.wavfile import write
from csv import writer
from dialog import Dialog  # custom dialogs
from functions import Functions  # custom functions


# Connection settings
NAOIP = '10.0.0.14' 
PORT = 9559
NAME = "nao"
PASSWD = "19981"
BASE_API = 'http://10.0.0.12:5000'

# Proxy
TEXTPROXY = ALProxy('ALTextToSpeech', NAOIP, PORT)
TEXTPROXY.setParameter("speed", 85)

POSTUREPROXY = ALProxy('ALRobotPosture', NAOIP, PORT)
MOTIONPROXY = ALProxy('ALMotion', NAOIP, PORT)
SOUNDPROXY = ALProxy("ALAudioPlayer", NAOIP, PORT)
MANAGERPROXY = ALProxy("ALBehaviorManager", NAOIP, PORT)

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

TEXTPROXY.say(Dialog.welcome)
result_ed, naoImage = Functions.emotionDetectionWithPic(NAOIP, PORT, BASE_API, TEXTPROXY, camera, resolution, colorSpace, images_folder)
    
response_fr = requests.get(BASE_API + '/facerecognition/' + naoImage)
result_fr = ast.literal_eval(response_fr.json())
gender = str(result_ed[u'gender'])
emotion_before_action = str(result_ed[u'dominant_emotion'])
img_id = result_fr['img_id']

if result_fr['name'] == 'not_found':
    TEXTPROXY.say(Dialog.name_question(gender))
    name_of_user = Functions.get_and_save_name(NAOIP, PORT, PASSWD, NAME, TEXTPROXY)
    # if answer is yes:
    data_save_approval = Functions.data_saving(NAOIP, PORT, BASE_API, PASSWD, NAME, TEXTPROXY, name_of_user, naoImage, data_save_approval)
else:
    name_of_user = result_fr['name']
    TEXTPROXY.say(Dialog.greeting_known_person(name_of_user, emotion_before_action))
    data_save_approval = Functions.delete_user(NAOIP, PORT, BASE_API, PASSWD, NAME, TEXTPROXY, name_of_user, img_id, data_save_approval)
    
print('\nUser approved storing data: ' + str(data_save_approval))
user_numeric_emotion = Functions.manual_emotion(NAOIP, PORT, PASSWD, NAME, TEXTPROXY, name_of_user)

#Set action based on mood
Functions.action(MOTIONPROXY, POSTUREPROXY, SOUNDPROXY, MANAGERPROXY, TEXTPROXY, user_numeric_emotion, emotion_before_action, name_of_user)

# Line below needed?
# TEXTPROXY.say('Let me take another picture so I can see if your mood changed.')

# Take another picture to check if mood changed
result_ed, naoImage = Functions.emotionDetectionWithPic(NAOIP, PORT, BASE_API, TEXTPROXY, camera, resolution, colorSpace, images_folder)

emotion_after_action = str(result_ed[u'dominant_emotion'])

# Convert emotions to integers
# Write function to save emotions before and after action and manual emotion rating into a file

Functions.emotionchange(emotion_before_action, emotion_after_action, TEXTPROXY)

print('emotion before action: ' + emotion_before_action + ' emotion after action: ' +  emotion_after_action + ' manual emotion rating: ' + str(user_numeric_emotion))

if data_save_approval == True:
    add = [emotion_before_action, emotion_after_action, user_numeric_emotion, gender]
    with open(runs, 'a') as f_object:
        writer_object = writer(f_object)
        writer_object.writerow(add)
        f_object.close()

# Clean session
requests.get(BASE_API + '/cleansession')