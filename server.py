#! /usr/bin/python3

# -*- coding: utf-8 -*-

from flask import Flask, render_template, send_file, request, Response
from imutils.video import WebcamVideoStream
import random, time, threading, cv2, math, socket, re, datetime
import numpy as np

server = socket.socket()
server.bind(("192.168.32.2", 9090))
server.listen(10)

game_xmax = 640
game_ymax = 480
game_xmin = 0
game_ymin = 0

time_action = time.time()
time_top_10_update = time.time()

game_speed = 0.01

font = cv2.FONT_HERSHEY_SIMPLEX

cam = False

log_file = "/home/pi/tank/log.log"

log = open(log_file, "a")
log.write("--------------------------------------------------------------------------------------------------------------------------------\n")
log.close()

if(cam): cap = WebcamVideoStream(src=0).start()
else: frame_gray = cv2.imread("/home/pi/tank/video.jpg", 0)


class class_tank():
    def __init__(self, xin, yin, ipin, anglein, colorin, namein):
        self.x = xin
        self.y = yin
        self.speed = 2
        self.ip = ipin
        self.color = colorin
        self.angle = anglein
        self.size = 20
        self.bullet = None
        self.radar = None
        self.life = True
        self.name = namein
        self.actions = 100
        self.time_actions = time.time()
        self.visible = True
        self.time_death = None
        self.num_death = 0
        self.num_murder = 0

class class_top_tank():
    def __init__(self, ipin, namein, murderin, deathin, scorein):
        self.ip = ipin
        self.name = namein
        self.murder = murderin
        self.death = deathin
        self.score = scorein

class class_bullet():
    def __init__(self, xin, yin, anglein, colorin):
        self.x = xin
        self.y = yin
        self.x_start = xin
        self.y_start = yin
        self.angle = anglein
        self.color = colorin

class class_draw_radar():
    def __init__(self):
        self.points = []
        self.time = time.time()

tanks = []
name_ip = {"192.168.32.2": "server_bot",
           "192.168.32.64": "Andrey",
           "192.168.32.192": "Tihon",
           "192.168.32.16": "Platon"}
top_10 = []

