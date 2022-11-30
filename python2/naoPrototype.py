# Imports
import time
import calendar
import requests
import os
import ast
import speech_recognition as sr
import paramiko
# Python Image Library
from PIL import Image # works only in local env
from naoqi import ALProxy
from dialog import Dialog
from scipy.io.wavfile import write
Dialog = Dialog()


# Connection settings
NAOIP = '192.168.0.242'
PORT = 9559
NAME = "nao"
passwd = "19981"
BASE_API = 'http://192.168.0.213:5000'

# Connection for paramiko
transport = paramiko.Transport((NAOIP, 22))
transport.connect(username=NAME, password=passwd)
print "Connected to transport......."

# Test
tts = 'ALTextToSpeech'
text = ALProxy(tts, NAOIP, PORT)
text.setParameter("speed", 80)


# NAO picture config
camera = 0 # 0 = top camera, 1 = bottom camera
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

########################################

#Record Audio 
def record_audio(NAOIP, PORT, t):
    recorderProxy = ALProxy("ALAudioRecorder", NAOIP, PORT)
    leds = ALProxy("ALLeds",NAOIP,PORT)
    recorderProxy.stopMicrophonesRecording()
    nao_recordings_path = "/home/nao/nao_solutions/wavs/"
    
    #settings
    time_stamp = str(calendar.timegm(time.gmtime()))
    audioName = r'name_' + time_stamp + r'.wav'
    remoteaudiofilepath = nao_recordings_path+audioName

    # configure channels
    # left, right, front rear (mics?)
    channels = (1, 0, 0, 0); # python tuple, C++ code uses AL:ALValue
    audio_file = recorderProxy.startMicrophonesRecording("/home/nao/nao_solutions/wavs/"+audioName, "wav", 16000, channels)
    #audio_file = recorderProxy.post.startMicrophonesRecording("/home/nao/nao_solutions/wavs/"+audioName, "wav", 16000, channels)
    #leds.rotateEyes(0x000000FF,1,t)
    # continue recording for t seconds
    time.sleep(t)

    # stop recording
    recorderProxy.stopMicrophonesRecording()
    
    return remoteaudiofilepath


#Speech2Text
def speech_recognition(remoteaudiofilepath):
    
    sftp = transport.open_sftp_client()
    audio_file = sftp.open(remoteaudiofilepath)

    r = sr.Recognizer()
    with sr.AudioFile(audio_file) as file:
        audio_file = r.listen(file)
        try:
            # using google speech recognition
            text_data = str(r.recognize_google(audio_file))
            #print('Converting audio transcripts into text ...')
            #print(text_data)
            sftp.remove(remoteaudiofilepath)
            return text_data
        except sr.UnknownValueError:
            sftp.remove(remoteaudiofilepath)


def record_name(NAOIP, PORT, record_name_time):
    text.say(Dialog.say_name)
    recording = record_audio(NAOIP, PORT, record_name_time)
    name_of_user = speech_recognition(recording)
    return name_of_user


def name_loop(NAOIP, PORT, record_name_time, name_of_user):
    while name_of_user == None:
        text.say(Dialog.sorry_message[0])
        time.sleep(1)
        name_of_user = record_name(NAOIP, PORT, record_name_time)
        continue
    return name_of_user


def confirm(NAOIP, PORT, record_confirm_time, name_of_user):
    text.say(Dialog.conformation_message_with_name(name_of_user))
    recording = record_audio(NAOIP, PORT, record_confirm_time)
    conformation = speech_recognition(recording)
    return conformation


def confirm_loop(NAOIP, PORT, record_confirm_time, conformation, name_of_user):
    while conformation not in ["yes", "no"]:
        text.say(Dialog.sorry_message[0])
        time.sleep(1)
        text.say(Dialog.confirm_loop_with_name(name_of_user))
        recording = record_audio(NAOIP, PORT, record_confirm_time)
        conformation = speech_recognition(recording)
        continue
    return conformation


def knowledgebase_entry(NAOIP, PORT, record_confirm_time, conformation, name_of_user):
    while conformation in ["yes", "no"]:
        if conformation == 'yes':
            text.say(Dialog.knownledge_base_entry(name_of_user))
            break

        elif conformation == 'no':
            text.say(Dialog.sorry_message[2])
            recording = record_audio(NAOIP, PORT, 5)
            name_of_user = speech_recognition(recording)

            name_of_user = name_loop(NAOIP, PORT, record_confirm_time, name_of_user)

            conformation = confirm(NAOIP, PORT, record_confirm_time, name_of_user)

            conformation = confirm_loop(NAOIP, PORT, record_confirm_time, conformation, name_of_user)

            continue
    return name_of_user

