import difflib
import cv2
import os
import time
def frame_to_timestamp(frame, fps):
    milliseconds = round((frame / fps) * 1000)
    seconds = milliseconds // 1000
    milliseconds = milliseconds % 1000
    
    hours = seconds // 3600
    minutes = (seconds % 3600) // 60
    seconds = seconds % 60

    return f"{hours:02}:{minutes:02}:{seconds:02},{milliseconds:03}"

def main(self,data, fps, similarity_threshold=0.80):
    fps = int(fps)
    if(fps == 0):
        if(getattr(self, "video_path", None)):
            cap = cv2.VideoCapture(self.video_path)
            fps = int(cap.get(cv2.CAP_PROP_FPS))
        else:
            self.srt_btn.setText('please select a video to generate srt file..')
            return
    data = list(data.queue)
    data.sort(key=lambda x: x['frame'])
    
    if not data:
        return []

    subtitles = []
    last_text = data[0]['text']
    last_confidence = data[0]['confidence']
    last_start = data[0]['frame']
    last_end = data[0]['frame']

    for entry in data[1:]:
        lev_distance = difflib.SequenceMatcher(None, last_text, entry['text']).ratio()
        confidence_diff = abs(last_confidence - entry['confidence'])

        # Key Fix: Use AND instead of OR for merging logic
        if lev_distance >= similarity_threshold :
            last_end = entry['frame']
            if entry['confidence'] > last_confidence:
                last_text = entry['text']
                last_confidence = entry['confidence']
        else:
            subtitles.append({
                'start': frame_to_timestamp(last_start, fps),
                'end': frame_to_timestamp(last_end, fps),
                'text': last_text
            })
            last_text = entry['text']
            last_confidence = entry['confidence']
            last_start = entry['frame']
            last_end = entry['frame']

    subtitles.append({
        'start': frame_to_timestamp(last_start, fps),
        'end': frame_to_timestamp(last_end, fps),
        'text': last_text
    })
    subtitles = adjust_subtitle_timings(subtitles)

    create_srt_file(subtitles,  os.path.join(os.path.dirname(os.path.dirname(__file__)),'output-'+str( int(time.time() * 1000))+'.srt'))
    print('created successfully')


def adjust_subtitle_timings(subtitles):
    # Adjust the end time of each subtitle to match the start time of the next subtitle
    for i in range(len(subtitles) - 1):
        subtitles[i]['end'] = subtitles[i + 1]['start']
    return subtitles

def create_srt_file(subtitles, output_file):
    with open(output_file, 'w', encoding='utf-8') as f:
        for index, subtitle in enumerate(subtitles, start=1):
            start_time = subtitle['start']
            end_time = subtitle['end']
            text = subtitle['text']
            
            # Write the subtitle index
            f.write(f"{index}\n")
            
            # Write the timing in SRT format
            f.write(f"{start_time} --> {end_time}\n")
            
            # Write the text (skip if empty)
            if text.strip():
                f.write(f"{text}\n")
            
            # Add an empty line between subtitles
            f.write("\n")





