import socket, time, random

client = socket.socket()
client.connect(("pitanksonline.duckdn.org", 9090))

def forward(): #Функция движения вперёд. Возващяет False если танк упёрся или кончилась энергия 
    client.send(b"u")
    return ok()
def backward(): #Функция движения назад. Возващяет False если танк упёрся или кончилась энергия
    client.send(b"d")
    return ok()
def right(): #Функция поврота влево. Возващяет False если танк упёрся или кончилась энергия
    client.send(b"r")
    return ok()
def left(): #Функция поворота вправо. Возващяет False если танк упёрся или кончилась энергия
    client.send(b"l")
    return ok()
def fire(): #Функция стрельбы. Требует много энергии
    client.send(b"f")
def exit(): client.send(b"e") #Функция выхода из программы. Автоубивает танк
def ok(): #Системная функция. Вызывать запрещено. Работает в составе функций движения.
    data = client.recv(2)
    if(data.decode("utf-8") == "ok"): return True
    else: return False
def energy(): #Функция запроса энергии. возвращяет число от 0 до 100
    client.send(b"e")
    data = client.recv(4)
    ret = data.decode("utf-8")
    return int(ret[1:])
def radar(angle): #Функуия радара. Принимает на вход угол поиска. Возвращяет кортеж 
    if(int(angle) < 10): # (символ обнаружетого объекта. t-танк. w-стена. n-путота, растояние от 0 до 150)
        send = "s00"+str(angle)
    elif(int(angle)<100):
        send = "s0"+str(angle)
    else: send = "s" + str(angle)
    client.send(send.encode())
    data = client.recv(4)
    ret = data.decode("utf-8")
    return ret[0], int(ret[1:])

while True:
    obj0, _ = radar(0)
    obj15, len15 = radar(30)
    obj345, len345 = radar(30)
    if(len15 == 0): len15 = 999
    if(len345 == 0): len345 = 999
    if(len15 > len345):
        for i in range(5): right()
    else:
        for i in range(5): left()
    for i in range(10):
        if(not forward()):
            for i in range(10): backward()
            for i in range(30): left()
    if(obj0 == "t"):
        fire()
