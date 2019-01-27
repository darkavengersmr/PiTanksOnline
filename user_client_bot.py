#! /usr/bin/python3

import socket, time, random

client = socket.socket()
client.connect(("192.168.32.2", 9090))
def forward():
    client.send(b"u")
    return ok()
def backward():
    client.send(b"d")
    return ok()
def right():
    client.send(b"r")
    return ok()
def left():
    client.send(b"l")
    return ok()
def fire():
    client.send(b"f")
def exit(): client.send(b"e")
def ok():
    data = client.recv(2)
    if(data.decode("utf-8") == "ok"): return True
    else: return False
def energy():
    client.send(b"e")
    data = client.recv(4)
    ret = data.decode("utf-8")
    return int(ret[1:])
def radar(angle):
    if(int(angle) < 10):
        send = "s00"+str(angle)
    elif(int(angle)<100):
        send = "s0"+str(angle)
    else: send = "s" + str(angle)
    client.send(send.encode())
    data = client.recv(4)
    ret = data.decode("utf-8")
    return ret[0], int(ret[1:])
def MyRight(len_):
    rad = 0
    for i in range(len_):
        rad+=1
        if(rad >= 5):
            rad = 0
            obj, len_ = radar(0)
            if(obj == "t"): fire()
        if(not right()):
            for i in range(random.randint(5, 15)): backward()
            for i in range(random.randint(5, 15)): right()
def MyLeft(len_):
    rad = 0
    for i in range(len_):
        rad+=1
        if(rad >= 5):
            rad = 0
            obj, len_ = radar(0)
            if(obj == "t"): fire()
        if(not left()):
            for i in range(random.randint(5, 15)): backward()
            for i in range(random.randint(5, 15)): left()
def MyForward(len_, napr):
    for i in range(len_):
        if(not forward()):
            for i in range(random.randint(5, 15)): backward()
            if(random.random() > 0.5): MyRight(random.randint(5, 15))
            else: MyLeft(random.randint(5 , 15))
        if(napr > 0): MyLeft(random.randint(3, 5))
        if(napr < 0): MyRight(random.randint(3, 5))
while True:
    obj30, len30 = radar(random.randint(25, 35))
    obj330, len330 = radar(random.randint(325, 335))
    if(obj30 == "t"): MyRight(15)
    elif(obj330 == "t"): MyLeft(15)
    else:
        obj0, len0 = radar(0)
        #if(len30 < 50 and len330 < 50): MyRight(random.randint(150, 210))
        if(obj0 == "w" and len0 < 30):
            if(random.random() > 0.5): MyRight(random.randint(30, 100))
            else: MyLeft(random.randint(30, 100))
        elif(obj0 == "t"):
            fire()
            while True:
                obj0, len0 = radar(0)
                if(obj0 != "t"): break
                time.sleep(0.1)
        else: MyForward(random.randint(1, 10), len30 - len330)
