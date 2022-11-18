import socket
import sqlite3
import threading
''' socket startup stuff '''
host="127.0.0.1"
port=25565
conn = sqlite3.connect('cis427_crypto.sqlite', check_same_thread=False)

serverOn = True
print ("Opened database successfully")

#creates table users if it doesnt exist
conn.execute('''CREATE TABLE IF NOT EXISTS users
        (ID INTEGER PRIMARY KEY     NOT NULL,
         email varchar(255) NOT NULL, 
         first_name    varchar(255)     ,
         last_name    varchar(255)     ,
         user_name    varchar(255)    NOT NULL,
         password    varchar(255)     ,
         usd_balance    DOUBLE NOT NULL);''')

#creates table cryptos if it doesnt exist
conn.execute('''CREATE TABLE IF NOT EXISTS cryptos 
        (ID INTEGER PRIMARY KEY     NOT NULL,
         crypto_namo    varchar(10)    NOT NULL,
         crypto_balance            DOUBLE ,
         user_id        varchar(255));''')

#checks to see if a user exists
if conn.execute("SELECT ID FROM users").fetchone():
    pass
else:
    # otherwise auto generates a new user
    print("User was auto-generated, as no user records were given")
    conn.execute("INSERT INTO users (ID,email,first_name,last_name,user_name,password,usd_balance) \
      VALUES (1, 'srprice@umich.edu', 'Steven', 'Price', 'srprice', 'password123', 100.00 )")

def buyFuncCreateRecord(name, amount, user_ID):
    conn.execute("INSERT INTO cryptos (crypto_name,crypto_balance,user_id) \
                VALUES (?, ?, ?) ", (name, float(amount), user_ID))
#searches SQL crypto and user table to grab price and change usd_balance
def buyFunc(name, amount, price, user_ID):
    #check to see if we need to make a new record or update
    counter = conn.execute("SELECT COUNT() from cryptos where user_id = ? and crypto_name = ?", (user_ID, name)).fetchone()[0]
    print(counter)
    
    if(counter ==0):
        #makes new record
        buyFuncCreateRecord(name, amount, user_ID)
        
    else:
        #updates record
        sel = conn.execute("SELECT crypto_balance from cryptos where user_id = ? and crypto_name = ?", (user_ID, name))
        for i in sel:
            cryptoBalance = float(i[0])
        cryptoBalance += float(amount)
        conn.execute("UPDATE cryptos set crypto_balance = ? where crypto_name = ? and user_id = ?", (cryptoBalance, name, user_ID))
        
    sel = conn.execute("SELECT usd_balance from users where ID = ?", (user_ID,))
    for i in sel:
        usdBalance = i[0]

    total = usdBalance - (float(price) * float(amount))
    if total < 0:
        return (False, total, price)
    conn.execute("UPDATE users set usd_balance = ? where ID = ?", (total, user_ID))
    sel = conn.execute("SELECT crypto_balance from cryptos where user_id = ? and crypto_name = ?", (user_ID,name))
    for i in sel:
        cBalance = i
    conn.commit()
    return (True, total, price, cBalance)

#searches SQL crypto and user table to grab price and change usd_balance
def sellFunc(name, price, amount, user_ID):
    sel = conn.execute("SELECT crypto_balance from cryptos where user_id = ? and crypto_name = ?", (user_ID,name))
    for i in sel:
        cryptoBalance = float(i[0])
    if(float(amount) > cryptoBalance):
        return (False, total, price)
    cryptoBalance -= float(amount)

    conn.execute("UPDATE cryptos set crypto_balance = ? where crypto_name = ? and user_id = ?", (cryptoBalance, name, user_ID))
    sel = conn.execute("SELECT usd_balance from users where ID = ?", (user_ID,))
    for i in sel:
        usdBalance = i[0]

    total = usdBalance + (float(price) * float(amount))
    conn.execute("UPDATE users set usd_balance = ? where ID = ?", (total, user_ID))
    sel = conn.execute("SELECT crypto_balance from cryptos where user_id = ? and crypto_name = ?", (user_ID,name))
    for i in sel:
        cBalance = i
    conn.commit()
    return (True, total, price, cBalance)

#searches crypto table and returns records for root users, shows all records
def listFuncRoot():
    sel = conn.execute("SELECT crypto_name, crypto_balance, users.first_name FROM cryptos INNER JOIN users ON users.ID = cryptos.user_id")
    print("The list of records in the Crypto database for user 1:")
    cryptoList = []
    for i in sel:
        print(i)
        cryptoList.append((i[0], i[1], i[2]))
    return cryptoList
