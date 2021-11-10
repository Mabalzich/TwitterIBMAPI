# -*- coding: utf-8 -*-
"""
Created on Sat Feb 20 13:46:57 2021

@author: sshum
"""
from ibm_watson import TextToSpeechV1
from ibm_cloud_sdk_core.authenticators import IAMAuthenticator

from tweepy import Stream
from tweepy import OAuthHandler
from tweepy.streaming import StreamListener

from cryptography.fernet import Fernet

import sounddevice as sd
import soundfile as sf

import json
import pickle
import hashlib
import socket
import sys

import ClientKeys

WAV_FILE = 'answer.wav'

#global for tweet filter
tweet_txt = ''

def client():
    if (sys.argv[1] != "-sip" or sys.argv[3] != "-sp" or sys.argv[5] != "-z"):
        sys.stderr.write("Incorrect Command line Arguments\n")
    
    sip = sys.argv[2]
    sport = int(sys.argv[4])
    sock_size = int(sys.argv[6])
    
    s = socket.socket(socket.AF_INET,socket.SOCK_STREAM)
    s.connect((sip,sport))
    
    sys.stderr.write("[Client 01] - Connecting to " + sip + " on port " + str(sport) + "\n")

    while True:
        try:
            # twitter code
            question = tweet()

            msg_tuple = encrypt(question)
            sys.stderr.write("[Client 07] - Question Payload: " + str(msg_tuple) + "\n")

            # serialize data
            msg = pickle.dumps(msg_tuple)

            sys.stderr.write("[Client 08] - Sending Question: " + str(msg) + "\n")
            s.sendall(msg)

            try:
                ret = s.recv(sock_size) #attempts to receive a response from the server

                # deserialize data here
                reply = pickle.loads(ret)
                sys.stderr.write("[Client 09] - Received Data: " + str(reply) + "\n")

                f = Fernet(reply[0])
                sys.stderr.write("[Client 10] - Decrypt Key: " + reply[0].decode('utf-8') + "\n")

                #checksum
                checksum = hashlib.md5(str(reply[1]).encode())

                if(checksum.digest() == reply[2]):

                    # decrypt message
                    answer = f.decrypt(reply[1]).decode('utf-8')
                    sys.stderr.write("[Client 11] - Plain Text: " + answer + "\n")

                    watson(answer)

                    sys.stderr.write("[Client 12] - Speaking Answer: " + answer + "\n")
                    playSound(WAV_FILE)

                else:
                    sys.stderr.write('[Client Error] - Checksums do not match\n')
                    s.close()

            except socket.timeout: #times out after 3 seconds
                sys.stderr.write("Request timed out")

        finally:
            sys.stderr.write("\n")

def encrypt(question):

    key = Fernet.generate_key()
    sys.stderr.write("[Client 05] - Generated Encryption Key: " + key.decode('utf-8') + "\n")

    f = Fernet(key)
    token = f.encrypt(bytes(question, encoding='utf8'))
    sys.stderr.write("[Client 06] - Cipher Text: " + token.decode('utf-8') + "\n")

    checksum = hashlib.md5(str(token).encode())

    return (key, token, checksum.digest())

def watson(text):
    authenticator = IAMAuthenticator(ClientKeys.IBM_WATSON_API_KEY)
    text_to_speech = TextToSpeechV1(authenticator=authenticator)
    
    text_to_speech.set_service_url('https://api.us-east.text-to-speech.watson.cloud.ibm.com')
    
    with open('answer.wav','wb') as audio_file:
        audio_file.write(text_to_speech.synthesize(text,voice='en-US_AllisonV3Voice',accept='audio/wav').get_result().content)
        audio_file.close()

def playSound(wavFile):
    # Extract data and sampling rate from file
    # Example Code copied from Joska de Langen
    # found at https://realpython.com/playing-and-recording-sound-python/#python-sounddevice
    data, fs = sf.read(wavFile, dtype='float32')
    sd.play(data, fs)
    status = sd.wait()  # Wait until file is done playing

class listener(StreamListener): # TO DO: this class might need editing

    def on_data(self, data):
        all_data = json.loads(data)

        tweet = all_data["text"].replace("#ECE4564T17", '').strip()

        sys.stderr.write("[Client 03] - New Question found: " + tweet + "\n")

        username = all_data["user"]["screen_name"]

        global tweet_txt
        tweet_txt = tweet

        return False # returns after one captured tweet

    def on_error(self, status):
        print(status)

def tweet():

    auth = OAuthHandler(ClientKeys.C_KEY, ClientKeys.C_SECRET)
    auth.set_access_token(ClientKeys.A_TOKEN, ClientKeys.A_SECRET)

    sys.stderr.write("[Client 02] - Listening for tweets from Twitter API that contain questions\n")
    twitterStream = Stream(auth, listener())
    twitterStream.filter(track=["#ECE4564T17"])

    question = str(tweet_txt)

    return str(question)

if __name__ == '__main__':
    client()
    