import cv2, pygame, numpy as np
from PySide6.QtWidgets import QWidget, QVBoxLayout, QLabel, QFrame, QHBoxLayout, QGraphicsDropShadowEffect
from PySide6.QtCore import Qt, QTimer, Slot, QSize
from PySide6.QtGui import QFont, QImage, QPixmap, QColor, QPainter, QBrush
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).parent.parent.parent))
from client.ui.stark_theme import T
from client.ui.icons import StarkIcons


def _sh(blur=28,dy=12,alpha=18,r=0,g=200,b=224):
    s=QGraphicsDropShadowEffect(); s.setBlurRadius(blur); s.setOffset(0,dy)
    s.setColor(QColor(r,g,b,alpha)); return s


class _Dot(QWidget):
    def __init__(self,color,parent=None):
        super().__init__(parent); self._c=QColor(color); self._a=255; self._d=-5
        self.setFixedSize(10,10); t=QTimer(self); t.timeout.connect(self._tick); t.start(50)
    def set_color(self,c): self._c=QColor(c); self.update()
    def _tick(self):
        self._a+=self._d
        if self._a<=60: self._d=5
        elif self._a>=255: self._d=-5
        self.update()
    def paintEvent(self,_):
        p=QPainter(self); p.setRenderHint(QPainter.RenderHint.Antialiasing)
        h=QColor(self._c); h.setAlpha(max(0,self._a//6))
        p.setBrush(QBrush(h)); p.setPen(Qt.PenStyle.NoPen); p.drawEllipse(0,0,10,10)
        c=QColor(self._c); c.setAlpha(self._a)
        p.setBrush(QBrush(c)); p.drawEllipse(2,2,6,6)


class VideoPlayerWidget(QWidget):
    def __init__(self,parent=None):
        super().__init__(parent)
        root=QVBoxLayout(self); root.setContentsMargins(0,0,0,0); root.setSpacing(0)

        # Carte glass
        wrapper=QFrame(); wrapper.setObjectName("vw")
        wrapper.setStyleSheet(f"""
            #vw{{
                background:{T.BG_CARD};
                border:1px solid {T.BORDER_GLASS};
                border-radius:{T.R_XL}px;
            }}
        """)
        wrapper.setGraphicsEffect(_sh(44,16,16))
        wl=QVBoxLayout(wrapper); wl.setContentsMargins(0,0,0,0); wl.setSpacing(0)

        # Zone vidéo
        self.avatar_display=QLabel()
        self.avatar_display.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.avatar_display.setStyleSheet(f"""
            QLabel{{
                background:qlineargradient(x1:0.5,y1:0,x2:0.5,y2:1,
                    stop:0 rgba(0,200,224,0.05),stop:0.5 {T.BG_CARD},stop:1 rgba(0,169,157,0.04));
                border:none;
                border-top-left-radius:{T.R_XL}px;
                border-top-right-radius:{T.R_XL}px;
            }}
        """)
        self.avatar_display.setMinimumSize(800,540)
        wl.addWidget(self.avatar_display,stretch=1)

        # Status bar
        bar=QFrame(); bar.setObjectName("sb"); bar.setFixedHeight(70)
        bar.setStyleSheet(f"""
            #sb{{
                background:rgba(255,255,255,0.75);
                border-top:1px solid rgba(255,255,255,0.70);
                border-bottom-left-radius:{T.R_XL}px;
                border-bottom-right-radius:{T.R_XL}px;
            }}
        """)
        bl=QHBoxLayout(bar); bl.setContentsMargins(22,0,22,0); bl.setSpacing(14)

        self._ic=QFrame(); self._ic.setFixedSize(44,44)
        self._ic.setStyleSheet(f"""QFrame{{
            background:qlineargradient(x1:0,y1:0,x2:1,y2:1,stop:0 {T.CYAN_500},stop:1 {T.TEAL_500});
            border-radius:13px;border:none;
        }}""")
        self._ic.setGraphicsEffect(_sh(14,5,35))
        icl=QVBoxLayout(self._ic); icl.setContentsMargins(0,0,0,0); icl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._ic_lbl=QLabel()
        self._ic_lbl.setPixmap(StarkIcons.user_check(T.TEXT_WHITE).pixmap(QSize(22,22)))
        icl.addWidget(self._ic_lbl); bl.addWidget(self._ic)

        tc=QVBoxLayout(); tc.setSpacing(2)
        self._status_main=QLabel("Agent RH : Prêt à vous écouter")
        self._status_main.setFont(QFont(T.FONT,T.FS_BASE,QFont.Weight.Bold))
        self._status_main.setStyleSheet(f"color:{T.TEXT_900};background:transparent;")
        self._status_sub=QLabel("SparkHire AI · Intelligence Vocale")
        self._status_sub.setFont(QFont(T.FONT,T.FS_XS))
        self._status_sub.setStyleSheet(f"color:{T.TEXT_300};letter-spacing:0.5px;background:transparent;")
        tc.addWidget(self._status_main); tc.addWidget(self._status_sub)
        bl.addLayout(tc,stretch=1)

        self._dot=_Dot(T.TEAL_500); bl.addWidget(self._dot)
        self._badge=QLabel("Disponible")
        self._badge.setFont(QFont(T.FONT,T.FS_XS,QFont.Weight.Bold))
        self._badge.setStyleSheet(f"""
            color:{T.GREEN_600};background:{T.GREEN_50};
            border:1px solid {T.GREEN_100};border-radius:{T.R_FULL}px;padding:5px 14px;
        """)
        bl.addWidget(self._badge)
        wl.addWidget(bar); root.addWidget(wrapper)

        if not pygame.get_init(): pygame.display.init()
        self.base_path=Path(__file__).resolve().parent.parent.parent
        self.video_dir=self.base_path/"assets"/"videos"
        self.video_paths={
            "idle":str(self.video_dir/"rh_idle.mp4"),
            "speaking":str(self.video_dir/"rh_speaking.mp4"),
            "listening":str(self.video_dir/"rh_listening.mp4"),
        }
        self.cap=None; self.timer=QTimer(); self.timer.timeout.connect(self._update_frame)
        self.current_state="idle"
        from client.ui.camera_preview_widget import CameraPreviewWidget
        self._camera_preview=CameraPreviewWidget(parent=self); self._camera_preview.hide()
        self.set_idle()

    @property
    def camera_preview(self): return self._camera_preview

    def _load_video(self,state):
        if self.cap: self.cap.release()
        p=self.video_paths.get(state,"")
        if not Path(p).exists(): self._show_placeholder(state); return
        self.cap=cv2.VideoCapture(p); self.current_state=state
        if not self.timer.isActive(): self.timer.start(33)

    def _show_placeholder(self,state):
        w,h=800,540; img=np.ones((h,w,3),dtype=np.uint8)
        for y in range(h):
            t_=y/h
            img[y,:,0]=int(234+t_*8); img[y,:,1]=int(248+t_*4); img[y,:,2]=int(250+t_*5)
        cx,cy=w//2,h//2
        cv2.circle(img,(cx,cy),72,int2bgr("#C8EFF5"),-1)
        cv2.circle(img,(cx,cy),72,int2bgr("#00C8E0"),2)
        cv2.putText(img,f"[ {state.upper()} ]",(cx-68,cy+8),cv2.FONT_HERSHEY_SIMPLEX,0.85,int2bgr("#00A99D"),2,cv2.LINE_AA)
        qt=QImage(img.data,w,h,3*w,QImage.Format_RGB888)
        self.avatar_display.setPixmap(QPixmap.fromImage(qt).scaled(
            self.avatar_display.size(),Qt.AspectRatioMode.KeepAspectRatio,Qt.TransformationMode.SmoothTransformation))

    @Slot()
    def _update_frame(self):
        if not self.cap or not self.cap.isOpened(): return
        ret,frame=self.cap.read()
        if not ret: self.cap.set(cv2.CAP_PROP_POS_FRAMES,0); return
        try:
            frame=cv2.cvtColor(frame,cv2.COLOR_BGR2RGB)
            pg=pygame.surfarray.make_surface(frame.swapaxes(0,1))
            buf=np.ascontiguousarray(pygame.surfarray.array3d(pg).swapaxes(0,1))
            h,w,ch=buf.shape; qt=QImage(buf.data,w,h,ch*w,QImage.Format_RGB888)
            self.avatar_display.setPixmap(QPixmap.fromImage(qt).scaled(
                self.avatar_display.size(),Qt.AspectRatioMode.KeepAspectRatioByExpanding,
                Qt.TransformationMode.SmoothTransformation))
        except Exception as e: print(f"[video] {e}")

    def resizeEvent(self,e):
        super().resizeEvent(e)
        if hasattr(self,"_camera_preview"): self._camera_preview.reposition()

    def _apply_state(self,icon_pix,main,mc,badge,bc,bg,bd,dc,ic0,ic1):
        self._ic_lbl.setPixmap(icon_pix)
        self._ic.setStyleSheet(f"""QFrame{{
            background:qlineargradient(x1:0,y1:0,x2:1,y2:1,stop:0 {ic0},stop:1 {ic1});
            border-radius:13px;border:none;
        }}""")
        self._status_main.setText(main)
        self._status_main.setStyleSheet(f"color:{mc};font-weight:700;background:transparent;")
        self._badge.setText(badge)
        self._badge.setStyleSheet(f"color:{bc};background:{bg};border:1px solid {bd};border-radius:{T.R_FULL}px;padding:5px 14px;")
        self._dot.set_color(dc)

    def set_idle(self):
        self._apply_state(
            StarkIcons.user_check(T.TEXT_WHITE).pixmap(QSize(22,22)),
            "Agent RH : Prêt à vous écouter",T.TEXT_900,
            "Disponible",T.GREEN_600,T.GREEN_50,T.GREEN_100,T.TEAL_500,
            T.TEAL_500,T.TEAL_400)
        self._load_video("idle")

    def set_speaking(self):
        self._apply_state(
            StarkIcons.message_circle(T.TEXT_WHITE).pixmap(QSize(22,22)),
            "Agent RH : Analyse de votre profil…",T.CYAN_700,
            "En cours",T.CYAN_700,T.CYAN_50,T.CYAN_200,T.CYAN_500,
            T.CYAN_500,T.CYAN_400)
        self._load_video("speaking")

    def set_listening(self):
        self._apply_state(
            StarkIcons.headphones(T.TEXT_WHITE).pixmap(QSize(22,22)),
            "Agent RH : Écoute attentive en cours…",T.TEXT_900,
            "Écoute…",T.AMBER_600,T.AMBER_50,T.AMBER_100,T.AMBER_500,
            T.AMBER_500,T.ORANGE_500)
        self._load_video("listening")

    def closeEvent(self,e):
        self.timer.stop()
        if self.cap: self.cap.release()
        super().closeEvent(e)


def int2bgr(h):
    h=h.lstrip("#")
    return int(h[0:2],16),int(h[2:4],16),int(h[4:6],16)