#list function for users that are non root users, returns list of current users cryptos
def listFunc(loggedInName):
    sel = conn.execute("SELECT crypto_name, crypto_balance, users.first_name \
                        FROM cryptos \
                        INNER JOIN users ON users.ID = cryptos.user_id \
                        WHERE users.first_name = ?", (loggedInName,))
    print("The list of records in the Crypto database for user 1:")
    cryptoList = []
    for i in sel:
        print(i)
        cryptoList.append((i[0], i[1], i[2]))
    return cryptoList

#searches users table and returns first_name, last_name, usd_balance from users
def balanceFunc():
    sel = conn.execute("SELECT first_name, last_name, usd_balance from users")
    balanceList = []
    for i in sel:
        balanceList.append((i[0], i[1], i[2]))
    return balanceList

#client logins to ther server while grabbing information from the database to help use with the other functions
def login(dataString, loggedIn, currentConnection, address):
    global connectionList
    loggedIn = False
    dataSplit = dataString.split() #datasplit[1] = user_name, datasplit[2] = password
    sel = conn.execute("SELECT user_name, password, first_name, ID from users")
    for i in sel:
        if(dataSplit[1] == i[0]):
            if(dataSplit[2] == i[1]):
                loggedIn=True
                loggedInName = i[2]
                
                user_ID = i[3]
                if(dataSplit[1] == "root" or dataSplit[1] == "Root"):
                    rootLogin=True
                else:
                    rootLogin=False
    if(loggedIn):
        #if successful
        currentConnection.sendall("200 OK".encode())
    else:
        #if not successful
        currentConnection.sendall("403 Wrong UserID or Password".encode())
        loggedIn = False
        loggedInName = ""
        rootLogin = False
        user_ID = ""
        
    connectionList[loggedInName] = address[0]
    return loggedIn, rootLogin, loggedInName, user_ID

#client logs out, if only the client was logged in to begin with
def logout(loggedIn, connection):
    global connectionList
    loggedIn = False
    loggedInName = ""
    rootLogin = False
    connection.sendall("200 OK".encode())
    return loggedIn, rootLogin, loggedInName

#deposits usd balance into user db, returns to client updated balance
def deposit(dataString, loggedInName, connection):
    dataSplit = dataString.split()
    sel = conn.execute("SELECT usd_balance from users where first_name = ?", (loggedInName,))
    for i in sel:
        usdBalance = i[0]
    try:
        total = usdBalance + float(dataSplit[1])
    except ValueError:
        #in case the client entered wrong formatting
        connection.sendall("400 NO\nDEPOSIT FAILED, WRONG FORMAT".encode())
        return

    conn.execute("UPDATE users set usd_balance = ? where first_name = ?", (total, loggedInName))
    conn.commit()
    connection.sendall("200 OK\nDeposit successfully. New balance $%f".encode() % total)

#show active clients online and logged in, only root users can use this
def who(currentConnection):
    global connectionList
    sendString = "200 OK\nThe list of the active users:\n"
    for x in connectionList:
        sendString+= "%s    %s\n" % (x, connectionList[x])
    currentConnection.sendall(sendString.encode())

#looks up crypto balances, returns to clients crypto name, balance, and who owns it
def lookUp(dataString, currentConnection):
    dataSplit = dataString.split()
    sendString = ""
    counter = 0
    sel = conn.execute("SELECT crypto_balance from cryptos where crypto_name = ?", (dataSplit[1],))
    for i in sel:
        counter +=1
        sendString += "%s %s\n" % (dataSplit[1], str(round(i[0], 2)))
    if(counter == 0):
        currentConnection.sendall("404 Your search did not match any records".encode())
    else:
        sendStringFirst = "200 OK\nFound %i match\n" % (counter)
        sendStringFirst += sendString
        currentConnection.sendall(sendStringFirst.encode())



