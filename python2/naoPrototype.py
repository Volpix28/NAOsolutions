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
text.say('Testrun')

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

naoImage = takePicture(NAOIP, PORT, camera, resolution, colorSpace, 'fileshare/images') # TODO set fileshare param to standard location 

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
    channels = (0, 0, 1, 0); # python tuple, C++ code uses AL:ALValue
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
    text.say(Dialog.conformation_message[0] + name_of_user + Dialog.conformation_message[1])
    recording = record_audio(NAOIP, PORT, record_confirm_time)
    conformation = speech_recognition(recording)
    return conformation


def confirm_loop(NAOIP, PORT, record_confirm_time, sorry_message, conformation, name_of_user):
    while conformation not in ["yes", "no"]:
        text.say(Dialog.sorry_message[sorry_message])
        time.sleep(1)
        text.say(Dialog.conformation_message[0] + name_of_user + Dialog.conformation_message[1] + Dialog.conformation_message[2])
        recording = record_audio(NAOIP, PORT, record_confirm_time)
        conformation = speech_recognition(recording)
        continue
    return conformation


def knowledgebase_entry(NAOIP, PORT, record_confirm_time, sorry_message, conformation, name_of_user):
    while conformation in ["yes", "no"]:
        if conformation == 'yes':
            text.say(Dialog.conformation_message[3] + name_of_user + Dialog.conformation_message[4])
            # API REQUEST add name 
            break

        elif conformation == 'no':
            text.say(Dialog.sorry_message[2])
            recording = record_audio(NAOIP, PORT, 5)
            name_of_user = speech_recognition(recording)

            name_of_user = name_loop(NAOIP, PORT, record_confirm_time, name_of_user)

            conformation = confirm(NAOIP, PORT, record_confirm_time, name_of_user)

            conformation = confirm_loop(NAOIP, PORT, record_confirm_time, sorry_message, conformation, name_of_user)

            continue
    return name_of_user

# MEGA FUNCTION !!!!
def get_and_save_name(NAOIP, PORT):
    name_of_user = record_name(NAOIP, PORT, 5)
    name_of_user = name_loop(NAOIP, PORT, 5, name_of_user)
    conformation = confirm(NAOIP, PORT, 3, name_of_user)
    conformation = confirm_loop(NAOIP, PORT, 3, 0, conformation, name_of_user)
    final_name = knowledgebase_entry(NAOIP, PORT, 3, 0, conformation, name_of_user)
    return final_name

#########################################################



# Filler
text.say('I hope you are having a good day.')

response_fr = requests.get(BASE_API + '/facerecognition/' + naoImage) # .get, .post
response_ed = requests.get(BASE_API + '/emotiondetection/' + naoImage)
result_ed = response_ed.json()
result_fr = ast.literal_eval(response_fr.json())
gender = str(result_ed[u'gender'])
emotion = str(result_ed[u'dominant_emotion'])
print(emotion, gender)
if result_fr['name'] == 'not found':
    text.say(
      'Nice to meet you, you look like a beautiful ' + gender \
      + ' and you seem to be ' + emotion \
      + ' May I ask for your Name?'
      )
    # say your name now: 
    name = get_and_save_name(NAOIP, PORT)
    # API Call addName
    requests.get(BASE_API + '/addname/' + name + '/' + naoImage)
else:
    text.say(
      'Hey ' + result_fr['name'] + ' long time no see!'\
      + ' You look rather ' + emotion \
      + ' today.')

#Set action for known person
#text.say('Nice to meet you again.')
#text.say(name)
#text.say('Hope you are having a good day.')

#Get response from API for gender and mood


#Set action based on mood


#Take another picture to check if mood changed


#Emotion detection