# MEGA FUNCTION !!!!
def get_and_save_name(NAOIP, PORT):
    name_of_user = record_name(NAOIP, PORT, 5)
    name_of_user = name_loop(NAOIP, PORT, 5, name_of_user)
    conformation = confirm(NAOIP, PORT, 3, name_of_user)
    conformation = confirm_loop(NAOIP, PORT, 3, conformation, name_of_user)
    final_name = knowledgebase_entry(NAOIP, PORT, 3, conformation, name_of_user)
    return final_name

#########################
# DELETE USER FUNCTIONS #
#########################

def deletion_recording(NAOIP, PORT, record_name_time):
    text.say(Dialog.user_deletion[0])
    recording = record_audio(NAOIP, PORT, record_name_time)
    conformation_delete_user = speech_recognition(recording)
    return conformation_delete_user

def delete_confirm_loop(NAOIP, PORT, record_confirm_time, conformation_delete_user, name_of_user):
    while conformation_delete_user not in ["yes", "no"]:
        text.say(Dialog.confirm_user_deletion_loop(name_of_user))
        recording = record_audio(NAOIP, PORT, record_confirm_time)
        conformation_delete_user = speech_recognition(recording)
        print(conformation_delete_user)
        continue
    return conformation_delete_user

def confirm_deletion(conformation_delete_user, img_id, name):
    if conformation_delete_user == 'yes':
        text.say(Dialog.user_deletion[1])
        #API
        requests.get(BASE_API + '/deleteperson/' + img_id)
        text.say(Dialog.user_deletion[2])
    else:
        text.say(Dialog.no_deletion(name))

# MEGA FUNCTION
def delete_user(name, img_id):
    user_deletion = deletion_recording(NAOIP, PORT, 2)
    user_deletion = delete_confirm_loop(NAOIP, PORT, 2, user_deletion, name)
    final_decision = confirm_deletion(user_deletion, img_id, name)
    return final_decision


#############################
# MANUAL EMOTION DETECTION #
#############################

def emotion_recording(NAOIP, PORT, record_name_time):
    text.say("Please rate your mood on a scale from 1 to 10. 10 means that you are happy!")
    recording = record_audio(NAOIP, PORT, record_name_time)
    emotion_rating = speech_recognition(recording)
    return emotion_rating

def emotion_recording_loop(NAOIP, PORT, record_name_time, emotion_rating, name_of_user):
    while emotion_rating not in ["1", "2", "3", "4", "5", "6", "7", "8", "9", "10"]:
        text.say("Please, say a number from 1 to 10 " + name_of_user + '.')
        recording  = record_audio(NAOIP, PORT, record_name_time)
        emotion_rating = speech_recognition(recording)
        continue
    return emotion_rating


def confirm_emotion(NAOIP, PORT, record_confirm_time, emotion_rating, name_of_user):
    text.say('Thank you for the information, ' + name_of_user + '. You said, ' + emotion_rating + ', I am right?')
    recording = record_audio(NAOIP, PORT, record_confirm_time)
    conformation = speech_recognition(recording)
    return conformation


def confirm_emotion_loop(NAOIP, PORT, record_confirm_time, conformation, emotion_rating, name_of_user):
    while conformation not in ["yes", "no"]:
        text.say(Dialog.sorry_message[0])
        time.sleep(1)
        text.say("Your Mood is on a scale from 1 to 10, " + emotion_rating + ". Please say, yes or no!")
        recording = record_audio(NAOIP, PORT, record_confirm_time)
        conformation = speech_recognition(recording)
        continue
    return conformation


def final_rating(NAOIP, PORT, record_confirm_time, confirm_rating,emotion_rating, name_of_user):
    while confirm_rating in ["yes", "no"]:
        if confirm_rating == 'yes':
            text.say("Okay, thank you for the Information!")
            break

        elif confirm_rating == 'no':
            text.say("I am really sorry about that! Please rate your mood on a scale from 1 to 10.")
            recording = record_audio(NAOIP, PORT, 2)
            emotion_rating = speech_recognition(recording)
            emotion_rating = emotion_recording_loop(NAOIP, PORT, record_confirm_time, emotion_rating, name_of_user)
            confirm_rating = confirm_emotion(NAOIP, PORT, record_confirm_time, emotion_rating, name_of_user)
            confirm_rating = confirm_emotion_loop(NAOIP, PORT, record_confirm_time, confirm_rating, emotion_rating, name_of_user)
            continue

    emotion_rating = int(emotion_rating)
    return emotion_rating

