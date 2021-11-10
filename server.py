# -*- coding: utf-8 -*-
"""
Created on Sat Feb 20 13:48:10 2021

@author: sshum
"""
import wolframalpha

from ibm_watson import TextToSpeechV1
from ibm_cloud_sdk_core.authenticators import IAMAuthenticator

from cryptography.fernet import Fernet

import sounddevice as sd
import soundfile as sf

import hashlib
import pickle

import socket
import sys

import ServerKeys

SERVER_ADDRESS = '192.168.86.32'
WAV_FILE = 'question.wav'

#parse arguments
def server():
    if (sys.argv[1] != "-sp" or sys.argv[3] != "-z"):
        sys.stderr.write("Incorrect Command line Arguments\n")
    
    sport = int(sys.argv[2])
    sock_size = sys.argv[4] 
        
    # Create a TCP socket
    # Notice the use of SOCK_STREAM for TCP packets 
    serverSocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    
    # Assign localhost IP address and port number to socket
    server_address = (SERVER_ADDRESS, sport) 
    serverSocket.bind(server_address)
    #Print Debug information on the console on STDERR
    sys.stderr.write('[Server 01] - Created socket at ' + SERVER_ADDRESS + "on port " + str(sport) + "\n")
    
    # TCP is a connection-oriented protocol so we need to listen to the port
    # can accept 5 different connections on this server
    serverSocket.listen(5)
    
    while True:
        sys.stderr.write('[Server 02] - Listening for client connections\n')
        # Accept the incoming connection
        socketConnection, client_address = serverSocket.accept()
        try:
            sys.stderr.write('[Server 03] - Accepted client connection from ' + str(client_address[0]) + ' on port ' + str(client_address[1]) + "\n")
    
            # Receive the encrypted question, decrypt it, and send answer
            while True:
                # Receive the client data in a buffer of sock_size bytes
                clientdata = socketConnection.recv(int(sock_size))
                
                if clientdata:

                    sys.stderr.write('[Server 04] - Received data: ' + str(clientdata) + "\n")

                    # deserialize data here
                    msg = pickle.loads(clientdata)
                    f = Fernet(msg[0])
                    sys.stderr.write('[Server 05] - Decrypt Key: ' + msg[0].decode('utf-8') + "\n")
                    
                    #checksum
                    checksum = hashlib.md5(str(msg[1]).encode())

                    if(checksum.digest() == msg[2]):

                        # decrypt message
                        question = f.decrypt(msg[1]).decode('utf-8')
                        sys.stderr.write('[Server 06] - Plain Text: ' + question + "\n")

                        # send to watson
                        watson(question)

                        sys.stderr.write('[Server 07] - Speaking Question: ' + question + "\n")
                        playSound(WAV_FILE)

                        # send to wolfram
                        sys.stderr.write('[Server 08] - Sending question to Wolframalpha\n')
                        answer = wolf(question)
                        sys.stderr.write('[Server 09] - Received question from Wolframalpha: ' + answer + '\n')

                        msg_tuple = encrypt(answer)
                        sys.stderr.write('[Server 13] - Answer Payload: ' + str(msg_tuple) + '\n')

                        # serialize data
                        msg2 = pickle.dumps(msg_tuple)

                        sys.stderr.write('[Server 14] - Sending answer: ' + str(msg2) + '\n\n')
                        socketConnection.sendall(msg2)

                    else:
                        sys.stderr.write('[Server Error] - Checksums do not match\n')

        finally:
            # Clean up the connection via closing the Socket
            socketConnection.close()
            

def encrypt(answer):

    key = Fernet.generate_key()
    sys.stderr.write("[Client 05] - Generated Encryption Key: " + key.decode('utf-8') + "\n")

    f = Fernet(key)
    token = f.encrypt(bytes(answer, encoding='utf8'))
    sys.stderr.write("[Client 06] - Cipher Text: " + token.decode('utf-8') + "\n")

    checksum = hashlib.md5(str(token).encode())

    return (key, token, checksum.digest())

def watson(text):
    authenticator = IAMAuthenticator(ServerKeys.IBM_WATSON_API_KEY)
    text_to_speech = TextToSpeechV1(authenticator=authenticator)
    
    text_to_speech.set_service_url('https://api.us-east.text-to-speech.watson.cloud.ibm.com')
    
    with open(WAV_FILE,'wb') as audio_file:
        audio_file.write(text_to_speech.synthesize(text,voice='en-US_AllisonV3Voice',accept='audio/wav').get_result().content)
        audio_file.close()

def playSound(wavFile):
    # Extract data and sampling rate from file
    # Example Code copied from Joska de Langen
    # found at https://realpython.com/playing-and-recording-sound-python/#python-sounddevice
    data, fs = sf.read(wavFile, dtype='float32')
    sd.play(data, fs)
    status = sd.wait()  # Wait until file is done playing

def wolf(question):
    app_id = ServerKeys.WOLFRAM_ALPHA_API_KEY
    client = wolframalpha.Client(app_id)
    res = client.query(question)

    try:
        ans = next(res.results).text

    except:
        ans = 'Wolfram does not know the answer'

    return ans
            
if __name__ == '__main__':
    server()