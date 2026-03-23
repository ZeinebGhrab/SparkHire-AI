import sys, types as _types
for _m in ["mediapipe.tasks","mediapipe.tasks.python","mediapipe.tasks.python.audio",
           "mediapipe.tasks.python.core","mediapipe.tasks.python.vision","mediapipe.tasks.python.text"]:
    if _m not in sys.modules: sys.modules[_m]=_types.ModuleType(_m)

_mp=None
try:
    import mediapipe as _mp_mod; _mp=_mp_mod
except Exception: pass

import numpy as np, cv2, threading
from PySide6.QtWidgets import QWidget, QVBoxLayout, QLabel, QFrame, QGraphicsDropShadowEffect
from PySide6.QtCore import Qt, QTimer, Slot
from PySide6.QtGui import QImage, QPixmap, QColor, QPainter, QBrush, QFont
from pathlib import Path
sys.path.insert(0,str(Path(__file__).parent.parent.parent))
from client.ui.stark_theme import T

_W=208;_H=176;_VH=150;_MARGIN=16;_R=16


class _Dot(QWidget):
    def __init__(self,color,parent=None):
        super().__init__(parent); self._c=QColor(color); self._a=255; self._d=-6
        self.setFixedSize(8,8); t=QTimer(self); t.timeout.connect(self._tick); t.start(50)
    def set_color(self,c): self._c=QColor(c); self.update()
    def _tick(self):
        self._a=max(60,min(255,self._a+self._d))
        if self._a<=60: self._d=6
        elif self._a>=255: self._d=-6
        self.update()
    def paintEvent(self,_):
        p=QPainter(self); p.setRenderHint(QPainter.RenderHint.Antialiasing)
        c=QColor(self._c); c.setAlpha(self._a)
        p.setBrush(QBrush(c)); p.setPen(Qt.PenStyle.NoPen); p.drawEllipse(0,0,8,8)


