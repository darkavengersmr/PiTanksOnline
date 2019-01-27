import socket, time, random

client = socket.socket()
client.connect(("pitanksonline.duckdns.org", 9090))

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
    object0, len0 = radar(0)
    #object30, len30 = radar(30)
    #object330, len330 = radar(330)
    if(object0 == "t"): fire()
    else:
        print(len0)
        if(len0 > 50 or len0 == 0):
            for i in range(10): forward()
            if(not forward()):
                for i in range(5): backward()
                if(random.random() > 0.5):
                    for i in range(random.randint(0, 90)): left()
                else:
                    for i in range(random.randint(0, 90)): right()
        else:
            if(random.random() > 0.5):
                for i in range(random.randint(0, 90)): left()
            else:
                for i in range(random.randint(0, 90)): right()
