from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QTextEdit, 
    QLineEdit, QPushButton, QLabel
)
from PyQt6.QtCore import Qt, pyqtSignal, pyqtSlot

class ChatPanel(QWidget):
    mensaje_enviado = pyqtSignal(str)
    solicitar_microfono = pyqtSignal()

    def __init__(self):
        super().__init__()
        self.setWindowTitle("AmigoNeon - Chat")
        self.resize(360, 480)
        self.setWindowFlags(
            Qt.WindowType.WindowStaysOnTopHint | 
            Qt.WindowType.Tool
        )
        self._construir_ui()

    def _construir_ui(self):
        layout_principal = QVBoxLayout(self)
        layout_principal.setContentsMargins(10, 10, 10, 10)
        layout_principal.setSpacing(8)

        # Historial de mensajes
        self.historial = QTextEdit()
        self.historial.setReadOnly(True)
        self.historial.setStyleSheet("""
            QTextEdit {
                background-color: #1E1E2E;
                color: #CDD6F4;
                border: 1px solid #45475A;
                border-radius: 8px;
                font-family: 'Segoe UI', sans-serif;
                font-size: 13px;
                padding: 8px;
            }
        """)
        layout_principal.addWidget(self.historial)

        # Barra inferior de entrada
        layout_entrada = QHBoxLayout()
        layout_entrada.setSpacing(6)

        self.input_texto = QLineEdit()
        self.input_texto.setPlaceholderText("Escribe tu orden...")
        self.input_texto.setStyleSheet("""
            QLineEdit {
                background-color: #313244;
                color: #FFFFFF;
                border: 1px solid #585B70;
                border-radius: 6px;
                padding: 6px 10px;
                font-size: 13px;
            }
        """)
        self.input_texto.returnPressed.connect(self._enviar_texto)
        layout_entrada.addWidget(self.input_texto)

        self.btn_mic = QPushButton("🎤")
        self.btn_mic.setFixedWidth(38)
        self.btn_mic.setStyleSheet("""
            QPushButton {
                background-color: #89B4FA;
                color: #11111B;
                border-radius: 6px;
                font-size: 14px;
                padding: 6px;
            }
            QPushButton:hover { background-color: #B4BEFE; }
        """)
        self.btn_mic.clicked.connect(self.solicitar_microfono.emit)
        layout_entrada.addWidget(self.btn_mic)

        self.btn_enviar = QPushButton("Enviar")
        self.btn_enviar.setStyleSheet("""
            QPushButton {
                background-color: #A6E3A1;
                color: #11111B;
                font-weight: bold;
                border-radius: 6px;
                padding: 6px 12px;
            }
            QPushButton:hover { background-color: #94E2D5; }
        """)
        self.btn_enviar.clicked.connect(self._enviar_texto)
        layout_entrada.addWidget(self.btn_enviar)

        layout_principal.addLayout(layout_entrada)

    def _enviar_texto(self):
        texto = self.input_texto.text().strip()
        if texto:
            self.agregar_mensaje("Tú", texto)
            self.input_texto.clear()
            self.mensaje_enviado.emit(texto)

    @pyqtSlot(str, str)
    def agregar_mensaje(self, emisor, texto):
        color = "#89B4FA" if emisor == "Tú" else "#A6E3A1"
        bloque = f"<b style='color: {color};'>{emisor}:</b> {texto}<br><br>"
        self.historial.append(bloque)