import socket
import threading
import sys

'''socket information'''
host=sys.argv[1]
port=25565

#function for getting user input, threaded so if another user were to
#shut down the server, the current user will be able to recieve the message
def getInput():
    userInput = input()
    try:
        s.sendall(userInput.encode())
    #if server is shut down already, doesn't send to server, just tells user that server is offline
    except OSError:
        print("Server was shut down before input could be sent, Closing Application")
    return

#socket to connect client to server
with socket.socket(socket.AF_INET,socket.SOCK_STREAM) as s:
    s.connect((host,port))
    connected = True
    #incase of connection closing, adds a 1 second timeout, to redo connected loop
    s.settimeout(1)
    print("Connection Established")

    userInput = input()
    #encode message as to transfer information between client to server it must be a byte.
    s.sendall(userInput.encode())
    while connected:
        #thread for getting input and reading messages at the same time
        thread_input=threading.Thread(target=getInput,args=())
        try:
            #decodes byte into string for user to read
            data=s.recv(1024).decode('utf-8')
            print(data)
            
            #quit if client receives from server 200 ok quit
            if(data == "200 OK QUIT" or data == "200 OK SHUTDOWN"):
                print("Client exiting, you might need to press enter to fully exit")
                s.close()
                connected = False
                sys.exit()
            #200 ok allows user to input another command
            #400 no, lets user know that command didn't work and allows them to try again
            #403 no, incorrect login
            elif(data[:6] == "200 OK" or data[:6] == "400 NO" or data[:3] == "403" or data[:3] == "404"):
                thread_input.start()
            
            
        except socket.timeout:
            pass
            
        



