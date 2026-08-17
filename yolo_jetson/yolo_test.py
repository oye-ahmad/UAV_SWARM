import os
import sys
import argparse
import glob

import cv2
from ultralytics import YOLO


# ---------------------------------------------------------
# 1. Define command-line arguments
# ---------------------------------------------------------

parser = argparse.ArgumentParser()

parser.add_argument(
    '--model',
    help='Path to YOLO model file, e.g. "runs/detect/train/weights/best.pt"',
    required=True
)

parser.add_argument(
    '--source',
    help='Path to folder containing input images',
    required=True
)

parser.add_argument(
    '--thresh',
    help='Minimum confidence threshold for displaying detections',
    default=0.5
)

parser.add_argument(
    '--resolution',
    help='Optional output resolution in WxH, e.g. "640x480"',
    default=None
)

args = parser.parse_args()


# ---------------------------------------------------------
# 2. Parse arguments
# ---------------------------------------------------------

model_path = args.model
input_folder = args.source
min_thresh = float(args.thresh)
user_res = args.resolution


# ---------------------------------------------------------
# 3. Check model
# ---------------------------------------------------------

if not os.path.exists(model_path):
    print("ERROR: Model path is invalid or model was not found.")
    sys.exit(0)


# ---------------------------------------------------------
# 4. Check input folder
# ---------------------------------------------------------

if not os.path.isdir(input_folder):
    print(f"ERROR: Input folder does not exist: {input_folder}")
    sys.exit(0)


# ---------------------------------------------------------
# 5. Create output folder
# ---------------------------------------------------------

# Example:
# input_folder = "dataset/test"
# output_folder = "dataset/test_results"

parent_directory = os.path.dirname(input_folder)
folder_name = os.path.basename(os.path.normpath(input_folder))

output_folder = os.path.join(
    parent_directory,
    folder_name + "_results"
)

os.makedirs(output_folder, exist_ok=True)

print(f"Input folder : {input_folder}")
print(f"Output folder: {output_folder}")


# ---------------------------------------------------------
# 6. Load YOLO model
# ---------------------------------------------------------

model = YOLO(model_path, task='detect')

labels = model.names


# ---------------------------------------------------------
# 7. Supported image extensions
# ---------------------------------------------------------

img_ext_list = [
    '.jpg', '.JPG',
    '.jpeg', '.JPEG',
    '.png', '.PNG',
    '.bmp', '.BMP'
]


# ---------------------------------------------------------
# 8. Get all images from folder
# ---------------------------------------------------------

imgs_list = []

for file in glob.glob(os.path.join(input_folder, '*')):

    _, file_ext = os.path.splitext(file)

    if file_ext in img_ext_list:
        imgs_list.append(file)


# Sort images for consistent processing order
imgs_list.sort()


if len(imgs_list) == 0:
    print("ERROR: No images found in the input folder.")
    sys.exit(0)


print(f"Found {len(imgs_list)} images.")


# ---------------------------------------------------------
# 9. Optional output resolution
# ---------------------------------------------------------

resize = False

if user_res:

    resize = True

    resW, resH = map(
        int,
        user_res.lower().split('x')
    )


# ---------------------------------------------------------
# 10. Bounding box colors
# ---------------------------------------------------------

bbox_colors = [
    (164, 120, 87),
    (68, 148, 228),
    (93, 97, 209),
    (178, 182, 133),
    (88, 159, 106),
    (96, 202, 231),
    (159, 124, 168),
    (169, 162, 241),
    (98, 118, 150),
    (172, 176, 184)
]


# ---------------------------------------------------------
# 11. Process every image
# ---------------------------------------------------------

for img_count, img_filename in enumerate(imgs_list, start=1):

    print(
        f"[{img_count}/{len(imgs_list)}] "
        f"Processing: {os.path.basename(img_filename)}"
    )


    # -----------------------------------------------------
    # Read image
    # -----------------------------------------------------

    frame = cv2.imread(img_filename)

    if frame is None:
        print(f"WARNING: Could not read {img_filename}")
        continue


    # -----------------------------------------------------
    # Resize image if requested
    # -----------------------------------------------------

    if resize:

        frame = cv2.resize(
            frame,
            (resW, resH)
        )


    # -----------------------------------------------------
    # Run YOLO inference
    # -----------------------------------------------------

    results = model(
        frame,
        verbose=False
    )


    # Get detections
    detections = results[0].boxes


    # Count detected objects
    object_count = 0


    # -----------------------------------------------------
    # Process each detection
    # -----------------------------------------------------

    for i in range(len(detections)):

        # ---------------------------------------------
        # Bounding box coordinates
        # ---------------------------------------------

        xyxy_tensor = detections[i].xyxy.cpu()

        xyxy = xyxy_tensor.numpy().squeeze()

        xmin, ymin, xmax, ymax = xyxy.astype(int)


        # ---------------------------------------------
        # Class ID and class name
        # ---------------------------------------------

        classidx = int(
            detections[i].cls.item()
        )

        classname = labels[classidx]


        # ---------------------------------------------
        # Confidence
        # ---------------------------------------------

        conf = detections[i].conf.item()


        # ---------------------------------------------
        # Confidence threshold
        # ---------------------------------------------

        if conf > min_thresh:

            color = bbox_colors[classidx % 10]


            # -----------------------------------------
            # Draw bounding box
            # -----------------------------------------

            cv2.rectangle(
                frame,
                (xmin, ymin),
                (xmax, ymax),
                color,
                2
            )


            # -----------------------------------------
            # Create label
            # -----------------------------------------

            label = f'{classname}: {int(conf * 100)}%'


            # -----------------------------------------
            # Calculate label size
            # -----------------------------------------

            labelSize, baseLine = cv2.getTextSize(
                label,
                cv2.FONT_HERSHEY_SIMPLEX,
                0.5,
                1
            )


            label_ymin = max(
                ymin,
                labelSize[1] + 10
            )


            # -----------------------------------------
            # Draw label background
            # -----------------------------------------

            cv2.rectangle(
                frame,
                (
                    xmin,
                    label_ymin - labelSize[1] - 10
                ),
                (
                    xmin + labelSize[0],
                    label_ymin + baseLine - 10
                ),
                color,
                cv2.FILLED
            )


            # -----------------------------------------
            # Draw label text
            # -----------------------------------------

            cv2.putText(
                frame,
                label,
                (xmin, label_ymin - 7),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.5,
                (0, 0, 0),
                1
            )


            # Increment object counter
            object_count += 1


    # -----------------------------------------------------
    # Draw total object count
    # -----------------------------------------------------

    cv2.putText(
        frame,
        f'Number of objects: {object_count}',
        (10, 30),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.7,
        (0, 255, 255),
        2
    )


    # -----------------------------------------------------
    # Generate output filename
    # -----------------------------------------------------

    filename = os.path.basename(img_filename)

    output_path = os.path.join(
        output_folder,
        filename
    )


    # -----------------------------------------------------
    # Save result
    # -----------------------------------------------------

    cv2.imwrite(
        output_path,
        frame
    )


print("\n========================================")
print("Processing completed successfully!")
print(f"Results saved in:")
print(output_folder)
print("========================================")