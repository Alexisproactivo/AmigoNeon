import math
import struct
import threading
import speech_recognition as sr
import pyaudio
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QTextEdit, 
    QLineEdit, QPushButton, QLabel, QFrame, QStackedWidget, QMenu
)
from PyQt6.QtCore import Qt, pyqtSignal, pyqtSlot, QPoint
from PyQt6.QtGui import QPainter, QColor, QBrush, QAction, QIcon, QPixmap
from PyQt6.QtSvg import QSvgRenderer


# Componente visual: Ecualizador animado por decibelios reales
class EcualizadorVozReal(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedHeight(30)
        self.num_barras = 22
        self.alturas = [0.15] * self.num_barras

    @pyqtSlot(float)
    def actualizar_nivel_real(self, nivel_normalizado):
        for i in range(self.num_barras):
            distancia_centro = abs(i - (self.num_barras / 2)) / (self.num_barras / 2)
            factor = max(0.12, nivel_normalizado * (1.15 - (distancia_centro * 0.4)))
            self.alturas[i] = min(1.0, factor)
        self.update()

    def resetear(self):
        self.alturas = [0.15] * self.num_barras
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        w_total = self.width()
        h_total = self.height()
        ancho_barra = 4
        espacio = 3
        inicio_x = (w_total - (self.num_barras * (ancho_barra + espacio))) // 2

        for i, val in enumerate(self.alturas):
            alto = int(h_total * val * 0.88)
            y = (h_total - alto) // 2
            x = inicio_x + (i * (ancho_barra + espacio))

            g = int(180 + (val * 75))
            painter.setBrush(QBrush(QColor(0, min(255, g), 255)))
            painter.setPen(Qt.PenStyle.NoPen)
            painter.drawRoundedRect(x, y, ancho_barra, alto, 2, 2)


class ChatPanel(QWidget):
    mensaje_enviado = pyqtSignal(str)
    solicitar_conversacion = pyqtSignal()
    nivel_audio_signal = pyqtSignal(float)
    texto_transcrito_signal = pyqtSignal(str)
    # Nuevas señales para avisar a main.py
    inicio_dictado_signal = pyqtSignal()
    fin_dictado_signal = pyqtSignal()
    

    def __init__(self):
        super().__init__()
        self.setWindowTitle("AmigoNeon // Terminal HUD")
        # Altura vertical optimizada
        self.resize(360, 520)
        self.setWindowFlags(Qt.WindowType.WindowStaysOnTopHint | Qt.WindowType.Tool)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)

        self.grabando = False
        self.frames_grabados = []
        self.sample_rate = 16000

        self._construir_ui()

        self.nivel_audio_signal.connect(self.ecualizador.actualizar_nivel_real)
        self.texto_transcrito_signal.connect(self._recibir_transcripcion)

    def _generar_icono_micro_svg(self):
        """Genera un ícono vectorial estilizado de micrófono gamer sin depender de archivos externos"""
        svg_code = """
        <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" width="20" height="20">
            <!-- Cápsula micro -->
            <rect x="9" y="2" width="6" height="11" rx="3" fill="#38BDF8"/>
            <!-- Soporte arco -->
            <path d="M5 10v1a7 7 0 0 0 14 0v-1" stroke="#38BDF8" stroke-width="2" stroke-linecap="round" fill="none"/>
            <!-- Base vertical -->
            <line x1="12" y1="18" x2="12" y2="22" stroke="#38BDF8" stroke-width="2" stroke-linecap="round"/>
            <line x1="8" y1="22" x2="16" y2="22" stroke="#38BDF8" stroke-width="2" stroke-linecap="round"/>
        </svg>
        """.encode("utf-8")
        renderer = QSvgRenderer(svg_code)
        pix = QPixmap(20, 20)
        pix.fill(Qt.GlobalColor.transparent)
        painter = QPainter(pix)
        renderer.render(painter)
        painter.end()
        return QIcon(pix)

    def _construir_ui(self):
        layout_exterior = QVBoxLayout(self)
        layout_exterior.setContentsMargins(6, 6, 6, 6)

        # Marco HUD Gamer Glassmorphism
        self.contenedor = QFrame(self)
        self.contenedor.setObjectName("panel_hud")
        self.contenedor.setStyleSheet("""
            QFrame#panel_hud {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1, 
                    stop:0 #0B0F19, stop:0.85 #070A10, stop:1 #020617);
                border: 1px solid rgba(56, 189, 248, 0.28);
                border-radius: 14px;
            }
            QLabel {
                font-family: 'Rajdhani', 'Orbitron', 'Consolas', 'Segoe UI', sans-serif;
            }
        """)

        layout_principal = QVBoxLayout(self.contenedor)
        layout_principal.setContentsMargins(10, 8, 10, 8)
        layout_principal.setSpacing(6)

        # 1. Cabecera ultra-delgada
        cabecera = QHBoxLayout()
        cabecera.setContentsMargins(2, 0, 2, 0)
        
        lbl_dot = QLabel("●")
        lbl_dot.setStyleSheet("color: #10B981; font-size: 11px;")
        cabecera.addWidget(lbl_dot)

        lbl_titulo = QLabel("TERMINAL // HUD")
        lbl_titulo.setStyleSheet("""
            color: #38BDF8;
            font-size: 11px;
            font-weight: 900;
            letter-spacing: 1.2px;
        """)
        cabecera.addWidget(lbl_titulo)
        cabecera.addStretch()

        btn_min = QPushButton("✕")
        btn_min.setFixedSize(20, 20)
        btn_min.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_min.setStyleSheet("""
            QPushButton {
                background: transparent;
                color: #64748B;
                border-radius: 10px;
                border: none;
                font-size: 11px;
                font-weight: bold;
            }
            QPushButton:hover {
                background: #EF4444;
                color: #FFFFFF;
            }
        """)
        btn_min.clicked.connect(self.hide)
        cabecera.addWidget(btn_min)
        layout_principal.addLayout(cabecera)

        # 2. Historial de mensajes (se le da el 100% de prioridad de expansión vertical)
        self.historial = QTextEdit()
        self.historial.setReadOnly(True)
        self.historial.setStyleSheet("""
            QTextEdit {
                background-color: rgba(11, 15, 25, 0.7);
                color: #E2E8F0;
                border: 1px solid #1E293B;
                border-radius: 10px;
                font-family: 'Rajdhani', 'Consolas', 'Segoe UI', sans-serif;
                font-size: 13px;
                padding: 8px;
            }
            QScrollBar:vertical {
                background: transparent;
                width: 4px;
            }
            QScrollBar::handle:vertical {
                background: #334155;
                border-radius: 2px;
            }
            QScrollBar::handle:vertical:hover {
                background: #38BDF8;
            }
        """)
        layout_principal.addWidget(self.historial, stretch=1)

        # 3. Stack inferior interactivo
        self.stack_entrada = QStackedWidget()
        self.stack_entrada.setFixedHeight(38)

        # --- Vista 0: Input Gamer estilizado y compacto ---
        vista_texto = QWidget()
        layout_txt = QHBoxLayout(vista_texto)
        layout_txt.setContentsMargins(0, 0, 0, 0)
        layout_txt.setSpacing(5)

        self.input_texto = QLineEdit()
        self.input_texto.setFixedHeight(34)
        self.input_texto.setPlaceholderText("Escribe un comando o consulta...")
        self.input_texto.setStyleSheet("""
            QLineEdit {
                background-color: #0F172A;
                color: #F8FAFC;
                border: 1px solid #1E293B;
                border-radius: 8px;
                padding: 0 10px;
                font-family: 'Segoe UI', sans-serif;
                font-size: 12px;
            }
            QLineEdit:focus {
                border: 1px solid #38BDF8;
                background-color: #111E36;
            }
        """)
        self.input_texto.returnPressed.connect(self._enviar_texto)
        layout_txt.addWidget(self.input_texto)

        # Botón Micrófono Gamer
        self.btn_mic = QPushButton()
        self.btn_mic.setFixedSize(34, 34)
        self.btn_mic.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_mic.setIcon(self._generar_icono_micro_svg())
        self.btn_mic.setStyleSheet("""
            QPushButton {
                background: #0B132B;
                border: 1px solid rgba(56, 189, 248, 0.4);
                border-radius: 8px;
            }
            QPushButton:hover {
                background: #0284C7;
                border: 1px solid #38BDF8;
            }
        """)
        self.btn_mic.clicked.connect(self._mostrar_menu_micro)
        layout_txt.addWidget(self.btn_mic)

        # Botón Enviar Gamer Neón
        self.btn_enviar = QPushButton("ENVIAR")
        self.btn_enviar.setFixedSize(65, 34)
        self.btn_enviar.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_enviar.setStyleSheet("""
            QPushButton {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #10B981, stop:1 #06B6D4);
                color: #FFFFFF;
                font-family: 'Rajdhani', sans-serif;
                font-weight: 900;
                font-size: 11px;
                letter-spacing: 0.8px;
                border-radius: 8px;
                border: none;
            }
            QPushButton:hover {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #059669, stop:1 #0891B2);
            }
        """)
        self.btn_enviar.clicked.connect(self._enviar_texto)
        layout_txt.addWidget(self.btn_enviar)

        self.stack_entrada.addWidget(vista_texto)

        # --- Vista 1: Modo Ecualizador Activo ---
        vista_grabando = QWidget()
        layout_rec = QHBoxLayout(vista_grabando)
        layout_rec.setContentsMargins(0, 0, 0, 0)
        layout_rec.setSpacing(6)

        frame_ondas = QFrame()
        frame_ondas.setFixedHeight(34)
        frame_ondas.setStyleSheet("""
            QFrame {
                background-color: #050B14;
                border: 1px solid #0284C7;
                border-radius: 8px;
            }
        """)
        layout_ondas = QHBoxLayout(frame_ondas)
        layout_ondas.setContentsMargins(8, 2, 8, 2)

        self.ecualizador = EcualizadorVozReal()
        layout_ondas.addWidget(self.ecualizador)
        layout_rec.addWidget(frame_ondas)

        # Botón Detener / Parar (Punto rojo neón)
        self.btn_stop = QPushButton("●")
        self.btn_stop.setFixedSize(34, 34)
        self.btn_stop.setToolTip("Parar y transcribir al texto")
        self.btn_stop.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_stop.setStyleSheet("""
            QPushButton {
                background-color: #EF4444;
                color: #FFFFFF;
                font-size: 18px;
                border-radius: 8px;
                border: none;
            }
            QPushButton:hover {
                background-color: #DC2626;
            }
        """)
        self.btn_stop.clicked.connect(self._detener_dictado_y_procesar)
        layout_rec.addWidget(self.btn_stop)

        self.stack_entrada.addWidget(vista_grabando)

        layout_principal.addWidget(self.stack_entrada)
        layout_exterior.addWidget(self.contenedor)

    def _mostrar_menu_micro(self):
        menu = QMenu(self)
        menu.setStyleSheet("""
            QMenu {
                background-color: #0F172A;
                color: #E2E8F0;
                border: 1px solid #38BDF8;
                border-radius: 8px;
                padding: 4px;
                font-family: 'Rajdhani', 'Segoe UI', sans-serif;
                font-size: 12px;
                font-weight: bold;
            }
            QMenu::item {
                padding: 6px 16px;
                border-radius: 4px;
            }
            QMenu::item:selected {
                background-color: #0284C7;
                color: #FFFFFF;
            }
        """)

        opcion_dictar = QAction("✍️ Dictar al chat", self)
        opcion_dictar.triggered.connect(self._iniciar_dictado_hardware)
        menu.addAction(opcion_dictar)

        opcion_hablar = QAction("🗣️ Hablar con tu Causa", self)
        opcion_hablar.triggered.connect(self.solicitar_conversacion.emit)
        menu.addAction(opcion_hablar)

        pos = self.btn_mic.mapToGlobal(QPoint(0, -menu.sizeHint().height() - 5))
        menu.exec(pos)

    # --- CAPTURA DE AUDIO REAL Y RMS ---
    def _iniciar_dictado_hardware(self):
        self.grabando = True
        self.frames_grabados = []
        self.stack_entrada.setCurrentIndex(1)
        self.inicio_dictado_signal.emit()  # <-- Pausa el centinela de voz
        threading.Thread(target=self._bucle_captura_microfono, daemon=True).start()

    def _bucle_captura_microfono(self):
        p = pyaudio.PyAudio()
        chunk_size = 1024

        try:
            stream = p.open(
                format=pyaudio.paInt16,
                channels=1,
                rate=self.sample_rate,
                input=True,
                frames_per_buffer=chunk_size
            )

            while self.grabando:
                raw_data = stream.read(chunk_size, exception_on_overflow=False)
                self.frames_grabados.append(raw_data)

                # Cálculo de amplitud real RMS
                count = len(raw_data) // 2
                shorts = struct.unpack(f"<{count}h", raw_data)
                sum_sq = sum(s * s for s in shorts)
                rms = math.sqrt(sum_sq / count) if count > 0 else 0

                nivel_normalizado = min(1.0, max(0.12, (rms / 2800.0)))
                self.nivel_audio_signal.emit(nivel_normalizado)

            stream.stop_stream()
            stream.close()
        except Exception as e:
            print(f"[Error PyAudio]: {e}")
        finally:
            p.terminate()

    def _detener_dictado_y_procesar(self):
        if not self.grabando:
            return
        self.grabando = False
        self.ecualizador.resetear()
        self.stack_entrada.setCurrentIndex(0)
        self.input_texto.setPlaceholderText("Transcribiendo lo que dijiste...")
        self.fin_dictado_signal.emit()  
        threading.Thread(target=self._transcribir_buffer_audio, daemon=True).start()

    def _transcribir_buffer_audio(self):
        if not self.frames_grabados:
            self.texto_transcrito_signal.emit("")
            return

        try:
            datos_completos = b"".join(self.frames_grabados)
            r = sr.Recognizer()
            audio_data = sr.AudioData(datos_completos, self.sample_rate, 2)
            texto = r.recognize_google(audio_data, language="es-PE").strip()
            self.texto_transcrito_signal.emit(texto)
        except Exception:
            self.texto_transcrito_signal.emit("")

    @pyqtSlot(str)
    def _recibir_transcripcion(self, texto):
        self.input_texto.setPlaceholderText("Escribe un comando o consulta...")
        if texto:
            self.input_texto.setText(texto)
            self.input_texto.setFocus()

    def _enviar_texto(self):
        texto = self.input_texto.text().strip()
        if texto:
            self.agregar_mensaje("Tú", texto)
            self.input_texto.clear()
            self.mensaje_enviado.emit(texto)

    @pyqtSlot(str, str)
    def agregar_mensaje(self, emisor, texto):
        if emisor in ["Tú", "Usuario"]:
            # Card usuario: acento Cyan
            borde = "border-left: 2px solid #38BDF8;"
            bg = "background: rgba(56, 189, 248, 0.08);"
            color_nombre = "#38BDF8"
            tag = "TÚ"
        else:
            # Card bot: acento Verde esmeralda / Plata
            borde = "border-left: 2px solid #10B981;"
            bg = "background: rgba(16, 185, 129, 0.08);"
            color_nombre = "#10B981"
            tag = "CAUSA"

        bloque = f"""
        <div style='margin-bottom: 6px; padding: 6px 8px; border-radius: 6px; {bg} {borde}'>
            <div style='color: {color_nombre}; font-weight: 800; font-size: 10px; letter-spacing: 0.8px;'>
                {tag}
            </div>
            <div style='color: #E2E8F0; font-size: 12px; margin-top: 2px;'>
                {texto}
            </div>
        </div>
        """
        self.historial.append(bloque)