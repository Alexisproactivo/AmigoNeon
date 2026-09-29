import random
from ui.guia import GuiaWidget
from pathlib import Path
from PyQt6.QtWidgets import QWidget, QApplication
from PyQt6.QtCore import Qt, QPoint, pyqtSignal, pyqtSlot, QTimer
from PyQt6.QtGui import QPainter, QPixmap

# Ruta absoluta hacia assets/sprites/
BASE_DIR = Path(__file__).resolve().parent.parent
SPRITES_DIR = BASE_DIR / "assets" / "sprites"

class AvatarWidget(QWidget):
    boca_signal = pyqtSignal(bool)
    estado_signal = pyqtSignal(str)
    cerrar_signal = pyqtSignal()
  

    def contextMenuEvent(self, event):
        """Al hacer clic derecho sobre el avatar, abre o cierra la guía de comandos"""
        self.panel_guia.alternar_mostrar(self.pos(), self.width())
        event.accept()

    def __init__(self):
        super().__init__()
        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint | 
            Qt.WindowType.WindowStaysOnTopHint | 
            Qt.WindowType.SubWindow
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.resize(180, 220)

        # Ubicación en esquina inferior derecha de la pantalla
        pantalla = QApplication.primaryScreen().availableGeometry()
        margen = 20
        self.move(pantalla.width() - self.width() - margen, pantalla.height() - self.height() - margen)
        
        # Inicializar panel de guía incorporado
        self.panel_guia = GuiaWidget()
        # Función auxiliar de carga y escalado limpio
        def cargar_sprite(nombre_archivo, fallback=None):
            ruta = SPRITES_DIR / nombre_archivo
            if ruta.exists():
                return QPixmap(str(ruta)).scaled(
                    160, 200, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation
                )
            return fallback

        # 1. Cuadros del ciclo de respiración en reposo
        self.pix_q1 = cargar_sprite("quieto_1.png")
        self.pix_q2 = cargar_sprite("quieto_2.png", fallback=self.pix_q1)
        self.pix_q3 = cargar_sprite("quieto_3.png", fallback=self.pix_q2)
        self.secuencia_respiracion = [self.pix_q1, self.pix_q2, self.pix_q3, self.pix_q2]
        self.idx_respiracion = 0

        # 2. Sprites funcionales y emocionales
        self.pix_habla = cargar_sprite("hablando.png", fallback=self.pix_q1)
        self.pix_parpadeo = cargar_sprite("parpadeo.png", fallback=self.pix_q1)
        self.pix_pensando = cargar_sprite("pensando.png", fallback=self.pix_q1)
        self.pix_alegre = cargar_sprite("alegre.png", fallback=self.pix_q1)
        self.pix_sorprendido = cargar_sprite("sorprendido.png", fallback=self.pix_q1)
        self.pix_error = cargar_sprite("error.png", fallback=self.pix_q1)

        self.sprites_emociones = {
            "pensando": self.pix_pensando,
            "alegre": self.pix_alegre,
            "sorprendido": self.pix_sorprendido,
            "error": self.pix_error
        }

        # Estados iniciales
        self.estado_emocional = "quieto"
        self.boca_abierta_estado = False
        self.en_parpadeo = False
        self.frame_actual = self.pix_q1
        self.drag_position = QPoint()

       # --- MOTOR DE RESPIRACIÓN FLUIDA POR VAIVÉN ---
        self.fase_respiracion = 0.0
        self.desplazamiento_y = 0
        self.timer_respiracion = QTimer(self)
        self.timer_respiracion.timeout.connect(self._actualizar_respiracion)
        self.timer_respiracion.start(30)  # ~33 FPS para movimiento suave

        # --- MOTOR DE PARPADEO AUTÓNOMO ---
        self.timer_parpadeo = QTimer(self)
        self.timer_parpadeo.timeout.connect(self._ejecutar_parpadeo)
        self._programar_siguiente_parpadeo()

        # Conectar señales seguras entre hilos
        self.boca_signal.connect(self._actualizar_frame_boca)
        self.estado_signal.connect(self._actualizar_estado_emocional)
        self.cerrar_signal.connect(self._cerrar_avatar)

    def _actualizar_respiracion(self):
        import math
        self.fase_respiracion += 0.06
        # Si está quieto en reposo, oscila 5 píxeles arriba y abajo
        if self.estado_emocional == "quieto" and not self.boca_abierta_estado:
            self.desplazamiento_y = int(math.sin(self.fase_respiracion) * 5)
        else:
            self.desplazamiento_y = 0
        self.update()

    def _resolver_frame(self):
        """Prioridad: Habla > Parpadeo > Emoción fija > Cuadro actual de respiración"""
        if self.boca_abierta_estado and self.pix_habla:
            return self.pix_habla
        if self.en_parpadeo and self.pix_parpadeo:
            return self.pix_parpadeo
        if self.estado_emocional in self.sprites_emociones:
            return self.sprites_emociones[self.estado_emocional]
        return self.secuencia_respiracion[self.idx_respiracion]

    def paintEvent(self, event):
        painter = QPainter(self)
        if self.frame_actual and not self.frame_actual.isNull():
            pos_y = 10 + self.desplazamiento_y
            painter.drawPixmap(10, pos_y, self.frame_actual)

    @pyqtSlot(bool)
    def _actualizar_frame_boca(self, abrir):
        self.boca_abierta_estado = abrir
        self.frame_actual = self._resolver_frame()
        self.update()

    @pyqtSlot(str)
    def _actualizar_estado_emocional(self, nuevo_estado):
        self.estado_emocional = nuevo_estado
        self.frame_actual = self._resolver_frame()
        self.update()

        # Regreso automático a reposo para estados temporales (en el hilo principal)
        if nuevo_estado == "alegre":
            QTimer.singleShot(4000, lambda: self.set_estado("quieto"))
        elif nuevo_estado in ["sorprendido", "error"]:
            QTimer.singleShot(2500, lambda: self.set_estado("quieto"))

    def _ejecutar_parpadeo(self):
        if self.estado_emocional == "quieto" and not self.boca_abierta_estado:
            self.en_parpadeo = True
            self.frame_actual = self._resolver_frame()
            self.update()
            QTimer.singleShot(160, self._terminar_parpadeo)
        else:
            self._programar_siguiente_parpadeo()

    def _terminar_parpadeo(self):
        self.en_parpadeo = False
        self.frame_actual = self._resolver_frame()
        self.update()
        self._programar_siguiente_parpadeo()

    def _programar_siguiente_parpadeo(self):
        self.timer_parpadeo.start(random.randint(3000, 6000))

    @pyqtSlot()
    def _cerrar_avatar(self):
        self.timer_respiracion.stop()
        self.timer_parpadeo.stop()
        self.close()
        QApplication.instance().quit()

    def set_boca(self, estado: bool):
        self.boca_signal.emit(estado)

    def set_estado(self, estado: str):
        self.estado_signal.emit(estado)

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