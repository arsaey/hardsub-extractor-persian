import os
import sys
import ocr_v1
import ocr_v2
import threading
from PyQt6.QtCore import *
from PyQt6.QtWidgets import QDoubleSpinBox,QApplication, QWidget, QPushButton, QVBoxLayout, QFileDialog, QLineEdit, QLabel, QSpinBox, QComboBox, QFormLayout
import extract_frame
import queue
import create_subtitle_file
class SubExtractorApp(QWidget):
    def __init__(self):
        super().__init__()
        self.setFixedSize(400, 520)  # اندازه ثابت
        self.setMaximumSize(400, 520)  # اندازه ثابت
        self.initUI()
        
        self.ocr_running = False

    def initUI(self):
        self.fps = 0
        self.lock = threading.Lock()
        self.solved_ocr = 0
        self.ocr_solved_key = queue.Queue()
        self.ocr_final_data = queue.Queue()

        layout = QVBoxLayout()  # تنظیم Layout اصلی به صورت عمودی
        layout.setContentsMargins(10, 10, 10, 10)  # حذف حاشیه‌های اضافی
        layout.setSpacing(5)  # فاصله کم بین ویجت‌ها
        # Video Selection
        self.video_label = QLabel("Select a video:")
        self.video_input = QPushButton("Browse Video")
        self.video_input.clicked.connect(self.browse_video)
        
        layout.addWidget(self.video_label)
        layout.addWidget(self.video_input)
        
        # Color Range Inputs
        self.range_label = QLabel("Set color range (min-max):")
        self.color_min = QLineEdit("205,205,0")
        self.color_max = QLineEdit("255,255,255")
        self.b_filter  = QLineEdit("85")

        layout.addWidget(self.range_label)
        layout.addWidget(self.color_min)
        layout.addWidget(QLabel("Max color:"))
        layout.addWidget(self.color_max)
        layout.addWidget(QLabel("B Filter"))
        layout.addWidget(self.b_filter)

        self.cpu_label = QLabel("Select CPU cores:")
        self.cpu_cores = QSpinBox()
        self.cpu_cores.setMinimum(1)
        self.cpu_cores.setMaximum(os.cpu_count())
        self.cpu_cores.setValue(1)

        layout.addWidget(self.cpu_label)
        layout.addWidget(self.cpu_cores)



        self.time_label = QLabel("Each x second:")
        self.time = QDoubleSpinBox()
        self.time.setMinimum(0.01)
        self.time.setMaximum(30)
        self.time.setValue(0.5)
        
        layout.addWidget(self.time_label)
        layout.addWidget(self.time)
        
        # OCR Version Selection
        self.ocr_version_label = QLabel("Select OCR Version:")
        self.ocr_version = QComboBox()
        self.ocr_version.addItems(["v1 (fastest)", "v2 (most reliable)", "v3 (disabled)"])
          # Extract Frames Button
        self.extract_btn = QPushButton("Extract Frames")
        self.extract_btn.clicked.connect(self.extract_frames)
        self.extract_btn.setEnabled(True)
        layout.addWidget(self.extract_btn)
       
        layout.addWidget(self.ocr_version_label)
        layout.addWidget(self.ocr_version)
        
       
        # OCR Button
        self.ocr_btn = QPushButton("Start OCR")
        self.ocr_btn.clicked.connect(self.start_ocr)
        self.ocr_btn.setEnabled(True)
        layout.addWidget(self.ocr_btn)
        
        # Stop OCR Button
        self.stop_btn = QPushButton("Stop OCR")
        self.stop_btn.clicked.connect(self.stop_ocr)
        self.stop_btn.setEnabled(False)
        layout.addWidget(self.stop_btn)
       
        self.srt_btn = QPushButton("Create srt by current ocr data")
        self.srt_btn.clicked.connect(self.srt_generate)
        self.srt_btn.setEnabled(False)
        layout.addWidget(self.srt_btn)
        
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.check_queue)
        self.timer.start(1000)  # Check every 1000 ms (1 second)

# در صورت نیاز به تغییر نمایش پنجره
        self.setWindowFlags(self.windowFlags() & ~Qt.WindowType.WindowMinimizeButtonHint & ~Qt.WindowType.WindowMaximizeButtonHint)
        self.setLayout(layout)
        self.setWindowTitle("SubExtractor Video Processor")
     
        self.show()
    
    def browse_video(self):
        file_name, _ = QFileDialog.getOpenFileName(self, "Select Video", "", "Video Files (*.mp4 *.avi *.mkv)")
        if file_name:
            self.video_label.setText(f"Selected: {file_name}")
            self.video_path = file_name
    
    def extract_frames(self):
        threading.Thread(target=extract_frame.main,args=(self,), daemon=True).start()
    
    
    def start_ocr(self):
        if not self.ocr_running:
            threading.Thread(target=self.run_ocr, daemon=True).start()
    
    def run_ocr(self):
        self.solved_ocr = 0
        ocr_version = self.ocr_version.currentText()
        self.ocr_btn.setEnabled(False)
        self.ocr_running = True
        self.stop_btn.setEnabled(True)
           
        if(ocr_version == 'v1 (fastest)'):
            ocr_v1.main(self)
        elif(ocr_version == 'v2 (most reliable)'):
            ocr_v2.main(self)
        
        elif(ocr_version == 'v3 (disabled)'):
            self.ocr_btn.setEnabled(True)
            self.stop_btn.setEnabled(False)

        
    
    def stop_ocr(self):
        self.ocr_running = False
        self.stop_btn.setEnabled(False)
        self.ocr_btn.setEnabled(True)
        print("Stopping OCR...")

    def end_ocr(self):
        self.ocr_running = False
        self.stop_btn.setEnabled(False)
        self.ocr_btn.setEnabled(True)
        print("Ending OCR...")
    
    def srt_generate(self):
        create_subtitle_file.main(self,self.ocr_final_data,self.fps)
        
    def check_queue(self):
        """Check if the queue has items and enable the button if it does."""
        if not self.ocr_final_data.empty():
            self.srt_btn.setEnabled(True)  # Enable the button
        else:
            self.srt_btn.setEnabled(False)  # Disable the button if the queue is empty

if __name__ == '__main__':
    save_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "data"))
    os.makedirs(save_dir, exist_ok=True)
    app = QApplication(sys.argv)
    ex = SubExtractorApp()
    sys.exit(app.exec())
