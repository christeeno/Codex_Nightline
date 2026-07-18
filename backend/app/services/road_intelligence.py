"""Confirm potholes across adjacent sampled road frames."""
from dataclasses import dataclass
from pathlib import Path
from collections.abc import Iterable
import time
import numpy as np
from app.adapters import PotholeDetectionAdapter
from app.core.config import Settings,get_settings
from app.schemas import BoundingBox,Detection,ProcessingStatistics,RoadAnalysisResult

@dataclass(frozen=True)
class SampledFrame:
    image: np.ndarray
    frame_number: int
    timestamp: float
    vehicle_boxes: tuple[BoundingBox,...]=()

class RoadIntelligenceEngine:
    def __init__(self,frame_source:object|None=None,adapter:PotholeDetectionAdapter|None=None,settings:Settings|None=None):self._settings=settings or get_settings();self._adapter=adapter or PotholeDetectionAdapter(self._settings);self._frame_source=frame_source
    def analyze_video(self,video_path:str|Path,frames:Iterable[SampledFrame]|None=None)->RoadAnalysisResult:
        start=time.perf_counter(); stats=ProcessingStatistics(video_path=str(video_path)); candidates=[]
        try:
            if frames is None: raise RuntimeError('No Processing Pipeline FrameSource is configured')
            for index,frame in enumerate(frames):
                stats.frames_processed+=1
                for box,confidence in self._adapter.detect(frame.image):
                    if not any(_iou(box,v)>=self._settings.vehicle_overlap_threshold for v in frame.vehicle_boxes) and (not self._settings.roi_enabled or (box.y1+box.y2)/2>=frame.image.shape[0]*self._settings.road_roi_top_ratio):candidates.append((index,frame,box,confidence))
        except Exception as exc:stats.errors.append(f'Road intelligence processing failed: {exc}')
        stats.candidate_detections=len(candidates);events=[]
        for candidate in candidates:
            if events and candidate[0]==events[-1][-1][0]+1 and _iou(events[-1][-1][2],candidate[2])>=self._settings.pothole_event_iou:events[-1].append(candidate)
            else:events.append([candidate])
        detections=[]
        for number,event in enumerate(events,1):
            if len(event)<self._settings.min_consecutive_frames:continue
            _,frame,box,confidence=max(event,key=lambda x:x[3]);detections.append(Detection(type='POTHOLE',timestamp=frame.timestamp,frame_number=frame.frame_number,confidence=confidence,bounding_box=box,tracking_id=f'pothole-{number:04d}',metadata={'source':'PeterHdd/pothole-detection-yolo','sampled_frame_count':len(event)}))
        elapsed=time.perf_counter()-start;stats.confirmed_potholes=len(detections);stats.inference_seconds=round(elapsed,4);stats.average_fps=round(stats.frames_processed/elapsed,3) if elapsed else 0;return RoadAnalysisResult(detections=detections,statistics=stats)
def _iou(a:BoundingBox,b:BoundingBox)->float:
    l,t,r,bottom=max(a.x1,b.x1),max(a.y1,b.y1),min(a.x2,b.x2),min(a.y2,b.y2);inter=max(0,r-l)*max(0,bottom-t);union=a.area+b.area-inter;return inter/union if union else 0
