import os
import concurrent.futures
from contextlib import contextmanager
from tqdm import tqdm  # Import tqdm for progress bar
import threading

# Directories for input and output files
dirname = os.path.dirname(os.path.dirname(__file__))
input_dir = os.path.join(dirname, "data")
rec_model_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'persian_trained_model')
# Initialize PaddleOCR once (do not share between threads)
char_model_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'persian_trained_model')

def init_ocr(PaddleOCR):
    return PaddleOCR(debug=False, use_angle_cls=True, lang='ar', ocr_version='PP-OCRv4', use_gpu=True, show_log=False, show_warning=False, rec_model_dir=rec_model_dir )

# OcrPool for managing OCR instances
class OcrPool:
    def init(self, pool_size, PaddleOCR):
        self.available_ocrs = [init_ocr(PaddleOCR) for _ in range(pool_size)]

    @contextmanager
    def acquire(self):
        if not self.available_ocrs:
            yield None  # No available OCR objects
        else:
            ocr = self.available_ocrs.pop()
            try:
                yield ocr
            finally:
                self.available_ocrs.append(ocr)


# Process each image, checking if OCR should continue
def process_image(image_path, self, total_len, ocrpool, progress_bar):
    if not self.ocr_running:
        return  # Stop processing if ocr_running is False

    key = image_path.split('.')[0]
    image_path = os.path.join(input_dir, image_path)
    with ocrpool.acquire() as ocr:
        if ocr is None:
            print(f"No available OCR instance for {image_path}")
            return

        result = ocr.ocr(image_path)

        data = []

        for line in result:
            if not isinstance(line, list):
                self.ocr_final_data.put({'frame': int(key), 'text': '', 'confidence': 1})
                with self.lock:
                    self.solved_ocr = self.solved_ocr + 1
                    self.ocr_btn.setText(str(self.solved_ocr) + '/' + str(total_len))


                break
            for word_info in line:
                points, (text, confidence) = word_info
                x, y = points[0]
                if confidence > 0.75:
                    data.append((float(x), float(y), text, float(confidence)))

        data.sort(key=lambda item: item[1])


        lines = []
        current_line = []
        threshold = 10
        for i, item in enumerate(data):
            if i == 0 or abs(item[1] - data[i - 1][1]) <= threshold:
                current_line.append(item)
            else:
                lines.append(current_line)
                current_line = [item]
     
        if current_line:
            lines.append(current_line)
        final_text = ''

        confidence_sum = 0
        confidence_count = 0
#        lines = [line[::-1] for line in reversed(lines)]
        sorted_lines = [sorted(line, key=lambda item: item[0], reverse=False) for line in lines]
        sorted_lines.reverse()
        for line in sorted_lines:
            for word in line:
                final_text = word[2] + ' ' + final_text + ' '
                confidence_sum = confidence_sum + word[3]
                confidence_count = confidence_count + 1

            final_text =   '\r\n'  + final_text

        confidence_avg = confidence_sum / confidence_count
        self.ocr_solved_key.put(key)
        self.ocr_final_data.put({'frame': int(key), 'text': final_text.strip('\r\n'), 'confidence': confidence_avg})

        with self.lock:
            self.solved_ocr = self.solved_ocr + 1
            self.ocr_btn.setText(str(self.solved_ocr) + '/' + str(total_len))

    # Update the tqdm progress bar after each task is processed
    progress_bar.update(1)

# Main function with tqdm synchronization
def main(self):
    from paddleocr import PaddleOCR
    ocrpool = OcrPool()
    image_files = os.listdir(input_dir)
    max_workers = int(self.cpu_cores.text())  # Adjust the number of threads
    ocrpool.init(max_workers * 2, PaddleOCR)
    image_files_not_done = []
    solved_keys = set()
    if(self.ocr_version.currentText() != 'v2 (most reliable)'):
        return

    if not self.ocr_solved_key.empty():
        solved_keys = set(self.ocr_solved_key.queue)  # Directly access the queue without blocking

    image_files_not_done = [image for image in image_files if image.split('.')[0] not in solved_keys]
    total_len = len(image_files_not_done)
    # Add tqdm progress bar around the image list
    with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = []
        # Wrap the image_files_not_done with tqdm
        with tqdm(total=total_len, desc="Processing Images", dynamic_ncols=True) as progress_bar:
            for image in image_files_not_done:
                if self.ocr_running:  # Only submit the task if OCR is still running
                    # Ensure we pass progress_bar to each task correctly
                    futures.append(executor.submit(process_image, image, self, total_len, ocrpool, progress_bar))

            # Wait for all tasks to complete
            concurrent.futures.wait(futures)
    self.end_ocr()



