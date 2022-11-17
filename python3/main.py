from flask import Flask
from flask_restful import Api, Resource
from deepface import DeepFace
import pandas as pd
import os
import json

app = Flask(__name__)
api = Api(app)

fileshare = os.listdir(r'C:\Users\alexa\Desktop\FH\5. Semester\Projekt\rest_api_tut\fileshare')
knowledge_base = os.listdir(r'C:\Users\alexa\Desktop\FH\5. Semester\Projekt\rest_api_tut\knowledge_base') # knowledge_base

# Functions
def moveFile(source, dest):
    """
    Move single file from source to destination. 
    source: filepath + filename 
    dest: new filepath + (new) filename
    """
    try:
        os.rename(source, dest)
        print(f'Successfully moved File from \"{source}\" to \"{dest}\"')
    except FileNotFoundError as err:
        print(f'ERROR: {err}')


class EmotionDetection(Resource): # Inherit from Resource
    def get(self, img_name): #overwrite get()
        obj = DeepFace.analyze(img_path = f'img/{img_name}', actions = ['gender', 'emotion'])
        return obj # has to be serializable


'''
todo: 
- create more functions for better readability
- clean fileshare afterwards:
                        2 events possible:
                            - person is already knwon and in "names_img" --> delete picture after processing
                            - person is not known, then after name is stored, move picture to names_img
'''

class FaceRecognition(Resource):
    def get(self, img_name):   
        for img in knowledge_base: # FaceRecognicion
            result = DeepFace.verify(img1_path = f'img/{img_name}', img2_path = f'names_img/{img}')
            print(f'Result JSON:\n{result}')
            if result['verified'] == True:
                df = pd.read_csv('names.csv')
                df = df[df['IMG'] == f'{img}']
                name = {'name':df['NAME'].to_string(header=False, index=False)}
                json_object = json.dumps(name, indent = 4) 
                print(f'json_object:\n{json_object}') 
                return json_object
        name = {'name':'not found'}
        json_object = json.dumps(name, indent = 4)
        return json_object

'''
todo:
- move img when name is recognized to names_img
'''

class AddName(Resource):
    def get(self, name, img_name):   
        df = pd.read_csv('names.csv')
        new_entry = {'IMG' : img_name, 'NAME': name}
        df = df.append(new_entry, ignore_index=True)
        df.to_csv('names.csv', index=False)
        # Move img to dir with known names
        # moveFile()
        return {'data': 'Posted'}

# add this resource to the api and make it acessable through URL
api.add_resource(EmotionDetection, "/emotiondetection/<string:img_name>") # add parameters with /<int:test>/...
api.add_resource(FaceRecognition, "/facerecognition/<string:img_name>")
api.add_resource(AddName, "/addname/<string:name>/<string:img_name>")



if __name__ == "__main__":
    app.run(host='0.0.0.0', debug=True)