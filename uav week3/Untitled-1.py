# %%
import cv2
import numpy as np
import csv

video_path = r"C:\UAV\UAV_SWARM\uav week2\grayscale material\person15_jogging_d1_uncomp.avi"
cap = cv2.VideoCapture(video_path)

if not cap.isOpened():
    print(f"Error: Video nahi mil saki!")
    exit()

bg_subtractor = cv2.createBackgroundSubtractorMOG2(history=500, varThreshold=40, detectShadows=False)

frame_number = 0
frame_log = []

###################################################
# Windows ko Bada aur Resizable Banayein (Crucial Step)
###################################################
cv2.namedWindow("1. Original Video", cv2.WINDOW_NORMAL)
cv2.namedWindow("2. Motion Mask", cv2.WINDOW_NORMAL)
cv2.namedWindow("3. Motion Edges", cv2.WINDOW_NORMAL)
cv2.namedWindow("4. Detected Jogger (Contours)", cv2.WINDOW_NORMAL)

# Default size barha kar 640x480 ya jo aap chahein set kar dein
cv2.resizeWindow("1. Original Video", 640, 480)
cv2.resizeWindow("2. Motion Mask", 640, 480)
cv2.resizeWindow("3. Motion Edges", 640, 480)
cv2.resizeWindow("4. Detected Jogger (Contours)", 640, 480)

print("Jogging Video par Motion Detection shuru... Rokne ke liye 'q' dabayein.")

while True:
    ret, frame = cap.read()
    if not ret:
        print("Video mukammal ho gayi.")
        break
        
    frame_number += 1

    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    gray_blurred = cv2.GaussianBlur(gray, (5, 5), 0)

    fg_mask = bg_subtractor.apply(gray_blurred)

    _, thresh = cv2.threshold(fg_mask, 200, 255, cv2.THRESH_BINARY)
    
    kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (5, 5))
    thresh = cv2.morphologyEx(thresh, cv2.MORPH_CLOSE, kernel)

    edges = cv2.Canny(thresh, 50, 150)

    contours, _ = cv2.findContours(
        thresh,
        cv2.RETR_EXTERNAL,
        cv2.CHAIN_APPROX_SIMPLE
    )

    contour_image = frame.copy()
    detection_count = 0

    for cnt in contours:
        area = cv2.contourArea(cnt)
        
        # Area threshold check
        if area > 800:  
            cv2.drawContours(contour_image, [cnt], -1, (0, 255, 0), 2)
            
            x, y, w, h = cv2.boundingRect(cnt)
            cv2.rectangle(contour_image, (x, y), (x + w, y + h), (255, 0, 0), 2)
            
            cv2.putText(contour_image, "Jogger", (x, y - 10), 
                        cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 0, 0), 2)
            
            detection_count = 1

    frame_log.append({
        "Frame": frame_number,
        "Detection Count": detection_count
    })

    # Show Windows (Ab ye automatic baray size mein khulein gi)
    cv2.imshow("1. Original Video", frame)
    cv2.imshow("2. Motion Mask", thresh)
    cv2.imshow("3. Motion Edges", edges)
    cv2.imshow("4. Detected Jogger (Contours)", contour_image)

    if cv2.waitKey(40) & 0xFF == ord('q'):
        break

cap.release()
cv2.destroyAllWindows()

# CSV file create karna
csv_file_path = "jogging_detection_results.csv"
with open(csv_file_path, mode='w', newline='') as file:
    fieldnames = ["Frame", "Detection Count"]
    writer = csv.DictWriter(file, fieldnames=fieldnames)
    writer.writeheader()
    for row in frame_log:
        writer.writerow(row)

print(f"\nExcel/CSV file '{csv_file_path}' successfully create ho gayi hai!")


