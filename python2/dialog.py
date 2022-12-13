import random

class Dialog:
    welcome = "Hi, I am NAO. I hope you are having a good day. For this experiment I will take pictures of you to recognize you and your emotion."
    say_name = "Please say your name now."
    sorry_message = ["Sorry, i didn't understand you, try again please!", "Sorry, i didn't understand you!", "Okay, i am sorry for that, please say your Name now."]
    confirmation_message = ["Your Name is ", " im right?", " Please say yes or no!", "Okay! ", " nice to meet you."]
    user_selection = ["Shall I delete your picture from my database? ", "Okay, that is a pity that I have to delete you now.", "I deleted you now."]
    emotion_recording = ["Please rate your mood on a scale from 1 to 10. 10 means that you are happy!", "Okay, thank you for the Information!", "I am really sorry about that! Please rate your mood on a scale from 1 to 10."]
    jokes = [
                "Why do pirates not take a shower when they walk the plank? They just wash up on shore.",
                "How do you drown a hipster? You throw him in the mainstream.",
                "What do you call a pony with a cough? A little horse.",
                "Why do bees have sticky hair? Because they use honeycombs.",
                "What are sharks two most favorite words? Man overboard!",
                "How does the ocean say hi? It waves!",
                "What kind of keys are sweet? Cookies!",
                "What is a computer's favorite snack? Computer chips.",
                "What is the most famous fish? A starfish!",
                "Where do fish sleep? In the riverbed."
                ]

    @staticmethod
    def experiment(name_of_user):
        return "Okay, " + name_of_user + " This is an experiment about emotion detection. To evaluate your state of emotion, please tell me how you feel today on a scale from one to ten."


    @staticmethod
    def confirmation_message_with_name(name_of_user):
        return Dialog.confirmation_message[0] + name_of_user + Dialog.confirmation_message[1]


    @staticmethod
    def confirm_loop_with_name(name_of_user):
        return Dialog.confirmation_message[0] + name_of_user + Dialog.confirmation_message[1] + Dialog.confirmation_message[2]


    @staticmethod
    def knownledge_base_entry(name_of_user):
        return Dialog.confirmation_message[3] + name_of_user + Dialog.confirmation_message[4]


    @staticmethod
    def confirm_user_deletion_loop(name_of_user):
        return Dialog.confirmation_message[2] + " " + name_of_user + " ."


    @staticmethod
    def no_deletion(name_of_user):
        return "Very good " + name_of_user + "! I will continue to recognise you and I hope it stays that way."


    @staticmethod
    def name_question(gender):
        return "Nice to meet you, you look like a beautiful " + gender + ". May I ask for your Name?"

    @staticmethod
    def greeting_known_person(name, emotion):
        return "Hey " + name + " long time no see!" + " You look rather " + emotion + " today."

    @staticmethod
    def invalid_emotion(name_of_user):
        return "Please, say a number from 1 to 10 " + name_of_user + '.'

    @staticmethod
    def emotion_confirmation(name_of_user, emotion_rating):
        return 'Thank you for the information, ' + name_of_user + '. You said, ' + emotion_rating + ', I am right?'
    
    @staticmethod
    def emotion_invalid_confirmation(emotion_rating):
        return "Your Mood is on a scale from 1 to 10, " + emotion_rating + ". Please say, yes or no!"

    @staticmethod
    def random_joke(name):
        secure_random = random.SystemRandom()
        joke = secure_random.choice(Dialog.jokes)
        return "Hey " + name + "! " + joke
