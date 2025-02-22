import numpy as np
from PIL import Image
import concurrent.futures
from tqdm import tqdm
import cv2
import os

def rgb_to_bgr(color):
    return [color[2], color[1], color[0]]  # Swap R and B

def isolate_specific_yellow(img,color_min,color_max):
    hsv_img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
    lower_yellow = np.array(color_min)  # Adjusted to detect subtitles
    upper_yellow = np.array(color_max)
    mask = cv2.inRange(hsv_img, lower_yellow, upper_yellow)

    kernel = np.ones((13, 13), np.uint8)  # Bigger kernel for better noise removal
    mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, kernel, iterations=22)

    contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    filtered_mask = np.zeros_like(mask)

    for cnt in contours:
        if cv2.contourArea(cnt) > 90:  # Increase threshold if necessary
            cv2.drawContours(filtered_mask, [cnt], -1, 255, thickness=cv2.FILLED)

    hsv_img = cv2.cvtColor(img, cv2.COLOR_HSV2BGR)
    hsv_img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)

    result = hsv_img.copy()

    transparent_img = np.dstack([result, np.ones_like(result[:, :, 0]) * 255])  # Add alpha channel

    transparent_img[filtered_mask < 1] = (0,0,0,0)  # Fully transparent

    img_pil = Image.fromarray(transparent_img,'RGBA')
    img = np.array(img_pil)
    return img_pil

def isolate_specific_yellow_2(img, color_min,color_max,b_filter):

    hsv_img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
    img = hsv_img

    if img is None:
        raise ValueError("Error: Image could not be loaded.")

    hsv_img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
    lower_yellow = np.array(color_min) 
    upper_yellow = np.array(color_max)

    mask = cv2.inRange(hsv_img, lower_yellow, upper_yellow)

    mask_bool = mask > 0

    white_bg = np.ones_like(img)  * 255

    white_bg[mask > 0] = img[mask > 0]

    img_pil = Image.fromarray(white_bg)

    img_pil = np.array(img_pil)
    mask = (img_pil[:, :, 0] <= b_filter)

    mask_bool = mask

    white_bg = np.ones_like(img_pil) * 255

    white_bg[mask_bool] = img_pil[mask_bool]

    img_pil = Image.fromarray(np.array(white_bg))

    return img_pil

def process_frame(frame, height, subtitle_height, subtitle_width, x_start, frame_count, color_min, color_max, b_filter, fps, frame_interval):
    curr_subtitle = frame[height - subtitle_height:height, x_start:x_start + subtitle_width]
    curr_subtitle_pil = isolate_specific_yellow(curr_subtitle, color_min, color_max)
    curr_subtitle_pil = isolate_specific_yellow_2(np.array(curr_subtitle_pil), color_min, color_max, b_filter)
    save_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "data"))
    os.makedirs(save_dir, exist_ok=True)
    curr_subtitle_pil.save(os.path.join(save_dir, f"{frame_count}.png"))

def main(self):
    if not getattr(self, "video_path", None):
        self.extract_btn.setText("Please select video file first")
        return

    cap = cv2.VideoCapture(self.video_path)
    fps = cap.get(cv2.CAP_PROP_FPS)
    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    frame_interval = int(fps * float(self.time.text()))
    
    frame_count = 0
    subtitle_height = subtitle_width = x_start = 0
    self.extract_btn.setEnabled(False)
    
    color_min = [int(val) for val in self.color_min.text().split(',')]
    color_max = [int(val) for val in self.color_max.text().split(',')]
    b_filter = int(self.b_filter.text())
    
    with tqdm(total=total_frames, desc="Processing frames", unit="frame") as progress_bar:
        with concurrent.futures.ThreadPoolExecutor(max_workers=int(self.cpu_cores.text())) as executor:
            futures = []
            while True:
                ret, frame = cap.read()
                if not ret:
                    break
                frame_count += 1
                if frame_count == 1:
                    height, width = frame.shape[:2]
                    subtitle_height = int(height * 0.38)
                    subtitle_width = int(width * 1)
                    x_start = int((width - subtitle_width) // 2) + 100
                    subtitle_width -= 100
                if frame_count % frame_interval == 0:
                    futures.append(executor.submit(process_frame, frame, height, subtitle_height, subtitle_width, x_start, frame_count, color_min, color_max, b_filter, fps, frame_interval))
                progress_bar.update(1)
                self.extract_btn.setText(f"{frame_count}/{total_frames}")
                for future in futures:
                    future.result()
        cap.release()
        self.extract_btn.setEnabled(False)
