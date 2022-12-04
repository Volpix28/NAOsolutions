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
from scipy.io.wavfile import write

#Costum dialogs
from dialog import Dialog
Dialog = Dialog()

#NAO Settings
from main import Connection_settings
Connection_settings = Connection_settings()

#NAO Settings
NAOIP = Connection_settings.NAOIP
PORT = Connection_settings.PORT
NAME = Connection_settings.NAME
passwd = Connection_settings.passwd
BASE_API = Connection_settings.BASE_API

tts = 'ALTextToSpeech'
text = ALProxy(tts, NAOIP, PORT)
text.setParameter("speed", 80)


class Functions:

    @staticmethod
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

    #Record Audio 
    @staticmethod
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
    @staticmethod
    def speech_recognition(remoteaudiofilepath):
        transport = paramiko.Transport((NAOIP, 22))
        transport.connect(username=NAME, password=passwd)
        print "Started Dialog..."
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

    ##########################
    # Name 2 Text Functiions #
    ##########################
    @staticmethod
    def record_name(NAOIP, PORT, record_name_time):
        text.say(Dialog.say_name)
        recording = Functions.record_audio(NAOIP, PORT, record_name_time)
        name_of_user = Functions.speech_recognition(recording)
        return name_of_user

    @staticmethod
    def name_loop(NAOIP, PORT, record_name_time, name_of_user):
        while name_of_user == None:
            text.say(Dialog.sorry_message[0])
            time.sleep(1)
            name_of_user = Functions.record_name(NAOIP, PORT, record_name_time)
            continue
        return name_of_user

    @staticmethod
    def confirm(NAOIP, PORT, record_confirm_time, name_of_user):
        text.say(Dialog.conformation_message_with_name(name_of_user))
        recording = Functions.record_audio(NAOIP, PORT, record_confirm_time)
        conformation = Functions.speech_recognition(recording)
        return conformation

    @staticmethod
    def confirm_loop(NAOIP, PORT, record_confirm_time, conformation, name_of_user):
        while conformation not in ["yes", "no"]:
            text.say(Dialog.sorry_message[0])
            time.sleep(1)
            text.say(Dialog.confirm_loop_with_name(name_of_user))
            recording = Functions.record_audio(NAOIP, PORT, record_confirm_time)
            conformation = Functions.speech_recognition(recording)
            continue
        return conformation

    @staticmethod
    def knowledgebase_entry(NAOIP, PORT, record_confirm_time, conformation, name_of_user):
        while conformation in ["yes", "no"]:
            if conformation == 'yes':
                text.say(Dialog.knownledge_base_entry(name_of_user))
                break

            elif conformation == 'no':
                text.say(Dialog.sorry_message[2])
                recording = Functions.record_audio(NAOIP, PORT, 5)
                name_of_user = Functions.speech_recognition(recording)

                name_of_user = Functions.name_loop(NAOIP, PORT, record_confirm_time, name_of_user)

                conformation = Functions.confirm(NAOIP, PORT, record_confirm_time, name_of_user)

                conformation = Functions.confirm_loop(NAOIP, PORT, record_confirm_time, conformation, name_of_user)

                continue
        return name_of_user

    # MEGA FUNCTION !!!!
    @staticmethod
    def get_and_save_name(NAOIP, PORT):
        name_of_user = Functions.record_name(NAOIP, PORT, 5)
        name_of_user = Functions.name_loop(NAOIP, PORT, 5, name_of_user)
        conformation = Functions.confirm(NAOIP, PORT, 3, name_of_user)
        conformation = Functions.confirm_loop(NAOIP, PORT, 3, conformation, name_of_user)
        final_name = Functions.knowledgebase_entry(NAOIP, PORT, 3, conformation, name_of_user)
        return final_name


    #########################
    # DELETE USER FUNCTIONS #
    #########################

    @staticmethod
    def deletion_recording(NAOIP, PORT, record_name_time):
        text.say(Dialog.user_deletion[0])
        recording = Functions.record_audio(NAOIP, PORT, record_name_time)
        conformation_delete_user = Functions.speech_recognition(recording)
        return conformation_delete_user

    @staticmethod
    def delete_confirm_loop(NAOIP, PORT, record_confirm_time, conformation_delete_user, name_of_user):
        while conformation_delete_user not in ["yes", "no"]:
            text.say(Dialog.confirm_user_deletion_loop(name_of_user))
            recording = Functions.record_audio(NAOIP, PORT, record_confirm_time)
            conformation_delete_user = Functions.speech_recognition(recording)
            print(conformation_delete_user)
            continue
        return conformation_delete_user

    @staticmethod
    def confirm_deletion(conformation_delete_user, img_id, name):
        if conformation_delete_user == 'yes':
            text.say(Dialog.user_deletion[1])
            #API
            requests.get(BASE_API + '/deleteperson/' + img_id)
            text.say(Dialog.user_deletion[2])
        else:
            text.say(Dialog.no_deletion(name))

    # MEGA FUNCTION
    @staticmethod
    def delete_user(name, img_id):
        user_deletion = Functions.deletion_recording(NAOIP, PORT, 2)
        user_deletion = Functions.delete_confirm_loop(NAOIP, PORT, 2, user_deletion, name)
        final_decision = Functions.confirm_deletion(user_deletion, img_id, name)
        return final_decision


    #############################
    # MANUAL EMOTION DETECTION #
    #############################

    @staticmethod
    def emotion_recording(NAOIP, PORT, record_name_time):
        text.say("Please rate your mood on a scale from 1 to 10. 10 means that you are happy!")
        recording = Functions.record_audio(NAOIP, PORT, record_name_time)
        emotion_rating = Functions.speech_recognition(recording)
        return emotion_rating

    @staticmethod
    def emotion_recording_loop(NAOIP, PORT, record_name_time, emotion_rating, name_of_user):
        while emotion_rating not in ["1", "2", "3", "4", "5", "6", "7", "8", "9", "10"]:
            text.say("Please, say a number from 1 to 10 " + name_of_user + '.')
            recording = Functions.record_audio(NAOIP, PORT, record_name_time)
            emotion_rating = Functions.speech_recognition(recording)
            continue
        return emotion_rating

    @staticmethod
    def confirm_emotion(NAOIP, PORT, record_confirm_time, emotion_rating, name_of_user):
        text.say('Thank you for the information, ' + name_of_user + '. You said, ' + emotion_rating + ', I am right?')
        recording = Functions.record_audio(NAOIP, PORT, record_confirm_time)
        conformation = Functions.speech_recognition(recording)
        return conformation

    @staticmethod
    def confirm_emotion_loop(NAOIP, PORT, record_confirm_time, conformation, emotion_rating, name_of_user):
        while conformation not in ["yes", "no"]:
            text.say(Dialog.sorry_message[0])
            time.sleep(1)
            text.say("Your Mood is on a scale from 1 to 10, " + emotion_rating + ". Please say, yes or no!")
            recording = Functions.record_audio(NAOIP, PORT, record_confirm_time)
            conformation = Functions.speech_recognition(recording)
            continue
        return conformation

    @staticmethod
    def final_rating(NAOIP, PORT, record_confirm_time, confirm_rating,emotion_rating, name_of_user):
        while confirm_rating in ["yes", "no"]:
            if confirm_rating == 'yes':
                text.say("Okay, thank you for the Information!")
                break

            elif confirm_rating == 'no':
                text.say("I am really sorry about that! Please rate your mood on a scale from 1 to 10.")
                recording = Functions.record_audio(NAOIP, PORT, 2)
                emotion_rating = Functions.speech_recognition(recording)
                emotion_rating = Functions.emotion_recording_loop(NAOIP, PORT, record_confirm_time, emotion_rating, name_of_user)
                confirm_rating = Functions.confirm_emotion(NAOIP, PORT, record_confirm_time, emotion_rating, name_of_user)
                confirm_rating = Functions.confirm_emotion_loop(NAOIP, PORT, record_confirm_time, confirm_rating, emotion_rating, name_of_user)
                continue

        emotion_rating = int(emotion_rating)
        return emotion_rating

    @staticmethod
    def manual_emotion(name_of_user):
        emotion_rating = Functions.emotion_recording(NAOIP, PORT, 2)
        emotion_rating = Functions.emotion_recording_loop(NAOIP, PORT, 2, emotion_rating, name_of_user)
        confirm_rating = Functions.confirm_emotion(NAOIP, PORT, 2, emotion_rating, name_of_user)
        confirm_rating = Functions.confirm_emotion_loop(NAOIP, PORT, 2, confirm_rating, emotion_rating, name_of_user)
        final_emotion_rating = Functions.final_rating(NAOIP, PORT, 2, confirm_rating, emotion_rating, name_of_user)
        return final_emotion_rating


    #############################
    # EMOTIONMATCHING FUNCTIONS #
    #############################

    #To-do: Check if it's possible to access entertainment/moods choreograph-functions in python // jokes
    @staticmethod
    def action(emotion_number, emotion, name_of_user):
        if emotion_number in [1,2,3,4,5]:
            if emotion == 'happy':
                text.say('You seem to be lying!')
                text.say(Dialog.random_joke(name_of_user))
                #action Confused?

            else:
                text.say('Let me try to cheer you up!')
                text.say(Dialog.random_joke(name_of_user))
                #action Saxophone?

        else:
            if emotion == 'happy':
                text.say('I am glad that you are in a good mood!')
                text.say(Dialog.random_joke(name_of_user))
                #action Excited?

            else:
                text.say('Hmm your expression earlier told me otherwise.')
                text.say(Dialog.random_joke(name_of_user))
                #action Confused?

    @staticmethod
    # To-Do: Create new elif statements
    #Caught all possible outcomes?
    def emotionchange(emotion, emotion2):
        negative = ['angry', 'disgust', 'fear', 'sad', 'surprised']
        neutral = ['neutral']
        positive = ['happy']
        if emotion in positive and emotion2 in positive:
            text.say('I am glad I could keep you happy.')
        
        elif emotion in positive and emotion2 not in positive:
            text.say('Looks like I made your mood worse. Sorry about that!')

        elif emotion in negative and emotion2 in negative or emotion in neutral and emotion2 in neutral:
            text.say('Looks like I could not change your mood.')

        elif emotion in negative or neutral and emotion2 in positive:
            text.say('I am glad I could brighten up your mood.')