class CameraPreviewWidget(QWidget):
    def __init__(self,parent=None):
        super().__init__(parent)
        self.setWindowFlags(Qt.WindowType.SubWindow)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setFixedSize(_W+4,_H+4)
        self._recording=False; self._has_camera=False; self._no_signal=True; self._blink=True
        self._mp_ready=False; self._face_mesh=None
        self._rt_lock=threading.Lock(); self._last_metrics={}; self._eval_metrics={}
        self._blink_timer=QTimer(self); self._blink_timer.setInterval(600)
        self._blink_timer.timeout.connect(self._toggle_blink)
        self._metrics_timer=QTimer(self); self._metrics_timer.setInterval(400)
        self._metrics_timer.timeout.connect(self._refresh_metrics_overlay); self._metrics_timer.start()
        self._init_mp(); self._build(); self._show_placeholder()

    def _init_mp(self):
        try:
            mp=_mp
            if mp is None:
                import mediapipe as mp
            self._face_mesh=mp.solutions.face_mesh.FaceMesh(
                static_image_mode=False,max_num_faces=1,refine_landmarks=True,
                min_detection_confidence=0.5,min_tracking_confidence=0.5)
            self._mp_ready=True; print("[CamPreview] MediaPipe OK")
        except ImportError: print("[CamPreview] pip install mediapipe==0.10.14")
        except Exception as e: print(f"[CamPreview] {str(e).split(chr(10))[0][:100]}")

    def _build(self):
        root=QVBoxLayout(self); root.setContentsMargins(2,2,2,2); root.setSpacing(0)
        self._frame=QFrame(); self._frame.setFixedSize(_W,_H)
        self._frame.setStyleSheet(f"""QFrame{{
            background:{T.BG_CARD};border:1px solid {T.BORDER_GLASS};border-radius:{_R}px;
        }}""")
        sh=QGraphicsDropShadowEffect(); sh.setBlurRadius(20); sh.setOffset(0,6)
        sh.setColor(QColor(0,200,224,35)); self._frame.setGraphicsEffect(sh)
        inner=QVBoxLayout(self._frame); inner.setContentsMargins(0,0,0,0); inner.setSpacing(0)
        self._img=QLabel(); self._img.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._img.setStyleSheet(f"""QLabel{{
            background:rgba(0,200,224,0.05);
            border-top-left-radius:{_R-2}px;border-top-right-radius:{_R-2}px;
            border-bottom-left-radius:{_R-2}px;border-bottom-right-radius:{_R-2}px;
        }}""")
        self._img.setFixedSize(_W-4,_H-4)
        inner.addWidget(self._img,alignment=Qt.AlignmentFlag.AlignCenter)
        self._rec=QLabel(" ● REC ",self._img)
        self._rec.setFont(QFont(T.FONT,6,QFont.Weight.Bold))
        self._rec.setStyleSheet(f"color:#fff;background:{T.RED_500};border-radius:4px;padding:1px 5px;")
        self._rec.move(7,7); self._rec.setVisible(False)
        root.addWidget(self._frame)

    def _analyze(self,frame_bgr):
        if not self._mp_ready or not self._face_mesh: return {}
        try:
            h,w=frame_bgr.shape[:2]
            if w>320: s=320/w; frame_bgr=cv2.resize(frame_bgr,(320,int(h*s)))
            rgb=cv2.cvtColor(frame_bgr,cv2.COLOR_BGR2RGB); res=self._face_mesh.process(rgb)
            if not res.multi_face_landmarks: return {"face":False}
            lm=res.multi_face_landmarks[0].landmark
            def ear(t,b,o,i): return abs(lm[t].y-lm[b].y)/(abs(lm[o].x-lm[i].x)+1e-6)
            blink=(ear(159,145,33,133)+ear(386,374,263,362))/2<0.20
            def ioff(ir,o,i,t,b):
                cx=(lm[o].x+lm[i].x)/2; cy=(lm[t].y+lm[b].y)/2
                ew=abs(lm[o].x-lm[i].x)+1e-6; return (lm[ir].x-cx)/ew,(lm[ir].y-cy)/ew
            ox=(ioff(468,33,133,159,145)[0]+ioff(473,263,362,386,374)[0])/2
            oy=(ioff(468,33,133,159,145)[1]+ioff(473,263,362,386,374)[1])/2
            ec=abs(ox)<0.35 and abs(oy)<0.28 and not blink
            yaw=abs(lm[454].x-lm[234].x-0.5)*60; st=max(0.0,min(1.0,1.0-yaw/30))
            ed=abs(lm[33].x-lm[263].x)+1e-6
            cu=max(0.0,((lm[13].y+lm[14].y)/2-(lm[61].y+lm[291].y)/2)/ed*3)
            bf=max(0.0,min(1.0,(0.55-abs(lm[107].x-lm[336].x)/ed)*5))
            br=max(0.0,min(1.0,((lm[159].y-lm[107].y)+(lm[386].y-lm[336].y))/ed*2))
            mar=abs(lm[13].y-lm[14].y)/(abs(lm[61].x-lm[291].x)+1e-6)
            if cu>0.25: em="happy"
            elif bf>0.30: em="angry"
            elif br>0.40 and mar>0.25: em="surprise"
            elif br>0.30: em="fear"
            else: em="neutral"
            return {"face":True,"eye_contact":ec,"stability":st,"emotion":em,
                    "confidence":min(10,max(0,(1 if ec else 0)*3.5+st*2.5+cu*2.0-bf*3.0)),
                    "stress":min(10,max(0,bf*3.5+(1-st)*2+(1-(1 if ec else 0))*2-cu*1.5))}
        except Exception: return {"face":False}

    @Slot(bytes)
    def on_frame(self,jpeg_bytes):
        try:
            buf=np.frombuffer(jpeg_bytes,dtype=np.uint8); frame=cv2.imdecode(buf,cv2.IMREAD_COLOR)
            if frame is None: return
            threading.Thread(target=lambda f:[self._rt_lock.__enter__(),
                self._last_metrics.update(self._analyze(f)),
                self._rt_lock.__exit__(None,None,None)],args=(frame.copy(),),daemon=True).start()
            frame=cv2.flip(frame,1); rgb=cv2.cvtColor(frame,cv2.COLOR_BGR2RGB)
            h,w,c=rgb.shape; tw,th=_W-4,_VH; r=min(tw/w,th/h)
            nw,nh=int(w*r),int(h*r); rs=cv2.resize(rgb,(nw,nh),interpolation=cv2.INTER_AREA)
            with self._rt_lock: fok=self._last_metrics.get("face",False)
            cv2.rectangle(rs,(1,1),(nw-2,nh-2),(0,200,224) if fok else (180,225,232),2)
            self._img.setPixmap(QPixmap.fromImage(QImage(rs.data.tobytes(),nw,nh,nw*c,QImage.Format.Format_RGB888)))
            if self._no_signal: self._no_signal=False; self._has_camera=True
        except Exception: pass

    def set_recording(self,r):
        self._recording=r; self._rec.setVisible(r)
        if r: self._blink_timer.start()
        else: self._blink_timer.stop(); self._rec.setVisible(False)

    def set_facial_result(self,m): pass
    def set_camera_unavailable(self): self._has_camera=False; self._show_placeholder()
    def _refresh_metrics_overlay(self): pass
    def _toggle_blink(self): self._blink=not self._blink; self._rec.setVisible(self._blink and self._recording)

    def _show_placeholder(self):
        w,h=_W-4,_VH; img=np.ones((h,w,3),dtype=np.uint8)
        img[:,:,0]=232; img[:,:,1]=248; img[:,:,2]=250
        cx,cy=w//2,h//2
        cv2.rectangle(img,(cx-24,cy-15),(cx+24,cy+15),(180,225,232),-1)
        cv2.rectangle(img,(cx-24,cy-15),(cx+24,cy+15),(0,200,224),1)
        cv2.circle(img,(cx,cy),8,(0,200,224),-1); cv2.circle(img,(cx,cy),4,(232,248,250),-1)
        cv2.fillPoly(img,[np.array([[cx+24,cy-9],[cx+33,cy-16],[cx+33,cy+16],[cx+24,cy+9]])],(180,225,232))
        self._img.setPixmap(QPixmap.fromImage(QImage(img.tobytes(),w,h,w*3,QImage.Format.Format_RGB888)))

    def reposition(self):
        if self.parent(): self.move(_MARGIN,self.parent().height()-self.height()-_MARGIN)

    def cleanup(self):
        if self._face_mesh:
            try: self._face_mesh.close()
            except Exception: pass
            self._face_mesh=None