def manual_emotion(name_of_user):
    emotion_rating = emotion_recording(NAOIP, PORT, 2)
    emotion_rating = emotion_recording_loop(NAOIP, PORT, 2, emotion_rating, name_of_user)
    confirm_rating = confirm_emotion(NAOIP, PORT, 2, emotion_rating, name_of_user)
    confirm_rating = confirm_emotion_loop(NAOIP, PORT, 2, confirm_rating, emotion_rating, name_of_user)
    final_emotion_rating = final_rating(NAOIP, PORT, 2, confirm_rating, emotion_rating, name_of_user)
    return final_emotion_rating


#############################
# EMOTIONMATCHING FUNCTIONS #
#############################

#To-do: Check if it's possible to access entertainment/moods choreograph-functions in python

def action(emotion_number):
    if emotion_number in [1,2,3,4,5]:
        if emotion == 'happy':
            text.say('You seem to be lying!')
            #action Confused

        else:
            text.say('Let me try to cheer you up!')
            #action Saxophone

    else:
        if emotion == 'happy':
            text.say('I am glad that you are in a good mood!')
            #action Excited

        else:
            text.say('Hmm your expression earlier told me otherwise.')
            #action Confused

def emotionchange(emotion, emotion2):
    if emotion == 'happy' and emotion2 == 'happy':
        text.say('I am glad I could keep you happy.')
    
    elif emotion == 'happy' and emotion2 is not 'happy':
        text.say('Looks like I made your mood worse. Sorry about that!')

    #elif needed or does else catch all the other outcomes?
    else:
        text.say('I am glad I could increase your mood.')


##########################
# START OF CONVERSATION #
##########################

text.say(Dialog.welcome)
naoImage = takePicture(NAOIP, PORT, camera, resolution, colorSpace, 'fileshare/images') 
time.sleep(2)
response_ed = requests.get(BASE_API + '/emotiondetection/' + naoImage)
result_ed = ast.literal_eval(response_ed.json())
while result_ed['dominant_emotion'] == 'face_not_found':
    # TO-DO: delete old naoImage from fileshare
    text.say('Face not found.')
    naoImage = takePicture(NAOIP, PORT, camera, resolution, colorSpace, 'fileshare/images')
    response_ed = requests.get(BASE_API + '/emotiondetection/' + naoImage)
    result_ed = ast.literal_eval(response_ed.json())
    
response_fr = requests.get(BASE_API + '/facerecognition/' + naoImage)
result_fr = ast.literal_eval(response_fr.json())
gender = str(result_ed[u'gender'])
emotion = str(result_ed[u'dominant_emotion'])

if result_fr['name'] == 'not_found':
    text.say(Dialog.name_question(gender))
    name = get_and_save_name(NAOIP, PORT)
    img_id = result_fr['img_id']
    requests.get(BASE_API + '/addname/' + name + '/' + naoImage)
else:
    name = result_fr['name']
    img_id = result_fr['img_id']
    text.say(Dialog.greeting_known_person(name, emotion))
    delete_user(name, img_id)

manual_emotion_rating = manual_emotion(name)

#Set action based on mood
action(manual_emotion_rating)

# Line below needed?
# text.say('Let me take another picture so I can see if your mood changed.')

#Take another picture to check if mood changed
#Change variable names or no need?
naoImage = takePicture(NAOIP, PORT, camera, resolution, colorSpace, 'fileshare/images') 

#Emotion detection
response_ed = requests.get(BASE_API + '/emotiondetection/' + naoImage)
result_ed = ast.literal_eval(response_ed.json())
while result_ed['dominant_emotion'] == 'face_not_found':
    # TO-DO: delete old naoImage from fileshare
    text.say('Face not found.')
    naoImage = takePicture(NAOIP, PORT, camera, resolution, colorSpace, 'fileshare/images')
    response_ed = requests.get(BASE_API + '/emotiondetection/' + naoImage)
    result_ed = ast.literal_eval(response_ed.json())

emotion2 = str(result_ed[u'dominant_emotion'])

print('emotion before action: ' + emotion + ' emotion after action: ' +  emotion2 + ' manual emotion rating: ' + str(manual_emotion_rating))

emotionchange(emotion, emotion2)



#DELETE USER?


