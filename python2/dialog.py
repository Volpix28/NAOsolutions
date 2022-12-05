import random

class Dialog:
    welcome = "Hi, I am NAO. I hope you are having a good day."
    say_name = "Please say your name now."
    sorry_message = ["Sorry, i didn't understand you, try again please!", "Sorry, i didn't understand you!", "Okay, i am sorry for that, please say your Name now."]
    conformation_message = ["Your Name is ", " im right?", " Please say yes or no!", "Okay! ", " I will enter your Name into the knowledge data base."]
    user_deletion = ["Shall I delete your picture from my database? ", "Okay, that is a pity that I have to delete you now.", "I deleted you now."]

    @staticmethod
    def experiment(name_of_user):
        return "Okay, " + name_of_user + " This is an experiment about emotion detection. To evaluate your state of emotion, please tell me how you feel today on a scale from one to ten."


    @staticmethod
    def conformation_message_with_name(name_of_user):
        return Dialog.conformation_message[0] + name_of_user + Dialog.conformation_message[1]


    @staticmethod
    def confirm_loop_with_name(name_of_user):
        return Dialog.conformation_message[0] + name_of_user + Dialog.conformation_message[1] + Dialog.conformation_message[2]


    @staticmethod
    def knownledge_base_entry(name_of_user):
        return Dialog.conformation_message[3] + name_of_user + Dialog.conformation_message[4]


    @staticmethod
    def confirm_user_deletion_loop(name_of_user):
        return Dialog.conformation_message[2] + " " + name_of_user + " ."


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
    def random_joke(name):
        jokes = [
                "Why do pirates not take a shower when they walk the plank? They just wash up on shore.",
                "How do you drown a hipster? You throw him in the mainstream.",
                "What do you call a pony with a cough? A little horse.",
                "Why do bees have sticky hair? Because they use honeycombs.",
                "What are sharks two most favorite words? Man overboard!"
                ]
        secure_random = random.SystemRandom()
        joke = secure_random.choice(jokes)
        return "Hey " + name + "! " + joke