def socket(conn, add, id_tank):
    global tanks
    print("\n\n\nNew Client -", add, "\n\n\n")
    while True:
        if(tanks[id_tank].life == False): break
        data = conn.recv(1)
        str_in = data.decode("utf-8")
        #print(str_in)
        if(len(str_in) == 1):
            x_next = tanks[id_tank].x
            y_next = tanks[id_tank].y
            angle_next = tanks[id_tank].angle
            if(str_in[0] == "d"):
                x_next, y_next = move(tanks[id_tank].x, tanks[id_tank].y, tanks[id_tank].angle, -1*tanks[id_tank].speed)
            elif(str_in[0] == "u"):
                x_next, y_next = move(tanks[id_tank].x, tanks[id_tank].y, tanks[id_tank].angle, tanks[id_tank].speed)
            elif(str_in[0] == "r"):
                angle_next -= 1
            elif(str_in[0] == "l"):
                angle_next += 1
            elif(str_in[0] == "q"):
                life = False
                tanks[id_tank].time_death = time.time()
                break
            elif(str_in[0] == "e"):
                if(tanks[id_tank].actions < 10): send = "e00" + str(tanks[id_tank].actions)
                elif(tanks[id_tank].actions < 100): send = "e0" + str(tanks[id_tank].actions)
                elif(tanks[id_tank].actions < 1000): send = "e" + str(tanks[id_tank].actions)
                conn.send(send.encode())
            elif(str_in[0] == "f" and tanks[id_tank].actions >= 20 and tanks[id_tank].bullet is None):
                tanks[id_tank].actions -= 20
                new_bullet_x, new_bullet_y = move(tanks[id_tank].x, tanks[id_tank].y, tanks[id_tank].angle, int(tanks[id_tank].size/1.5))
                tanks[id_tank].bullet = class_bullet(new_bullet_x, new_bullet_y, tanks[id_tank].angle, tanks[id_tank].color)
                time.sleep(game_speed)
            elif(str_in[0] == "s" and tanks[id_tank].actions > 0):
                if(tanks[id_tank].actions > 0):
                    tanks[id_tank].actions -= 1
                    angle_tmp = conn.recv(3)
                    angle_scan = angle_tmp.decode("utf-8")
                    angle_scan = (360 - int(angle_scan)) + tanks[id_tank].angle
                    scan_x, scan_y = move(tanks[id_tank].x, tanks[id_tank].y, angle_scan, int(tanks[id_tank].size/1.4))
                    tanks[id_tank].radar = class_draw_radar()
                    tanks[id_tank].radar.points.append((int(scan_x), int(scan_y)))
                    scan_tank = False
                    while True:
                        len_ = math.sqrt(math.pow(abs(tanks[id_tank].x-scan_x), 2)+math.pow(abs(tanks[id_tank].y-scan_y), 2))
                        if(len_ >= 150):
                            conn.send(b"n000")
                            break
                        scan_x, scan_y = move(scan_x, scan_y, angle_scan, 1)
                        tanks[id_tank].radar.points.append((int(scan_x), int(scan_y)))
                        if(frame_gray.shape[0] > int(scan_y) and frame_gray.shape[1] > int(scan_x) and
                           int(scan_y) > 0 and int(scan_x) > 0):
                            if(frame_gray[int(scan_y), int(scan_x)] != 0):
                                len_ = math.sqrt(math.pow(abs(tanks[id_tank].x-scan_x), 2)+math.pow(abs(tanks[id_tank].y-scan_y), 2))
                                if(int(len_) < 10): send = "w00" + str(int(len_))
                                elif(int(len_) < 100): send = "w0" + str(int(len_))
                                elif(int(len_) < 1000): send = "w" + str(int(len_))
                                conn.send(send.encode())
                                break
                            else:
                                for j in tanks:
                                    if(j.visible):
                                        if(abs(scan_x - j.x) < tanks[id_tank].size/2 and abs(scan_y - j.y) < tanks[id_tank].size/2):
                                            len_ = math.sqrt(math.pow(abs(tanks[id_tank].x-j.x), 2)+math.pow(abs(tanks[id_tank].y-j.y), 2))
                                            if(j.life): str_send = "t"
                                            else: str_send = "w"
                                            if(int(len_) < 10): send = str_send + "00" + str(int(len_))
                                            elif(int(len_) < 100): send = str_send + "0" + str(int(len_))
                                            elif(int(len_) < 1000): send = str_send + str(int(len_))
                                            conn.send(send.encode())
                                            scan_tank = True
                                            break
                                        if(scan_tank): break
                                if(scan_tank): break
                        else:
                            len_ = math.sqrt(math.pow(abs(tanks[id_tank].x-scan_x), 2)+math.pow(abs(tanks[id_tank].y-scan_y), 2))
                            if(int(len_) < 10): send = "w00" + str(int(len_))
                            elif(int(len_) < 100): send = "w0" + str(int(len_))
                            elif(int(len_) < 1000): send = "w" + str(int(len_))
                            conn.send(send.encode())
                            break
                    time.sleep(game_speed/2)
                else: conn.send(b"lwen")

            if(tanks[id_tank].angle != angle_next or tanks[id_tank].x != x_next or tanks[id_tank].y != y_next):

                left_up = turn(x_next-(tanks[id_tank].size/2), y_next-(tanks[id_tank].size/1.5), x_next, y_next, angle_next)
                right_up = turn(x_next+(tanks[id_tank].size/2), y_next-(tanks[id_tank].size/1.5), x_next, y_next, angle_next)
                right_down = turn(x_next+(tanks[id_tank].size/2), y_next+(tanks[id_tank].size/2), x_next, y_next, angle_next)
                left_down = turn(x_next-(tanks[id_tank].size/2), y_next+(tanks[id_tank].size/2), x_next, y_next, angle_next)
                forsenter = turn(x_next, y_next-(tanks[id_tank].size/1.5), x_next, y_next, angle_next)
                baksenter = turn(x_next, y_next+(tanks[id_tank].size/2), x_next, y_next, angle_next)
                senter = (x_next, y_next)

                if(5<left_up[0]<game_xmax-game_xmin-5 and 5<left_down[0]<game_xmax-game_xmin-5 and
                   5<right_up[0]<game_xmax-game_xmin-5 and 5<right_down[0]<game_xmax-game_xmin-5 and
                   5<left_up[1]<game_ymax-game_ymin-5 and 5<left_down[1]<game_ymax-game_ymin-5 and
                   5<right_up[1]<game_ymax-game_ymin-5 and 5<right_down[1]<game_ymax-game_ymin-5):
                    if(frame_gray[int(left_up[1]), int(left_up[0])] == 0 and frame_gray[int(left_down[1]), int(left_down[0])] == 0 and
                       frame_gray[int(right_up[1]), int(right_up[0])] == 0 and frame_gray[int(right_down[1]), int(right_down[0])] == 0 and
                       frame_gray[int(senter[1]), int(senter[0])] == 0 and frame_gray[int(forsenter[1]), int(forsenter[0])] == 0 and
                       frame_gray[int(baksenter[1]), int(baksenter[0])] == 0):
                        stop_tank = False
                        for j in range(len(tanks)):
                            if(j != id_tank and tanks[j].visible):
                                if((abs(left_up[0] - tanks[j].x) < tanks[j].size/2 and
                                   abs(left_up[1] - tanks[j].y) < tanks[j].size/2) or
                                   (abs(left_down[0] - tanks[j].x) < tanks[j].size/2 and
                                   abs(left_down[1] - tanks[j].y) < tanks[j].size/2) or
                                   (abs(right_down[0] - tanks[j].x) < tanks[j].size/2 and
                                   abs(right_down[1] - tanks[j].y) < tanks[j].size/2) or
                                   (abs(right_up[0] - tanks[j].x) < tanks[j].size/2 and
                                   abs(right_up[1] - tanks[j].y) < tanks[j].size/2) or
                                   (abs(senter[0] - tanks[j].x) < tanks[j].size/2 and
                                   abs(senter[1] - tanks[j].y) < tanks[j].size/2) or
                                   (abs(forsenter[0] - tanks[j].x) < tanks[j].size/2 and
                                   abs(forsenter[1] - tanks[j].y) < tanks[j].size/2) or
                                   (abs(baksenter[0] - tanks[j].x) < tanks[j].size/2 and
                                   abs(baksenter[1] - tanks[j].y) < tanks[j].size/2)):
                                    stop_tank = True

                        if(not stop_tank):
                            if(tanks[id_tank].actions >= 1):
                                tanks[id_tank].actions -= 1
                                tanks[id_tank].x = x_next
                                tanks[id_tank].y = y_next
                                tanks[id_tank].angle = angle_next
                                tanks[id_tank].time_actions = time.time()
                                ok_fl = True
                                conn.send(b"ok")
                            else: conn.send(b"fl")
                        else: conn.send(b"fl")
                    else: conn.send(b"fl")
                else: conn.send(b"fl")
            time.sleep(game_speed)

                #else: print("STOP - wall")
            #else: print("STOP - area")
            #if(drive):
            #    if(ok_fl): conn.send(b"ok")
            #    else: conn.send(b"fl")
