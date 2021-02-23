import cv2
from picamera.array import PiRGBArray
from picamera import PiCamera
import numpy as np
import pickle
import RPi.GPIO as GPIO
from time import sleep

servoPIN = 18
buzzerPIN = 17

GPIO.setwarnings(False)
GPIO.setmode(GPIO.BCM)

GPIO.setup(servoPIN, GPIO.OUT)
GPIO.setup(buzzerPIN, GPIO.OUT)

p = GPIO.PWM(servoPIN, 50)


with open('labels', 'rb') as f:
    dicti = pickle.load(f)
    f.close()

camera = PiCamera()
camera.resolution = (640, 480)
camera.framerate = 30
rawCapture = PiRGBArray(camera, size=(640, 480))


faceCascade = cv2.CascadeClassifier(
    '/usr/share/opencv/haarcascades/haarcascade_frontalface_default.xml')

recognizer = cv2.face.LBPHFaceRecognizer_create()
recognizer.read("trainer.yml")

font = cv2.FONT_HERSHEY_SIMPLEX

for frame in camera.capture_continuous(rawCapture, format="bgr", use_video_port=True):
    frame = frame.array
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    faces = faceCascade.detectMultiScale(gray, scaleFactor=1.5, minNeighbors=5)
    for (x, y, w, h) in faces:
        roiGray = gray[y:y+h, x:x+w]

        id_, conf = recognizer.predict(roiGray)

        for name, value in dicti.items():
            if value == id_:
                print("-----------------------------")
                print(name)

        if conf <= 70:
            cv2.rectangle(frame, (x, y), (x+w, y+h), (0, 255, 0), 2)
            cv2.putText(frame, name + " " + str(conf), (x, y),
                        font, 2, (0, 0, 255), 2, cv2.LINE_AA)

            # Servo Motor
            print("Door Unlocked for 5 seconds")
            p.start(2.5)
            sleep(5)
            print("Door Locked")
            p.ChangeDutyCycle(10)
            sleep(0.5)

        else:
            print("Access Denied")

            # Buzzer
            for i in range(3):
                GPIO.output(buzzerPIN, GPIO.HIGH)
                sleep(0.5)  # Delay in seconds
                GPIO.output(buzzerPIN, GPIO.LOW)
                sleep(0.5)

    cv2.imshow('frame', frame)
    key = cv2.waitKey(1)

    rawCapture.truncate(0)

    if key == 27:
        break

p.stop()
GPIO.cleanup()
cv2.destroyAllWindows()
