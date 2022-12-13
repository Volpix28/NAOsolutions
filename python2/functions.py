import time
import calendar
import requests
#IMPORTS
import os
import ast
import speech_recognition as sr
import paramiko

from PIL import Image  # works only in local env
from naoqi import ALProxy
from scipy.io.wavfile import write  # TODO: used?
from dialog import Dialog  # custom dialogs
from actions import Actions #costum Actions


def getTimestamp():
    return str(calendar.timegm(time.gmtime()))

class Functions:
    @staticmethod
    def emotionDetectionWithPic(NAOIP, PORT, BASE_API, text, camera, resolution, colorSpace, images_folder):
        naoImage = Functions.takePicture(NAOIP, PORT, camera, resolution, colorSpace, images_folder) 
        response_ed = requests.get(BASE_API + '/emotiondetection/' + naoImage)
        while response_ed.status_code != 200:
            text.say('Face not found.')
            os.remove(os.path.join(images_folder, naoImage))
            try: 
                naoImage = Functions.takePicture(NAOIP, PORT, camera, resolution, colorSpace, images_folder)
                response_ed = requests.get(BASE_API + '/emotiondetection/' + naoImage)
            except ValueError:
                print(response_ed)
        result_ed = ast.literal_eval(response_ed.json())
        return result_ed, naoImage

    @staticmethod
    def takePicture(IP, PORT, camera, resolution, colorSpace, location):
        camProxy = ALProxy('ALVideoDevice', IP, PORT)
        videoClient = camProxy.subscribeCamera('python_client', camera, resolution, colorSpace, 5)
        naoImage = camProxy.getImageRemote(videoClient)
        camProxy.unsubscribe(videoClient)
        imageName = 'image_' + getTimestamp() + '.png'
        im = Image.frombytes('RGB', (naoImage[0], naoImage[1]), naoImage[6]) # naoImage[0] = width, naoImage[1] = height, naoImage[6] = image data as ASCII char array
        im.save(location + os.sep + imageName, 'PNG')
        print('Image: ' + imageName + ' successfully saved @ ' + location)
        return imageName

    #Record Audio 
    @staticmethod
    def record_audio(NAOIP, PORT, t):
        recorderProxy = ALProxy('ALAudioRecorder', NAOIP, PORT)
        leds = ALProxy('ALLeds',NAOIP,PORT) # TODO: not used
        recorderProxy.stopMicrophonesRecording()
        nao_recordings_path = '/home/nao/nao_solutions/wavs/'
        # settings
        audioName = 'name_' + getTimestamp() + '.wav'
        remoteaudiofilepath = nao_recordings_path + audioName
        # configure channels
        # left, right, front rear (mics?)
        channels = (1, 0, 0, 0); # python tuple, C++ code uses AL:ALValue
        print('Started Dialog...')
        recorderProxy.startMicrophonesRecording('/home/nao/nao_solutions/wavs/' + audioName, 'wav', 16000, channels)
        # audio_file = recorderProxy.post.startMicrophonesRecording('/home/nao/nao_solutions/wavs/'+audioName, 'wav', 16000, channels)
        # leds.rotateEyes(0x000000FF,1,t)
        # continue recording for t seconds
        time.sleep(t)
        # stop recording
        recorderProxy.stopMicrophonesRecording()
        return remoteaudiofilepath


    @staticmethod # Speech2Text using google speech recognition
    def speech_recognition(remoteaudiofile, NAOIP, PASSWD, NAME):
        transport = paramiko.Transport((NAOIP, 22))
        transport.connect(username=NAME, password=PASSWD)
        sftp = transport.open_sftp_client()
        audio_file = sftp.open(remoteaudiofile)
        r = sr.Recognizer()
        with sr.AudioFile(audio_file) as file:
            audio_file = r.listen(file)
            try:
                # using google speech recognition
                text_data = str(r.recognize_google(audio_file))
                print('recognized text: ', text_data)
                return text_data
            except sr.UnknownValueError as uve:
                print('Error ', uve)
            finally:
                sftp.remove(remoteaudiofile)

    ##########################
    # Name 2 Text Functiions #
    ##########################
    @staticmethod
    def record_name(NAOIP, PORT, PASSWD, NAME, text, record_name_time):
        text.say(Dialog.say_name)
        recording = Functions.record_audio(NAOIP, PORT, record_name_time)
        name_of_user = Functions.speech_recognition(recording, NAOIP, PASSWD, NAME)
        return name_of_user

    @staticmethod
    def name_loop(NAOIP, PORT, PASSWD, NAME, text, record_name_time, name_of_user):
        while name_of_user == None:
            text.say(Dialog.sorry_message[0])
            time.sleep(1)
            name_of_user = Functions.record_name(NAOIP, PORT, PASSWD, NAME, text, record_name_time)
        return name_of_user

    @staticmethod
    def confirm(NAOIP, PORT, PASSWD, NAME, text, record_confirm_time, name_of_user):
        text.say(Dialog.confirmation_message_with_name(name_of_user))
        recording = Functions.record_audio(NAOIP, PORT, record_confirm_time)
        confirmation = Functions.speech_recognition(recording, NAOIP, PASSWD, NAME)
        while confirmation not in ['yes', 'no']:
            text.say(Dialog.sorry_message[0])
            time.sleep(1)
            text.say(Dialog.confirm_loop_with_name(name_of_user))
            recording = Functions.record_audio(NAOIP, PORT, record_confirm_time)
            confirmation = Functions.speech_recognition(recording, NAOIP, PASSWD, NAME)
        return confirmation

    @staticmethod
    def knowledgebase_entry(NAOIP, PORT, PASSWD, NAME, text, record_confirm_time, confirmation, name_of_user):
        while confirmation in ['yes', 'no']:
            if confirmation == 'yes':
                text.say(Dialog.knownledge_base_entry(name_of_user))
                break
            elif confirmation == 'no':
                text.say(Dialog.sorry_message[2])
                recording = Functions.record_audio(NAOIP, PORT, 5)
                name_of_user = Functions.speech_recognition(recording, NAOIP, PASSWD, NAME)
                name_of_user = Functions.name_loop(NAOIP, PORT, record_confirm_time, name_of_user)
                confirmation = Functions.confirm(NAOIP, PORT, record_confirm_time, name_of_user)
        return name_of_user

    # MEGA FUNCTION !!!!
    @staticmethod
    def get_and_save_name(NAOIP, PORT, PASSWD, NAME, text):
        name_of_user = Functions.record_name(NAOIP, PORT, PASSWD, NAME, text, 5)
        name_of_user = Functions.name_loop(NAOIP, PORT, PASSWD, NAME, text, 5, name_of_user)
        confirmation = Functions.confirm(NAOIP, PORT, PASSWD, NAME, text, 3, name_of_user)
        final_name = Functions.knowledgebase_entry(NAOIP, PORT, PASSWD, NAME, text, 3, confirmation, name_of_user)
        return final_name


    ########################
    # DELETE USER FUNCTION #
    ########################

    @staticmethod
    def delete_user(NAOIP, PORT, BASE_API, PASSWD, NAME, text, user_name, img_id):
        text.say(Dialog.user_selection[0])
        recording = Functions.record_audio(NAOIP, PORT, 2)
        user_selection = Functions.speech_recognition(recording, NAOIP, PASSWD, NAME)
        while user_selection not in ['yes', 'no', 'nope']:
            text.say(Dialog.confirm_user_deletion_loop(user_name))
            recording = Functions.record_audio(NAOIP, PORT, 2)
            user_selection = Functions.speech_recognition(recording, NAOIP, PASSWD, NAME)
            print('INFO delete_user() - user_selection: ', user_selection)
        if user_selection == 'yes':
            text.say(Dialog.user_selection[1])
            requests.get(BASE_API + '/deleteperson/' + img_id)
            text.say(Dialog.user_selection[2])
        else:
            text.say(Dialog.no_deletion(user_name))


    #############################
    # MANUAL EMOTION DETECTION #
    #############################

    @staticmethod
    def emotion_recording(NAOIP, PORT, PASSWD, NAME, text, record_name_time):
        text.say(Dialog.emotion_recording[0])
        recording = Functions.record_audio(NAOIP, PORT, record_name_time)
        emotion_rating = Functions.speech_recognition(recording, NAOIP, PASSWD, NAME)
        return emotion_rating

    @staticmethod
    def emotion_recording_loop(NAOIP, PORT, PASSWD, NAME, text, record_name_time, emotion_rating, name_of_user):
        while emotion_rating not in ['1', '2', '3', '4', '5', '6', '7', '8', '9', '10']: # TODO change to range(1,11)
            text.say(Dialog.invalid_emotion(name_of_user))
            recording = Functions.record_audio(NAOIP, PORT, record_name_time)
            emotion_rating = Functions.speech_recognition(recording, NAOIP, PASSWD, NAME)
        return emotion_rating

    @staticmethod
    def confirm_emotion(NAOIP, PORT, PASSWD, NAME, text, record_confirm_time, emotion_rating, name_of_user):
        text.say(Dialog.emotion_confirmation(name_of_user, emotion_rating))
        recording = Functions.record_audio(NAOIP, PORT, record_confirm_time)
        confirmation = Functions.speech_recognition(recording, NAOIP, PASSWD, NAME)
        return confirmation

    @staticmethod
    def confirm_emotion_loop(NAOIP, PORT, PASSWD, NAME, text, record_confirm_time, confirmation, emotion_rating):
        while confirmation not in ['yes', 'no']:
            text.say(Dialog.sorry_message[0])
            time.sleep(1)
            text.say(Dialog.emotion_invalid_confirmation(emotion_rating))
            recording = Functions.record_audio(NAOIP, PORT, record_confirm_time)
            confirmation = Functions.speech_recognition(recording, NAOIP, PASSWD, NAME)
        return confirmation

    @staticmethod
    def final_rating(NAOIP, PORT, PASSWD, NAME, text, record_confirm_time, confirm_rating,emotion_rating, name_of_user):
        while confirm_rating in ['yes', 'no']:
            if confirm_rating == 'yes':
                text.say(Dialog.emotion_recording[1])
                break
            elif confirm_rating == 'no':
                text.say(Dialog.emotion_recording[2])
                recording = Functions.record_audio(NAOIP, PORT, 2)
                emotion_rating = Functions.speech_recognition(recording, NAOIP, PASSWD, NAME)
                emotion_rating = Functions.emotion_recording_loop(NAOIP, PORT, PASSWD, NAME, record_confirm_time, emotion_rating, name_of_user)
                confirm_rating = Functions.confirm_emotion(NAOIP, PORT, PASSWD, NAME, record_confirm_time, emotion_rating, name_of_user)
                confirm_rating = Functions.confirm_emotion_loop(NAOIP, PORT, PASSWD, NAME, record_confirm_time, confirm_rating, emotion_rating, name_of_user)
        emotion_rating = int(emotion_rating)
        return emotion_rating

    @staticmethod
    def manual_emotion(NAOIP, PORT, PASSWD, NAME, text, name_of_user):
        emotion_rating = Functions.emotion_recording(NAOIP, PORT, PASSWD, NAME, text, 2)
        emotion_rating = Functions.emotion_recording_loop(NAOIP, PORT, PASSWD, NAME, text, 2, emotion_rating, name_of_user)
        confirm_rating = Functions.confirm_emotion(NAOIP, PORT, PASSWD, NAME, text, 2, emotion_rating, name_of_user)
        confirm_rating = Functions.confirm_emotion_loop(NAOIP, PORT, PASSWD, NAME, text, 2, confirm_rating, emotion_rating)
        final_emotion_rating = Functions.final_rating(NAOIP, PORT, PASSWD, NAME, text, 2, confirm_rating, emotion_rating, name_of_user)
        return final_emotion_rating


    #############################
    # EMOTIONMATCHING FUNCTIONS #
    #############################

    # TODO Check if it's possible to access entertainment/moods choreograph-functions in python // jokes
    @staticmethod
    def action(MOTIONPROXY, POSTUREPROXY, text, emotion_number, emotion, name_of_user):
        if emotion_number in range(1,6):
            if emotion in ['happy', 'surprised']:
                text.say('You seem to be lying! ')
                text.say(Dialog.random_joke(name_of_user))
                # action Confused?
                Actions.hulahoop(MOTIONPROXY, POSTUREPROXY)
            else:
                text.say('Let me try to cheer you up! ')
                text.say(Dialog.random_joke(name_of_user))
                # action Hulahup?
                # hulahoop(NAOIP, PORT)
                Actions.dance(MOTIONPROXY)
        else:
            if emotion in ['happy', 'surprised']:
                text.say('I am glad that you are in a good mood! ')
                text.say(Dialog.random_joke(name_of_user))
                # action Excited?
                # hulahoop(NAOIP, PORT)
                Actions.dance(MOTIONPROXY)
            else:
                text.say('Hmm your expression earlier told me otherwise. ')
                text.say(Dialog.random_joke(name_of_user))
                # action Confused?
                Actions.hulahoop(MOTIONPROXY, POSTUREPROXY)
                

    @staticmethod
    # TODO: Create new elif statements - caught all possible outcomes?
    def emotionchange(emotion, emotion2, text):
        negative = ['angry', 'disgust', 'fear', 'sad']
        neutral = ['neutral']
        positive = ['happy', 'surprised']
        if emotion in positive and emotion2 in positive:
            text.say('I am glad I could keep you happy.')
        elif emotion in positive and emotion2 not in positive:
            text.say('Looks like I made your mood worse. Sorry about that!')
        elif emotion in negative and emotion2 in negative or emotion in neutral and emotion2 in neutral:
            text.say('Looks like I could not change your mood.')
        elif emotion in negative or neutral and emotion2 in positive:
            text.say('I am glad I could brighten up your mood.')