def new_client():
    global tanks, color
    while True:
        connect, addres = server.accept()
        id_tank = -1
        new = True
        for i in range(len(tanks)):
            if(str(tanks[i].ip) == str(addres[0])):
                new = False
                id_tank = i
        while True:
            x_next = random.randint(5, game_xmax-game_xmin-5)
            y_next = random.randint(5, game_ymax-game_ymin-5)
            angle_next = random.randint(0, 359)
            color = (random.randint(0, 25)*10, random.randint(0, 25)*10, random.randint(0, 25)*10)

            left_up = turn(x_next-(10), y_next-(20/1.5), x_next, y_next, angle_next)
            right_up = turn(x_next+(10), y_next-(20/1.5), x_next, y_next, angle_next)
            right_down = turn(x_next+(10), y_next+(10), x_next, y_next, angle_next)
            left_down = turn(x_next-(10), y_next+(10), x_next, y_next, angle_next)
            forsenter = turn(x_next, y_next-(20/1.5), x_next, y_next, angle_next)
            baksenter = turn(x_next, y_next+(10), x_next, y_next, angle_next)
            senter = (x_next, y_next)

            if(5<left_up[0]<game_xmax-game_xmin-5 and 5<left_down[0]<game_xmax-game_xmin-5 and
               5<right_up[0]<game_xmax-game_xmin-5 and 5<right_down[0]<game_xmax-game_xmin-5 and
               5<left_up[1]<game_ymax-game_ymin-5 and 5<left_down[1]<game_ymax-game_ymin-5 and
               5<right_up[1]<game_ymax-game_ymin-5 and 5<right_down[1]<game_ymax-game_ymin-5):
                if(frame_gray[int(left_up[1]), int(left_up[0])] == 0 and frame_gray[int(left_down[1]), int(left_down[0])] == 0 and
                   frame_gray[int(right_up[1]), int(right_up[0])] == 0 and frame_gray[int(right_down[1]), int(right_down[0])] == 0 and
                   frame_gray[int(senter[1]), int(senter[0])] == 0 and frame_gray[int(forsenter[1]), int(forsenter[0])] == 0 and
                   frame_gray[int(baksenter[1]), int(baksenter[0])] == 0):
                    stop_tank = False
                    for j in range(len(tanks)):
                        if(tanks[j].visible):
                            if((abs(left_up[0] - tanks[j].x) < tanks[j].size/2 and
                               abs(left_up[1] - tanks[j].y) < tanks[j].size/2) or
                               (abs(left_down[0] - tanks[j].x) < tanks[j].size/2 and
                               abs(left_down[1] - tanks[j].y) < tanks[j].size/2) or
                               (abs(right_down[0] - tanks[j].x) < tanks[j].size/2 and
                               abs(right_down[1] - tanks[j].y) < tanks[j].size/2) or
                               (abs(right_up[0] - tanks[j].x) < tanks[j].size/2 and
                               abs(right_up[1] - tanks[j].y) < tanks[j].size/2) or
                               (abs(senter[0] - tanks[j].x) < tanks[j].size/2 and
                               abs(senter[1] - tanks[j].y) < tanks[j].size/2) or
                               (abs(forsenter[0] - tanks[j].x) < tanks[j].size/2 and
                               abs(forsenter[1] - tanks[j].y) < tanks[j].size/2) or
                               (abs(baksenter[0] - tanks[j].x) < tanks[j].size/2 and
                               abs(baksenter[1] - tanks[j].y) < tanks[j].size/2)):
                                stop_tank = True

                    if(not stop_tank):
                        if(addres[0] in name_ip.keys()): name = name_ip[addres[0]]
                        else: name = addres[0]
                        if(new):
                            tanks.append(class_tank(x_next, y_next, addres[0], angle_next, color, name))
                            pr3 = threading.Thread(target=socket, args=(connect, addres[0], len(tanks)-1))
                            pr3.start()
                            log = open(log_file, "a")
                            log.write(str(datetime.datetime.today()) + " connect: " + str(name) + ", " + str(addres[0]) + "\n")
                            log.close()
                        elif(tanks[id_tank].life == False):
                            tanks[id_tank].color = color
                            tanks[id_tank].x = x_next
                            tanks[id_tank].y = y_next
                            tanks[id_tank].angle = angle_next
                            tanks[id_tank].life = True
                            tanks[id_tank].visible = True
                            tanks[id_tank].time_actions = time.time()
                            tanks[id_tank].time_death = None
                            tanks[id_tank].name = name_ip[addres[0]]
                            pr3 = threading.Thread(target=socket, args=(connect, addres[0], id_tank))
                            pr3.start()
                            log = open(log_file, "a")
                            log.write(str(datetime.datetime.today()) + " connect: " + str(tanks[id_tank].name) + ", " + str(tanks[id_tank].ip) + "\n")
                            log.close()
                        break

