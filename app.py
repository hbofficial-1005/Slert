from flask import Flask, redirect, url_for, render_template
import cv2
import dlib 
from imutils import face_utils
import playsound
from scipy.spatial import distance as dist
import threading
import numpy as np
from datetime import datetime
from cryptography.fernet import Fernet
app = Flask(__name__)
@app.route('/')
def home():
	return render_template("index.html")

@app.route('/index')
def index():
	EYE_AR_THRESH = 0.25
	EYE_AR_CONSEC_FRAMES = 50
	YAWN_AR_CONSEC_FRAMES = 50
	YAWN_THRESH = 20
	COUNTER_EAR = 0
	COUNTER_YAWN = 0
	ALARM_ON_eye = False
	ALARM_ON_yawn = False

	(lstart , lend) = face_utils.FACIAL_LANDMARKS_IDXS['left_eye']
	(rstart , rend) = face_utils.FACIAL_LANDMARKS_IDXS['right_eye']
	(mstart, mend) = face_utils.FACIAL_LANDMARKS_IDXS['mouth']

	sleep_count = 0
	yawn_count = 0
	p = "shape_predictor_68_face_landmarks.dat"
	detector = dlib.get_frontal_face_detector()
	predictor = dlib.shape_predictor(p)

	trip_start = datetime.now()
	trip_start_string = trip_start.strftime("%d/%m/%Y %H:%M:%S")

	sleep_list = []
	yawn_list = []

	trip_history = open(r"history.txt", "a")

	cap = cv2.VideoCapture(0)

	key = Fernet.generate_key()
	file = open('key.key', 'wb')
	file.write(key)
	file.close()
	 
	while True:
	    
	    _, image = cap.read()
	    
	    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
	        
	    
	    rects = detector(gray, 0)
	    
	   
	    for rect in rects:
	        
	        shape = predictor(gray, rect)
	        shape = face_utils.shape_to_np(shape)
	        left_eye = shape[lstart:lend]
	        right_eye = shape[rstart:rend]
	        mouth = shape[mstart:mend]
	        ear_right = ear_e(right_eye)
	        ear_left = ear_e(left_eye)
	        
	        distance = lip_distance(shape)
	        
	        ear = (ear_left+ear_right)/2.0
	        
	        leftEyeHull = cv2.convexHull(left_eye)
	        rightEyeHull = cv2.convexHull(right_eye)
	        #cv2.drawContours(image, [leftEyeHull], -1, (255, 0, 0), 1)
	        #cv2.drawContours(image, [rightEyeHull], -1, (255, 0, 0), 1)
	        cv2.drawContours(image, [mouth], -1, (255, 0, 0), 1)
	       
	        if (ear <= EYE_AR_THRESH or distance > YAWN_THRESH):
	            if ear <= EYE_AR_THRESH:
	                COUNTER_EAR += 1
	            if distance > YAWN_THRESH:
	                COUNTER_YAWN += 1
	                
	            
	            #Eye Alert
	            if COUNTER_EAR >= EYE_AR_CONSEC_FRAMES:
	                if not ALARM_ON_eye:
	                    ALARM_ON_eye = True
	                    
	                    x=threading.Thread(target=alarm('alarm_sound_trim.mp3'))
	                    x.start()
	                    sleep_count +=1
	                    sleep_time = datetime.now()
	                    sleep_time_string = sleep_time.strftime("%d/%m/%Y %H:%M:%S")
	                    sleep_list.append(sleep_time_string)
	                cv2.putText(image , 'SLEEP ALERT!' ,(10,30), cv2.FONT_HERSHEY_SIMPLEX ,0.7, (0,255,30) , 2)
	            
	            #Yawn Alert
	            if COUNTER_YAWN >= YAWN_AR_CONSEC_FRAMES:
	                if not ALARM_ON_yawn:
	                    ALARM_ON_yawn = True
	                
	                    m = threading.Thread(target=alarm('alarm_sound_trim.mp3'))                 
	                    m.start()
	                    yawn_count += 1
	                    yawn_time= datetime.now()
	                    yawn_time_string = yawn_time.strftime("%d/%m/%Y %H:%M:%S")
	                    yawn_list.append(yawn_time_string)
	                cv2.putText(image , 'YAWN ALERT!' , (10,60), cv2.FONT_HERSHEY_SIMPLEX ,0.7, (0,255,30) , 2)
	        else:
	            COUNTER_EAR = 0
	            COUNTER_YAWN = 0
	            ALARM_ON_eye = False
	            ALARM_ON_yawn = False
	        #cv2.putText(image, "EAR: {:.2f}".format(ear), (300, 30),cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 2)    
	        #cv2.putText(image, "YAWN: {:.2f}".format(distance), (300, 60), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 2)
	        
	    
	    cv2.imshow("Output", image)
	    
	    
	    k = cv2.waitKey(5) & 0xFF
	    if k == ord('q'):
	        trip_end = datetime.now()
	        trip_end_string = trip_end.strftime("%d/%m/%Y %H:%M:%S")
	        break

	cv2.destroyAllWindows()
	
	#print("You have slept " + str(sleep_count) + " time(s).")
	#print("You have yawned " + str(yawn_count) + " time(s).")
	cap.release()
	result = f"Trip duration: {trip_start_string} to {trip_end_string}, You have slept {sleep_count} time(s) at {sleep_list}, and yawned {yawn_count} time(s) at {yawn_list} during your trip.\n"
	trip_history.writelines(result)
	trip_history.close()

	input_file = 'history.txt'
	output_file = 'history_encrypted.encrypted'

	with open(input_file, 'rb') as f:
	    data = f.read()

	fernet = Fernet(key)
	encrypted = fernet.encrypt(data)

	with open(output_file, 'wb') as f:
	    f.write(encrypted)

	input_file2 = 'history_encrypted.encrypted'
	output_file2 = 'history_decrypted.txt'

	with open(input_file2, 'rb') as f:
	    data = f.read()

	#fernet = Fernet(key)
	decrypted = fernet.decrypt(data)

	with open(output_file2, 'wb') as f:
	    f.write(decrypted)

	return result
	#return redirect(url_for("result",sleep=sleep_count,yawn=yawn_count))

def ear_e(eye):
    A = dist.euclidean(eye[1], eye[5])
    B = dist.euclidean(eye[2], eye[4]) 
    C = dist.euclidean(eye[0], eye[3])
    ear = (A + B) / (2.0 * C)
    return ear

def alarm(path):
    playsound.playsound(path, block= False)
	    

def lip_distance(shape):
    top_lip = shape[50:53]
    top_lip = np.concatenate((top_lip, shape[61:64]))
    low_lip = shape[56:59]
    low_lip = np.concatenate((low_lip, shape[65:68]))

    top_mean = np.mean(top_lip, axis=0)
    low_mean = np.mean(low_lip, axis=0)

    distance = abs(top_mean[1] - low_mean[1])
    return distance

#@app.route("/result")
#def result(sleep,yawn):
	