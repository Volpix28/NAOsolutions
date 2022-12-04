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
    concat_path = partial(os.path.join, dir)  # local temp function to map concatenated subfolder
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
        df = pd.DataFrame(columns=['IMG', 'NAME'])
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
        obj = DeepFace.analyze(img_path=images_folder + os.sep + img_name, 
                               actions=['gender', 'emotion'])
        obj_filtered = {'dominant_emotion': obj['dominant_emotion'], 'gender': obj['gender']}
        json_object = json.dumps(obj_filtered, indent = 4)
        return json_object


class FaceRecognition(Resource):
    def get(self, img_name):
        name, img_id = 'not found', 'not_in_database'
        known_images = os.listdir(knowledge_base)
        for i in range(0, len(known_images)):
            result = DeepFace.verify(img1_path=knowledge_base + os.sep + known_images[i],
                                     img2_path=images_folder + os.sep + img_name,
                                     model_name='Facenet512',
                                     distance_metric='euclidean_l2')
            print(f'\nINFO - FaceRecognition: {i+1}. run: comparing image \"{img_name}\" with \"{known_images[i]}\"\nresult: {result}\n\n')
            if result['verified'] is True:
                df = pd.read_csv(names_csv)
                name = df['NAME'][df['IMG']==known_images[i]].values[0]
                img_id = known_images[i]
                break
        # os.remove(images_folder + os.sep + img_name)
        json_object = json.dumps({'name': name, 'img_id': img_id}, indent = 4)
        return json_object


class AddName(Resource):
    def get(self, person_name, img_name):
        '''
        adding image name and name of person to names.csv and moves the file from 'images' to 'knowledge_base'
        '''
        df = pd.read_csv(names_csv)
        new_entry = {'IMG': img_name, 'NAME': person_name}
        df = df.append(new_entry, ignore_index=True)
        df.to_csv(names_csv, index=False)
        moveFile(images_folder + os.sep + img_name, knowledge_base + os.sep + img_name)
        return {'data': 'Posted'}


class DeletePerson(Resource):
    def get(self, img_id):
        '''
        remove image from folder \'images\', \'knowledge_base\' and names.csv file
        '''
        df = pd.read_csv(names_csv)
        df.drop(df.loc[df['IMG']==img_id].index, inplace=True)
        df.to_csv(names_csv, index=False)
        knowledge_base_file = os.path.join(knowledge_base + os.sep + img_id)
        images_file = os.path.join(images_folder + os.sep + img_id)
        os.remove(knowledge_base_file)
        print(f'INFO - DeletePerson: \"{knowledge_base_file}\" deleted')
        os.remove(images_file)
        print(f'INFO - DeletePerson: \"{images_file}\" deleted')
        return {'data': 'deleted'}


class CleanSession(Resource):
    def get(self):
        for file in os.listdir(images_folder):
            print(f'removing file: {file}')
            os.remove(f'{images_folder}/{file}')
        return {'data': 'deleted'}


# add this resource to the api and make it accessable through URL
api.add_resource(EmotionDetection, "/emotiondetection/<string:img_name>")  # add parameters with /<int:test>/...
api.add_resource(FaceRecognition, "/facerecognition/<string:img_name>")
api.add_resource(AddName, "/addname/<string:person_name>/<string:img_name>")
api.add_resource(DeletePerson, "/deleteperson/<string:img_id>")
api.add_resource(CleanSession, "/cleansession")


if __name__ == "__main__":
    app.run(host='0.0.0.0', debug=True)
