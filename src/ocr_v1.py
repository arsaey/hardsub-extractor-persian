import os
import pytesseract
from PIL import Image
from tqdm import tqdm  # Import tqdm for progress bar

langs = "fas"  # Persian language for OCR
config = "--psm 6 --oem 3 "  # PSM 6: uniform block of text, OEM 3: both traditional and LSTM models


# Directories for input and output files
dirname = os.path.dirname(os.path.dirname(__file__))
input_dir = os.path.join(dirname, "data")

def main(self):
    file_list = os.listdir(input_dir)  # Renamed to avoid conflict with built-in `list`
    total_len = len(file_list)
    
    solved_keys = set()
    if not self.ocr_solved_key.empty():
        solved_keys = set(self.ocr_solved_key.queue)  # Directly access the queue without blocking

    # Filter out images that have already been processed
    image_files_not_done = [filename for filename in file_list if filename.split('.')[0] not in solved_keys]
    total_len = len(image_files_not_done)  # Update total_len after filtering out done images
    
    # Wrap the filtered file list with tqdm for progress bar
    with tqdm(total=total_len, desc="Processing Images", dynamic_ncols=True) as progress_bar:
        for filename in image_files_not_done:
            if not self.ocr_running:
                break
            
            img_ext = ['.png', '.webp', '.jpg', '.jpeg', '.tiff']
            if filename.endswith(tuple(img_ext)):
                key = filename.split('.')[0]  # Extract the key from the filename


                fileAddress = os.path.join(input_dir, filename)
                
                # Ensure valid resolution before preprocessing
                img = Image.open(fileAddress)
                with self.lock:
                    self.solved_ocr = self.solved_ocr + 1
                    self.ocr_btn.setText(str(self.solved_ocr) + '/' + str(total_len))

                
                if img:
                    # Recognize the text as string in the image using pytesseract
                    try:
                        self.ocr_solved_key.put(key)
                        text = str(pytesseract.image_to_string(fileAddress, lang="fas", config=config))
                        text = os.linesep.join([s for s in text.splitlines() if s.strip()])
                        self.ocr_solved_key.put(key)
                        key = filename.split('.')[0]
                        self.ocr_final_data.put({'frame': int(key), 'text': text, 'confidence': 1})
                    except pytesseract.pytesseract.TesseractError as e:
                        print(f"Error processing image {filename}: {e}")
                        continue
                    
                    # Remove empty lines from the text
                    
                    # Update solved OCR key to prevent reprocessing

                # Update tqdm progress bar after each image
                progress_bar.update(1)
    self.end_ocr()