def main(connection, address):
    global serverOn, connectionList
    loggedIn = False
    rootLogin = False
    loggedInName = ""
    with connection:
        print("Connection by ", address)
        while serverOn:
            try:
                data = connection.recv(1024)
                #if user sent server a command
                if data:
                    #when sending/receiving information from client to server, it will have to be in bytes,
                    #thats why .decode("UTF-8") and .encode() is being used 
                    dataString = data.decode("UTF-8")
                    print(dataString)
                    sendString = "RECEIVED: " + dataString
                    connection.sendall(sendString.encode())
                    if(dataString[:5] == "LOGIN" and not loggedIn):
                        try:
                            loggedIn, rootLogin, loggedInName, user_ID = login(dataString,loggedIn, connection, address)
                        except(IndexError):
                            connection.sendall("400 NO Wrong Formatting".encode())
                    elif(dataString[:6] == "LOGOUT" and loggedIn):
                        del connectionList[loggedInName]
                        loggedIn, rootLogin, loggedInName = logout(loggedIn, connection)
                    elif(dataString[:7] == "DEPOSIT" and loggedIn):
                        deposit(dataString, loggedInName, connection)
                    elif(dataString[:3] == "WHO" and loggedIn and rootLogin):
                        who(connection)
                    elif(dataString[:6] == "LOOKUP" and loggedIn):
                        lookUp(dataString, connection)
                    elif(dataString[:3] == "BUY" and loggedIn):
                        #datasplit organizes data so I can manipulate the vars
                        dataSplit = dataString.split()
                        # 1 = name, 2= amount, 3= price
                        #try to catch misformatting by user
                        try:
                            result = buyFunc(dataSplit[1],dataSplit[2],dataSplit[3],user_ID) 
                            if result[0]:
                                sendString = "200 OK\nBOUGHT: New balance " + str(result[3]) + " " + dataSplit[1] + ", USD Balance $" + str(result[1])
                                connection.sendall(sendString.encode())
                            else:
                                connection.sendall("400 NO Not enough balance".encode())
                        except (OSError, ValueError, IndexError):
                            connection.sendall("400 NO Wrong Formatting".encode())

                    elif(dataString[:4] == "SELL" and loggedIn):
                        dataSplit = dataString.split()
                        #1=name, 2=price, 3=amount
                        #try to catch misformatting by user
                        try:
                            result = sellFunc(dataSplit[1],dataSplit[2],dataSplit[3],user_ID) 
                            if result[0]:
                                sendString = "200 OK\nSOLD: New balance:" + str(result[3]) + " " + dataSplit[1] + " " + "USD $" + str(result[1])
                                connection.sendall(sendString.encode())
                            else:
                                connection.sendall("400 NO Selling error Occurred".encode())
                        except (sqlite3.ProgrammingError, ValueError, IndexError, UnboundLocalError):
                            connection.sendall("400 NO Wrong Formatting".encode())

                    elif(dataString == "LIST" and loggedIn and rootLogin):
                        #sends client list of cryptos
                        cryptoList = listFuncRoot()
                        stringSend = "200 OK\nThe list of records in the Crypto database:\n"
                        for i in cryptoList:
                            stringSend = stringSend+ i[0]+" "+ str(i[1])+ " " +i[2] + "\n"
                        connection.sendall(stringSend.encode())

                    elif(dataString == "LIST" and loggedIn):
                        #sends client list of cryptos
                        cryptoList = listFunc(loggedInName)
                        stringSend = "200 OK\nThe list of records in the Crypto database for %s:\n" % (loggedInName)
                        for i in cryptoList:
                            stringSend = stringSend+ i[0]+" "+ str(i[1])+ " " +i[2] + "\n"
                        connection.sendall(stringSend.encode())

                    elif(dataString == "BALANCE" and loggedIn):
                        #sends client balance of user
                        balanceList = balanceFunc()
                        tempString = "200 OK"
                        for i in balanceList:
                            tempString += "\nBalance for user "+ i[0]+" "+ i[1]+": $"+ str(i[2])
                        tempString = tempString.encode()
                        connection.sendall(tempString)
                    elif(dataString == "SHUTDOWN" and loggedIn and rootLogin):
                        #Client tells server to shutdown
                        connection.sendall("200 OK SHUTDOWN".encode())
                        serverOn = False
                    elif(dataString == "QUIT"):
                        #sends quit command for client to terminate
                        loggedIn = False
                        rootLogin = False
                        try:
                            del connectionList[loggedInName]
                        except(KeyError):
                            pass
                        connection.sendall("200 OK QUIT".encode())
                        return
                        
                    else:
                        #if client did not send a correctly formatted command / a command that didn't exist
                        connection.sendall("400 NO Not an option".encode())
            except socket.timeout:
                pass
            

print("Server is started\n")
#server waits for connection
with socket.socket(socket.AF_INET,socket.SOCK_STREAM) as s:
    s.bind((host,port))
    s.listen(10) # 10 possible clients at a time
    
    s.settimeout(0.2)
    connectionList = {}
    connectionShutDownList = []
    while serverOn:
        try:
            #server grabs the users information and is able to send user information
            connection, address = s.accept()
            connectionShutDownList.append(connection)
            #starts thread and enters main function
            client_thread=threading.Thread(target=main,args=(connection,address))
            client_thread.start()
        #server restarts loop every .2 seconds to see if serverOn is still true
        except socket.timeout:
            pass
    else:
        #when serverOn = false quit all clients
        for i in connectionShutDownList:
            try:
                i.sendall("200 OK SHUTDOWN".encode())
            except OSError:
                pass

        
#SHUTDOWN NEEDS TO KILL ALL THREADS


#close database and socket while saving
client_thread.join()
s.close()
conn.commit()
conn.close()


