import socket
import numpy as np
import cv2

TCP_IP = '127.0.0.1'
TCP_PORT = 5007
IMG_WIDTH = 512
IMG_HEIGHT = 288
BUFFER_SIZE = 6 + IMG_WIDTH*IMG_HEIGHT*3

id = -1
lap = 0
total_laps = 0
damage = 0
position = 0
show = True

s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
s.connect((TCP_IP, TCP_PORT))

while 1:
    data = s.recv(BUFFER_SIZE)
    print('Length', len(data))
    
    if data[1] == 2:
        print('Game is running')
        lap = data[2]
        damage = data[4]
        position = data[5]

        ## Example code on how to get the image
        # Is only done once at the start of the race (show flag)
        if show:
            mat = np.fromstring(data[6:], dtype=np.uint8)
            mat = mat.reshape(IMG_HEIGHT,IMG_WIDTH,3)
            mat = np.flip(mat, 0) # Invert the y axis
            mat = np.flip(mat, 2) # Change from RGB to BGR 
            cv2.imshow('image',mat)
            show = False

        ## Test sending input
        up = 0x00
        down = 0x00
        left = 0x00
        right = 0x00

        # You have to focus the window with the image
        # and you can only press one key at a time, but it is good enough for now
        key = cv2.waitKeyEx(1)
        if key == 2490368:
            up = 0x01
        elif key == 2621440:
            down = 0x01
        elif key == 2424832:
            left = 0x01
        elif key == 2555904:
            right = 0x01
        
        input = bytes([id, up, down, left, right])
        s.send(input)
        
    elif data[1] == 1:
        print('Countdown')
        total_laps = data[3]
    elif data[1] == 0:
        print('Waiting for start')
        id = data[0]
    elif data[1] == 3:
        print('Finished!')
    elif data[1] == 4:
        print('Broken')
    elif data[1] == 5:
        print('Canceled')

s.close()