def turn(x_old,y_old,x_cent,y_cent,u):
    x_pov = ((x_old)-x_cent) * math.cos(math.radians(u)) + ((y_old)-y_cent) * math.sin(math.radians(u))
    y_pov = ((y_old)-y_cent) * math.cos(math.radians(u)) - ((x_old)-x_cent) * math.sin(math.radians(u))
    return x_pov+x_cent, y_pov+y_cent

def move(x, y, angle, speed):
    return x+speed*math.sin(math.radians((-1*angle)%360)), y-speed*math.cos(math.radians((-1*angle)%360))

def image2jpeg(image):
    ret, jpeg = cv2.imencode('.jpg', image)
    return jpeg.tobytes()

def camera2inet():
    app = Flask(__name__, template_folder="templates")
    print("Start inet thread")

    @app.route('/')
    def name():
        return render_template('name.html')

    @app.route('/simple_bot1.py')
    def simple_bot1():
        return send_file("templates/simple_bot1.py", mimetype="image/jpg", as_attachment=True, attachment_filename="templates/simple_bot1.py")

    @app.route('/simple_bot2.py')
    def simple_bot2():
        return send_file("templates/simple_bot2.py", mimetype="image/jpg", as_attachment=True, attachment_filename="templates/simple_bot2.py")

    @app.route('/get_name.php', methods=['GET'])
    def get():
        print("get name")
        name = request.args.get('login')
        #print(request.remote_addr)
        name_ip[str(request.remote_addr)] = name
        #name_ip.update((str(request.remote_addr), name))
        print("--------", name_ip, "-------")
        return render_template('home.html')

    def gen():
        while True:
            frame_inet = cv2.cvtColor(frame_gray, cv2.COLOR_GRAY2RGB)
            #frame_inet = frame.copy()
            for i in tanks:
                if(i.visible):
                    if(i.life): color = i.color
                    else: color = (100, 100, 100)

                    left_up = turn(i.x-(i.size/2), i.y-(i.size/1.5), i.x, i.y, i.angle)
                    right_up = turn(i.x+(i.size/2), i.y-(i.size/1.5), i.x, i.y, i.angle)
                    right_down = turn(i.x+(i.size/2), i.y+(i.size/2), i.x, i.y, i.angle)
                    left_down = turn(i.x-(i.size/2), i.y+(i.size/2), i.x, i.y, i.angle)
                    gun = turn(i.x, i.y-i.size, i.x, i.y, i.angle)

                    cv2.line(frame_inet, (int(left_up[0]), int(left_up[1])), (int(right_up[0]), int(right_up[1])), color, 2)
                    cv2.line(frame_inet, (int(right_up[0]), int(right_up[1])), (int(right_down[0]), int(right_down[1])), color, 2)
                    cv2.line(frame_inet, (int(right_down[0]), int(right_down[1])), (int(left_down[0]), int(left_down[1])), color, 2)
                    cv2.line(frame_inet, (int(left_down[0]), int(left_down[1])), (int(left_up[0]), int(left_up[1])), color, 2)
                    cv2.line(frame_inet, (int(i.x), int(i.y)), (int(gun[0]), int(gun[1])), color, 2)
                    cv2.circle(frame_inet, (int(i.x), int(i.y)), int(i.size/3), i.color, 2)

                    cv2.putText(frame_inet, i.name, (int(i.x - (len(i.name)*i.size)/8), int(i.y - i.size)), font, 0.3, color, 1, cv2.LINE_AA)

                    if(i.radar is not None):
                        if(time.time() - i.radar.time < 1):
                            for j in i.radar.points: #радар
                                cv2.line(frame_inet, j, j, (50, 50, 50), 1)
                        else:
                            i.radar = None
                    if(i.bullet is not None):
                        cv2.line(frame_inet, (int(i.bullet.x), int(i.bullet.y)), (int(i.bullet.x), int(i.bullet.y)), i.bullet.color, 5)

            frameinet = image2jpeg(frame_inet)
            yield (b'--frame\r\n'
                    b'Content-Type: image/jpeg\r\n\r\n' + frameinet + b'\r\n\r\n')
    @app.route('/video')
    def video():
        return Response(gen(),
                        mimetype='multipart/x-mixed-replace; boundary=frame')
    def gen_top():
        while True:
            frame_inet = cv2.cvtColor(frame_gray, cv2.COLOR_GRAY2RGB)
            for i in tanks:
                if(i.visible):
                    if(i.life): color = i.color
                    else: color = (100, 100, 100)

                    left_up = turn(i.x-(i.size/2), i.y-(i.size/1.5), i.x, i.y, i.angle)
                    right_up = turn(i.x+(i.size/2), i.y-(i.size/1.5), i.x, i.y, i.angle)
                    right_down = turn(i.x+(i.size/2), i.y+(i.size/2), i.x, i.y, i.angle)
                    left_down = turn(i.x-(i.size/2), i.y+(i.size/2), i.x, i.y, i.angle)
                    gun = turn(i.x, i.y-i.size, i.x, i.y, i.angle)

                    cv2.line(frame_inet, (int(left_up[0]), int(left_up[1])), (int(right_up[0]), int(right_up[1])), color, 2)
                    cv2.line(frame_inet, (int(right_up[0]), int(right_up[1])), (int(right_down[0]), int(right_down[1])), color, 2)
                    cv2.line(frame_inet, (int(right_down[0]), int(right_down[1])), (int(left_down[0]), int(left_down[1])), color, 2)
                    cv2.line(frame_inet, (int(left_down[0]), int(left_down[1])), (int(left_up[0]), int(left_up[1])), color, 2)
                    cv2.line(frame_inet, (int(i.x), int(i.y)), (int(gun[0]), int(gun[1])), color, 2)
                    cv2.circle(frame_inet, (int(i.x), int(i.y)), int(i.size/3), i.color, 2)

                    cv2.putText(frame_inet, i.name, (int(i.x - (len(i.name)*i.size)/8), int(i.y - i.size)), font, 0.3, color, 1, cv2.LINE_AA)

                    if(i.radar is not None):
                        if(time.time() - i.radar.time < 1):
                            for j in i.radar.points: #радар
                                cv2.line(frame_inet, j, j, (50, 50, 50), 1)
                        else:
                            i.radar = None
                    if(i.bullet is not None):
                        cv2.line(frame_inet, (int(i.bullet.x), int(i.bullet.y)), (int(i.bullet.x), int(i.bullet.y)), i.bullet.color, 5)

            if(len(top_10) > 0):
                for i in range(len(top_10)):
                    cv2.putText(frame_inet, str(i+1) + ": " + top_10[i].name + ", " + str(top_10[0].ip) + ", " + str(top_10[i].score),
                                (0, (i+1)*20), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 0, 255))

            frameinet = image2jpeg(frame_inet)
            yield (b'--frame\r\n'
                    b'Content-Type: image/jpeg\r\n\r\n' + frameinet + b'\r\n\r\n')
    @app.route('/video_top')
    def video_top():
        return Response(gen_top(),
                        mimetype='multipart/x-mixed-replace; boundary=frame')
    def gen_color():
        while True:
            if(cam): yield (b'--frame\r\n'
                                b'Content-Type: image/jpeg\r\n\r\n' + image2jpeg(frame.copy()) + b'\r\n\r\n')
            else: yield (b'--frame\r\n'
                                b'Content-Type: image/jpeg\r\n\r\n' + image2jpeg(frame_gray.copy()) + b'\r\n\r\n')

    @app.route('/video_color')
    def video_color():
        return Response(gen_color(),
                        mimetype='multipart/x-mixed-replace; boundary=frame')

    app.run(host='0.0.0.0', debug=False, threaded=True)

