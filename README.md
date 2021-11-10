# TwitterIBMAPI
Learned how to use the Twitter, IBM Watson, and Wolfram Alpha APIs and practiced socket networking.

Note: I did not post my API keys for privacy reasons.

Client Functionality:

-Establish a TCP connection with the server.

-Use Twitter API to read questions in the form of tweets with a specific hashtag.
-Encrypt the question via python hashlib library and add a checksum for message integrity.
-Serialize the resulting encryption to be sent over the socket connection to the server.
-Await a response from the server.
-Deserialize and decrypt the response.
-Additional functionality to check the checksum.
-IBM watson API converts the text to speech outputted in an audio file.
-Sounddevice python library plays the audio.
-Back to listening for Tweets.

Server Functionality:

-Establish client TCP connection (up to 5 clients).
-Await message from client.
-Deserialize and decrypt message.
-Check the checksum.
-IBM watson API converts the text to speech outputted in an audio file.
-Sounddevice python library plays the audio.
-Query the Wolfram API with the question.
-Encrypt the Wolfram Answer via python hashlib library and add a checksum for message integrity.
-Serialize and send back to the client.
-Return to listening for messages.

