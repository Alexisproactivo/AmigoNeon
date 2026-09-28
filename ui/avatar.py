from pathlib import Path
from PyQt6.QtWidgets import QWidget, QApplication
from PyQt6.QtCore import Qt, QPoint, pyqtSignal, pyqtSlot
from PyQt6.QtGui import QPainter, QPixmap

# Ruta a la carpeta de sprites desde ui/
BASE_DIR = Path(__file__).resolve().parent.parent
SPRITES_DIR = BASE_DIR / "assets" / "sprites"

class AvatarWidget(QWidget):
    boca_signal = pyqtSignal(bool)
    cerrar_signal = pyqtSignal()

    def __init__(self):
        super().__init__()
        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint | 
            Qt.WindowType.WindowStaysOnTopHint | 
            Qt.WindowType.SubWindow
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        
        self.resize(180, 220)
        
        # Obtener el área visible de la pantalla (descontando la barra de tareas)
        pantalla = QApplication.primaryScreen().availableGeometry()
        
        # Margen respecto a la esquina (20px del borde derecho e inferior)
        margen = 20
        pos_x = pantalla.width() - self.width() - margen
        pos_y = pantalla.height() - self.height() - margen
        
        self.move(pos_x, pos_y)

        img_quieto = SPRITES_DIR / "quieto.png"
        img_habla = SPRITES_DIR / "hablando.png"

        self.pix_quieto = (
            QPixmap(str(img_quieto)).scaled(
                160, 200, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation
            )
            if img_quieto.exists()
            else None
        )
        self.pix_habla = (
            QPixmap(str(img_habla)).scaled(
                160, 200, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation
            )
            if img_habla.exists()
            else None
        )

        self.frame_actual = self.pix_quieto
        self.boca_abierta_estado = False
        self.drag_position = QPoint()

        self.boca_signal.connect(self._actualizar_frame_boca)
        self.cerrar_signal.connect(self._cerrar_avatar)

    def paintEvent(self, event):
        painter = QPainter(self)
        if self.frame_actual and not self.frame_actual.isNull():
            painter.drawPixmap(10, 10, self.frame_actual)

    @pyqtSlot(bool)
    def _actualizar_frame_boca(self, abrir):
        self.boca_abierta_estado = abrir
        if abrir and self.pix_habla:
            self.frame_actual = self.pix_habla
        else:
            self.frame_actual = self.pix_quieto
        self.update()

    @pyqtSlot()
    def _cerrar_avatar(self):
        self.close()
        QApplication.instance().quit()

    def set_boca(self, estado):
        self.boca_signal.emit(estado)

    def cerrar(self):
        self.cerrar_signal.emit()

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.drag_position = event.globalPosition().toPoint() - self.frameGeometry().topLeft()
            event.accept()

    def mouseMoveEvent(self, event):
        if event.buttons() == Qt.MouseButton.LeftButton:
            self.move(event.globalPosition().toPoint() - self.drag_position)
            event.accept()
            
    def mouseDoubleClickEvent(self, event):
        if hasattr(self, 'toggle_chat_callback') and self.toggle_chat_callback:
            self.toggle_chat_callback()
        event.accept()