pr2 = threading.Thread(target=new_client)
pr2.start()

pr1 = threading.Thread(target=camera2inet)
pr1.start()

'''
#Пробный кадр с камеры для определения размеров поля
frame = cap.read()
hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
frame_gray = cv2.inRange(hsv, (0, 0, 0), (150, 255, 80))

moments_up = cv2.moments(frame_gray[:int(frame.shape[0]/2), int(frame.shape[1]/2)], 1)
game_ymin = int(moments_up['m01']/moments_up['m00']) + 5

moments_right = cv2.moments(frame_gray[int(frame.shape[0]/2), int(frame.shape[1]/2):], 1)
game_xmax = int(moments_right['m01']/moments_right['m00'] + int(frame.shape[1]/2)) - 5

moments_down = cv2.moments(frame_gray[int(frame.shape[0]/2):, int(frame.shape[1]/2)], 1)
game_ymax = int(moments_down['m01']/moments_down['m00'] + int(frame.shape[0]/2)) - 5

moments_left = cv2.moments(frame_gray[int(frame.shape[0]/2), :int(frame.shape[1]/2)], 1)
game_xmin = int(moments_left['m01']/moments_left['m00']) + 5

print(game_xmin, game_xmax, game_ymin, game_ymax)
'''
while 1:
    if(cam):
        frame = cap.read()
        hsv = cv2.cvtColor(frame[game_ymin:game_ymax, game_xmin:game_xmax, :], cv2.COLOR_BGR2HSV)
        frame_gray = cv2.inRange(hsv, (0, 0, 0), (150, 255, 50))
        #frame_gray = cv2.inRange(hsv, (0, 0, 0), (150, 255, 80))

    for i in tanks:
        if(i.bullet is not None):
            next_bullet_x, next_bullet_y = move(i.bullet.x, i.bullet.y, i.bullet.angle, 1)
            if(math.sqrt(math.pow(abs(i.bullet.x_start - next_bullet_x), 2) + math.pow(abs(i.bullet.y_start - next_bullet_y), 2)) < 200):
                if(5<next_bullet_x<game_xmax-game_xmin-5 and 5<next_bullet_y<game_ymax-game_ymin-5):
                    if(frame_gray[int(next_bullet_y), int(next_bullet_x)] == 0):
                        kill_tank = False
                        id_kill_tank = -1
                        for j in range(len(tanks)):
                            if((abs(next_bullet_x - tanks[j].x) < tanks[j].size/2 and
                               abs(next_bullet_y - tanks[j].y) < tanks[j].size/2)):
                                kill_tank = True
                                id_kill_tank = j

                        if(not kill_tank):
                            i.bullet.x = next_bullet_x
                            i.bullet.y = next_bullet_y
                        else:
                            i.bullet = None
                            tanks[id_kill_tank].life = False
                            tanks[id_kill_tank].time_death = time.time()
                            tanks[id_kill_tank].num_death += 1
                            i.num_murder += 1
                            print("Player", i.ip, "kill", tanks[id_kill_tank].ip, "!")

                    else: i.bullet = None
                else: i.bullet = None
            else: i.bullet = None

    if(time.time() - time_action > 0.1):
        time_action = time.time()
        for i in tanks:
            if(i.life):
                if(i.actions > 90): i.actions = 100
                else:i.actions += 10
                if(time.time() - i.time_actions > 30):
                    i.time_death = time.time()
                    i.life = False
            else:
                if(time.time() - i.time_death > 90): i.visible = False

    if(time.time() - time_top_10_update > 30 and len(tanks) > 0):
        time_top_10_update = time.time()

        next_top_10_score = []
        next_top_10_obj = []
        for i in tanks:
            score = i.num_murder*10 - i.num_death
            if(score < 0): score = 0
            next_top_10_score.append(score)
            next_top_10_obj.append(i)

        top_10.clear()
        for i in range(10):
            index_max_element = np.argmax(next_top_10_score)
            obj = next_top_10_obj.pop(index_max_element)
            top_10.append(class_top_tank(obj.ip, obj.name, obj.num_murder, obj.num_death, next_top_10_score.pop(index_max_element)))
            if(len(next_top_10_score) == 0): break
        print("---------- top_tank ------------")
        for i in top_10:
            print(i.name + ":", "ip -", i.ip, "murders -", i.murder, "death -", i.death, "score -", i.score)
        print("---------- top_tank ------------")
    time.sleep(game_speed/5)
