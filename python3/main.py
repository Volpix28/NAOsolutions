from flask import Flask
from flask_restful import Api, Resource
from deepface import DeepFace
from functools import partial

#IMPORTS
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


def createFolders(dir, *subfolders: str):
    '''
    Creates one or more directories if not existent.
    dir: absolute path
    subfolders: name(s) of folder(s)
    '''
    concat_path = partial(os.path.join, dir)  # local temp function to map concatenated subfolder
    for subfolder in map(concat_path, subfolders):
        os.makedirs(subfolder, exist_ok=True)


def createCsv(dir, *files: str):
    '''
    Here two empty csv's are created with the names.csv and runs.csv. 
    In names.csv the name and the image name from the knownledge database are written in. 
    In runs.csv all results are stored.
    '''
    exist = [f for f in files if os.path.isfile(dir + os.sep + f)]
    non_exist = list(set(exist) ^ set(files))  # Symmetric Difference
    if len(non_exist) != 0:
        for f in non_exist:
            file_path = dir + os.sep + f
            if f == 'names.csv':
                df = pd.DataFrame(columns=['IMG', 'NAME'])
            elif f == 'runs.csv':
                df = pd.DataFrame(columns=['BEFORE_ACTION', 'AFTER_ACTION', 'USER_NUMERIC_EMOTION', 'GENDER'])
            else:
                df = pd.DataFrame({})
            df.to_csv(file_path, index=False)
            print('INFO - createCsv: %s created' % file_path)
    else:
        print('INFO - createCsv: file(s) %s already exists' % exist)


#API 
app = Flask(__name__)
api = Api(app)

# create fileshare with 'images' and 'knowledge_base' subfolder if not existent
createFolders('fileshare', 'images', 'knowledge_base')
fileshare = os.path.join(os.getcwd(), 'fileshare')
createCsv(fileshare, 'names.csv', 'runs.csv')
names_csv = os.path.join(fileshare + os.sep + 'names.csv')
knowledge_base = os.path.join(fileshare, 'knowledge_base')
images_folder = os.path.join(fileshare, 'images')


class EmotionDetection(Resource):
    '''
    This code defines a method get in a class DeepFace. 
    The method takes as input an image name img_name, and performs facial analysis on the image 
    using the DeepFace.analyze function. The function analyzes the image located at the path 
    images_folder + os.sep + img_name and extracts the gender and emotion information.

    The extracted information is then filtered and stored in a dictionary 
    obj_filtered with only the dominant emotion and gender information. 
    The dictionary is then converted to a JSON object using the json.dumps method and 
    returned as the output of the get method.
    '''
    def get(self, img_name):
        obj = DeepFace.analyze(img_path=images_folder + os.sep + img_name,
                               actions=['gender', 'emotion'])
        obj_filtered = {'dominant_emotion': obj['dominant_emotion'], 'gender': obj['gender']}
        json_object = json.dumps(obj_filtered, indent=4)
        return json_object


class FaceRecognition(Resource):
    '''
    In this class the face recognition is executed, this class compares the persons 
    if they are already in the Knownledge data base.

    Note: 
    There must always be the same number of photos in the Knowledge_base as 
    there are entries in the names.csv.
    '''
    def get(self, img_name):
        name, img_id = 'not_found', 'not_in_database'
        known_images = os.listdir(knowledge_base)
        for i in range(0, len(known_images)):
            result = DeepFace.verify(img1_path=knowledge_base + os.sep + known_images[i],
                                     img2_path=images_folder + os.sep + img_name,
                                     model_name='Facenet512',
                                     distance_metric='euclidean_l2')
            print(f'\nINFO - FaceRecognition: {i+1}. run: comparing image \"{img_name}\" with \"{known_images[i]}\"\nresult: {result}\n\n')
            if result['verified'] is True:
                df = pd.read_csv(names_csv)
                print(name)
                name = df['NAME'][df['IMG']==known_images[i]].values[0]
                img_id = known_images[i]
                break
        # os.remove(images_folder + os.sep + img_name)
        json_object = json.dumps({'name': name, 'img_id': img_id}, indent=4)
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
    '''
    If this class is triggered, then the photos in /fileshare/images are deleted.
    '''
    def get(self):
        for file in os.listdir(images_folder):
            print(f'removing file: {file}')
            os.remove(f'{images_folder}/{file}')
        return {'data': 'deleted'}


# add this resource to the api and make it accessable through URL 
api.add_resource(EmotionDetection, '/emotiondetection/<string:img_name>')  # add parameters with /<int:test>/...
api.add_resource(FaceRecognition, '/facerecognition/<string:img_name>')
api.add_resource(AddName, '/addname/<string:person_name>/<string:img_name>')
api.add_resource(DeletePerson, '/deleteperson/<string:img_id>')
api.add_resource(CleanSession, '/cleansession')


#RUN
if __name__ == '__main__':
    app.run(host='0.0.0.0', debug=True)
