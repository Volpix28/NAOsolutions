from flask import Flask
from flask_restful import Api, Resource
from deepface import DeepFace
from functools import partial
import pandas as pd
import os
import json


def moveFile(source, dest):
    '''
    Move single file from source to destination.
    source: filepath + filename 
    dest: new filepath + (new) filename
    '''
    try:
        os.rename(source, dest)
        print(f'Successfully moved File from \"{source}\" to \"{dest}\"')
    except FileNotFoundError as err:
        print(f'ERROR: {err}')

def createFolders(dir, subfolders):
    '''
    Creates one or more directories if not existent.
    dir: absolute path
    subfolders: name(s) of folder(s)
    '''
    concat_path = partial(os.path.join, dir) # creates local temp function to map each concatenated subfolder
    for subfolder in map(concat_path, subfolders): 
        os.makedirs(subfolder, exist_ok=True)

def createNamesCsv(dir):
    '''
    Creates names.csv file with column header.
    '''
    file_name = dir + os.sep + 'names.csv'
    if os.path.exists(file_name):
        print('INFO - createNamesCsv: names.csv already exists')
    else:
        df = pd.DataFrame(columns=['IMG','NAME'])
        df.to_csv(file_name, index=False)
        print('INFO - createNamesCsv: names.csv created')


app = Flask(__name__)
api = Api(app)

# create fileshare with 'images' and 'knowledge_base' subfolder if not existent
createFolders('fileshare', ['images', 'knowledge_base'])
fileshare = os.path.join(os.getcwd(), 'fileshare')
createNamesCsv(fileshare)
names_csv = os.path.join(fileshare + os.sep + 'names.csv')
knowledge_base = os.path.join(fileshare, 'knowledge_base')
images_folder = os.path.join(fileshare, 'images')


class EmotionDetection(Resource):
    def get(self, img_name):
        try:
            obj = DeepFace.analyze(images_folder + os.sep + img_name, actions = ['gender', 'emotion'])
            return obj
        except:
            return {'error': 'face_not_found'}

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
        result = DeepFace.verify(images_folder + os.sep + img_name, knowledge_base + os.sep + img_name)
        if result['verified'] == True:
            df = pd.read_csv(names_csv)
            df = df[df['IMG'] == f'{img_name}']
            name = {'name':df['NAME'].to_string(header=False, index=False)}
            json_object = json.dumps(name, indent = 4)
            print(f'json_object:\n{json_object}')
        else:
            json_object = json.dumps({'name':'not_found'}, indent = 4)
        return json_object


class AddName(Resource):
    def get(self, person_name, img_name):
        '''
        adds image name and name of person to names.csv and moves the png file from 'images' to 'knowledge_base'
        '''
        df = pd.read_csv(names_csv)
        new_entry = {'IMG' : img_name, 'NAME': person_name}
        df = df.append(new_entry, ignore_index=True)
        df.to_csv(names_csv, index=False)
        moveFile(images_folder + os.sep + img_name, knowledge_base + os.sep + img_name)
        return {'data': 'Posted'}


class DeletePerson(Resource):
    def get(self, person_name):
        '''
        remove image from folder \'images\', \'knowledge_base\' and names.csv file
        '''
        df = pd.read_csv(names_csv)
        file_name = df.loc[df['NAME'] == person_name, 'IMG'].item()
        df.drop(df.loc[df['NAME']==person_name].index, inplace=True)
        df.to_csv(names_csv, index=False)
        knowledge_base_file = os.path.join(knowledge_base + os.sep + file_name)
        os.remove(knowledge_base_file)
        print(f'Knowledge base file: \"{knowledge_base_file}\" deleted')
        return {'data': 'deleted'}



# add this resource to the api and make it accessable through URL
api.add_resource(EmotionDetection, "/emotiondetection/<string:img_name>") # add parameters with /<int:test>/...
api.add_resource(FaceRecognition, "/facerecognition/<string:img_name>")
api.add_resource(AddName, "/addname/<string:person_name>/<string:img_name>")
api.add_resource(DeletePerson, "/deleteperson/<string:person_name>")


if __name__ == "__main__":
    app.run(host='0.0.0.0', debug=True) # set debug=False in production