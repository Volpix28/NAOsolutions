# NAOsolutions
University Project for enhancing the NAO with python 3.X libraries and python 2.17 with naoqi.

This script in splitted into 2 Folders.
The python2 folder should be opened via the dockerfile and the python3 folder provides the
possibility to enhance NAO´s features like face recognition and emotion detection from [DeepFace](https://github.com/serengil/deepface).

All Tools used are open-source and can be used for free for further development.
Communication between the two enviroments is done via flask-restful API.

## python2

- **actions.py** stores all functions related to NAO´s movement
- **dialog.py** stores all of the dialogs for the default functionality of this repository
- **functions.py** stores all functions related to the main.py scipt (conformation loops, photo capture, audio recording, ...)
- **main.py** contains all configuration data needed to establish all connections and run the script

## python3

- **main.py** contains all the functions for creating needed folders and starts the API (WSL IP is needed when using Windows on local env)

## fileshare
Acts as local fileshare. The python 2.7 enviroment gets acess granted through [bind mount](https://docs.docker.com/storage/bind-mounts/).

- **images** contains all the pictures made in one session (gets cleared automatically after every communication)
- **knowledge_base** contains all saved pictures needed for the face recognition
- **names.csc** contains all names for the face recognition (empty at default)
- **runs.csv** contains all data thats gathered through the feature we implemented (empty at default)

*Please feel free to use this Flask and Docker setup for your own features without losing the possibilities provided by the naoqi-library!*

**Developers**
Böswarth, Lukas
Dielacher, Marcel
Kopeinig, Matthias
Roucka, Alexander
