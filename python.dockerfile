#create a dockerfile with python 2.7
FROM python:2.7
#set the working directory to /app
WORKDIR /naoqi
#copy the reqs folder into the container at /app
COPY reqs /naoqi
#install python pip
RUN apt-get update && apt-get install -y python-pip
#install any needed packages specified in requirements.txt
RUN pip install --trusted-host pypi.python.org -r requirements.txt
# Set the path to the SDK
ENV PYTHONPATH=${PYTHONPATH}:/naoqi/pynaoqi-python2.7-2.5.5.5-linux64/lib/python2.7/site-packages
ENV LD_LIBRARY_PATH="/naoqi/pynaoqi-python2.7-2.5.5.5-linux64/lib/python2.7/site-packages:$LD_LIBRARY_PATH"
#make port 8080 available to the world outside this container
EXPOSE 8080
#run app
CMD ["python", "app.py"]