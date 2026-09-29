from pathlib import Path
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
    QPushButton, QScrollArea, QFrame, QGraphicsDropShadowEffect
)
from PyQt6.QtCore import Qt, QPoint
from PyQt6.QtGui import QPixmap, QColor, QPainter, QPainterPath

BASE_DIR = Path(__file__).resolve().parent.parent
SPRITES_DIR = BASE_DIR / "assets" / "sprites"

class GuiaWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint | 
            Qt.WindowType.WindowStaysOnTopHint | 
            Qt.WindowType.Tool
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        # Tamaño optimizado y amplio
        self.resize(370, 600)
        self.drag_position = QPoint()
        self._construir_ui()

    def _construir_ui(self):
        layout_exterior = QVBoxLayout(self)
        layout_exterior.setContentsMargins(12, 12, 12, 12)

        # 1. Tarjeta principal contenedora Glassmorphism
        self.tarjeta = QFrame(self)
        self.tarjeta.setObjectName("tarjeta_principal")
        self.tarjeta.setStyleSheet("""
            QFrame#tarjeta_principal {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1, 
                    stop:0 rgba(255, 255, 255, 0.96), 
                    stop:0.65 rgba(243, 248, 252, 0.94),
                    stop:1 rgba(210, 235, 245, 0.96));
                border-radius: 30px;
                border: 1px solid rgba(255, 255, 255, 0.9);
            }
            QLabel {
                font-family: 'Rajdhani', 'Orbitron', 'Consolas', 'Segoe UI', sans-serif;
                background: transparent;
            }
        """)

        sombra = QGraphicsDropShadowEffect(self)
        sombra.setBlurRadius(32)
        sombra.setColor(QColor(15, 23, 42, 60))
        sombra.setOffset(0, 10)
        self.tarjeta.setGraphicsEffect(sombra)

        layout_card = QVBoxLayout(self.tarjeta)
        layout_card.setContentsMargins(20, 20, 20, 20)
        layout_card.setSpacing(12)

        # 2. Cabecera (Avatar + Botón Cerrar)
        fila_top = QHBoxLayout()
        lbl_avatar = QLabel()
        lbl_avatar.setFixedSize(66, 66)
        lbl_avatar.setPixmap(self._obtener_avatar_circular(66))
        fila_top.addWidget(lbl_avatar)

        fila_top.addStretch()

        btn_cerrar = QPushButton("✕")
        btn_cerrar.setFixedSize(34, 34)
        btn_cerrar.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_cerrar.setStyleSheet("""
            QPushButton {
                background-color: rgba(255, 255, 255, 0.85);
                border-radius: 17px;
                font-family: 'Segoe UI', sans-serif;
                font-weight: 800;
                color: #64748b;
                font-size: 14px;
                border: 1px solid rgba(0,0,0,0.06);
            }
            QPushButton:hover {
                background-color: #ef4444;
                color: #ffffff;
            }
        """)
        btn_cerrar.clicked.connect(self.hide)
        fila_top.addWidget(btn_cerrar)
        layout_card.addLayout(fila_top)

        # 3. Identidad del bot
        lbl_nombre = QLabel("AMIGO NEON")
        lbl_nombre.setStyleSheet("font-size: 21px; font-weight: 900; color: #0f172a; letter-spacing: 1px;")
        layout_card.addWidget(lbl_nombre)

        lbl_rol = QLabel("HUD // ASISTENTE MULTIMODAL")
        lbl_rol.setStyleSheet("font-size: 11px; font-weight: 700; color: #64748b; letter-spacing: 1px;")
        layout_card.addWidget(lbl_rol)

        # 4. Métricas / Atajos rápidos
        fila_stats = QHBoxLayout()
        fila_stats.setContentsMargins(4, 2, 4, 4)

        def crear_columna_stat(valor, etiqueta):
            col = QVBoxLayout()
            col.setSpacing(1)
            lbl_v = QLabel(valor)
            lbl_v.setStyleSheet("font-size: 14px; font-weight: 900; color: #0f172a;")
            lbl_v.setAlignment(Qt.AlignmentFlag.AlignCenter)
            lbl_e = QLabel(etiqueta)
            lbl_e.setStyleSheet("font-size: 9px; font-weight: 800; color: #94a3b8; letter-spacing: 0.8px;")
            lbl_e.setAlignment(Qt.AlignmentFlag.AlignCenter)
            col.addWidget(lbl_v)
            col.addWidget(lbl_e)
            return col

        fila_stats.addLayout(crear_columna_stat("★ 5.0", "SYSTEM"))
        div1 = QFrame()
        div1.setFrameShape(QFrame.Shape.VLine)
        div1.setStyleSheet("color: rgba(148, 163, 184, 0.35);")
        fila_stats.addWidget(div1)

        fila_stats.addLayout(crear_columna_stat("[F8]", "LISTEN"))
        div2 = QFrame()
        div2.setFrameShape(QFrame.Shape.VLine)
        div2.setStyleSheet("color: rgba(148, 163, 184, 0.35);")
        fila_stats.addWidget(div2)

        fila_stats.addLayout(crear_columna_stat("[F9]", "MUTE"))
        layout_card.addLayout(fila_stats)

        # 5. Caja central Gamer/HUD Pizarra
        caja_comandos = QFrame()
        caja_comandos.setStyleSheet("""
            QFrame {
                background-color: #111827;
                border-radius: 20px;
                border: 1px solid #1f2937;
            }
        """)
        layout_caja = QVBoxLayout(caja_comandos)
        layout_caja.setContentsMargins(14, 14, 14, 12)
        layout_caja.setSpacing(10)

        # Pastillas (Pills) gamer temáticas en el encabezado
        fila_pills = QHBoxLayout()
        fila_pills.setSpacing(6)

        pills_data = [
            ("VOICE", "#c084fc", "rgba(192, 132, 252, 0.15)"),
            ("VISION", "#38bdf8", "rgba(56, 189, 248, 0.15)"),
            ("AUDIO", "#4ade80", "rgba(74, 222, 128, 0.15)")
        ]
        for tag, color_txt, bg_color in pills_data:
            pill = QLabel(f"• {tag}")
            pill.setStyleSheet(f"""
                background-color: {bg_color};
                color: {color_txt};
                font-size: 10px;
                font-weight: 800;
                letter-spacing: 0.8px;
                padding: 4px 9px;
                border-radius: 9px;
                border: 1px solid {color_txt}40;
            """)
            fila_pills.addWidget(pill)
        fila_pills.addStretch()
        layout_caja.addLayout(fila_pills)

        # Scroll con secciones multicolores
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet("""
            QScrollArea {
                background: transparent;
                border: none;
            }
            QScrollBar:vertical {
                background: transparent;
                width: 5px;
            }
            QScrollBar::handle:vertical {
                background: #374151;
                border-radius: 2px;
            }
            QScrollBar::handle:vertical:hover {
                background: #4b5563;
            }
        """)

        contenido = QWidget()
        layout_scroll = QVBoxLayout(contenido)
        layout_scroll.setContentsMargins(2, 4, 8, 4)
        layout_scroll.setSpacing(10)

        # Definición de secciones temáticas (Título, Color acento, Fondo tarjeta, Comandos)
        modulos = [
            ("🎤 VOICE CONTROL", "#c084fc", "rgba(192, 132, 252, 0.08)", [
                "Di <b>'Amigo'</b> o <b>'Causa'</b> para despertar.",
                "Pulsa <b>F8</b> para hablar directo sin clave."
            ]),
            ("🎵 AUDIO & STREAMING", "#4ade80", "rgba(74, 222, 128, 0.08)", [
                "<b>'Pon [tema] en Spotify'</b> (autoplay directo).",
                "<b>'Pon [tema] en YouTube'</b> (abre video)."
            ]),
            ("👁️ VISION AI", "#38bdf8", "rgba(56, 189, 248, 0.08)", [
                "<b>'Mira mi pantalla'</b> o <b>'¿Qué opinas?'</b>",
                "Analiza código, ventanas y contenido activo."
            ]),
            ("⚙️ SYSTEM COMMANDS", "#fb923c", "rgba(251, 146, 60, 0.08)", [
                "<b>'Sube / Baja volumen'</b> o <b>'Volumen a 40'</b>.",
                "<b>'Abre Word / Excel / Calculadora'</b>.",
                "<b>'Busca el archivo [nombre]'</b> en tus discos."
            ]),
            ("🛑 POWER / EXIT", "#f87171", "rgba(248, 113, 113, 0.08)", [
                "<b>'Eso es todo'</b>: Vuelve a reposo.",
                "<b>'Apágate'</b>: Cierre total de la app."
            ])
        ]

        for categoria, color_tema, bg_card, items in modulos:
            card_sec = QFrame()
            card_sec.setStyleSheet(f"""
                QFrame {{
                    background-color: {bg_card};
                    border-left: 3px solid {color_tema};
                    border-radius: 8px;
                    padding: 4px;
                }}
            """)
            layout_sec = QVBoxLayout(card_sec)
            layout_sec.setContentsMargins(8, 6, 8, 6)
            layout_sec.setSpacing(4)

            lbl_cat = QLabel(categoria)
            lbl_cat.setStyleSheet(f"""
                font-size: 11px; 
                font-weight: 900; 
                color: {color_tema}; 
                letter-spacing: 0.8px;
                border: none;
            """)
            layout_sec.addWidget(lbl_cat)

            for item in items:
                lbl_item = QLabel(f"› {item}")
                lbl_item.setWordWrap(True)
                lbl_item.setStyleSheet("""
                    font-size: 12px; 
                    line-height: 1.4; 
                    color: #e2e8f0; 
                    border: none;
                    margin-left: 2px;
                """)
                layout_sec.addWidget(lbl_item)

            layout_scroll.addWidget(card_sec)

        scroll.setWidget(contenido)
        layout_caja.addWidget(scroll)
        layout_card.addWidget(caja_comandos)

        # 6. Botón inferior principal
        btn_accion = QPushButton("ENTENDIDO // CONTINUAR")
        btn_accion.setFixedHeight(44)
        btn_accion.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_accion.setStyleSheet("""
            QPushButton {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #10b981, stop:1 #06b6d4);
                color: #ffffff;
                font-family: 'Rajdhani', 'Consolas', sans-serif;
                font-weight: 900;
                font-size: 14px;
                letter-spacing: 1px;
                border-radius: 22px;
                border: none;
            }
            QPushButton:hover {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #059669, stop:1 #0891b2);
            }
        """)
        btn_accion.clicked.connect(self.hide)
        layout_card.addWidget(btn_accion)

        layout_exterior.addWidget(self.tarjeta)

    def _obtener_avatar_circular(self, tamano):
        ruta_img = SPRITES_DIR / "quieto_1.png"
        pix = QPixmap(str(ruta_img)) if ruta_img.exists() else QPixmap()
        
        resultado = QPixmap(tamano, tamano)
        resultado.fill(Qt.GlobalColor.transparent)

        painter = QPainter(resultado)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        path = QPainterPath()
        path.addEllipse(0, 0, tamano, tamano)
        painter.setClipPath(path)

        painter.fillRect(0, 0, tamano, tamano, QColor(186, 230, 253))

        if not pix.isNull():
            pix_escalado = pix.scaled(
                tamano, tamano, 
                Qt.AspectRatioMode.KeepAspectRatioByExpanding, 
                Qt.TransformationMode.SmoothTransformation
            )
            painter.drawPixmap(0, 0, pix_escalado)
        painter.end()
        return resultado
    
    def alternar_mostrar(self, pos_avatar, ancho_avatar):
        if self.isVisible():
            self.hide()
        else:
            # Misma fórmula de posicionamiento exacto
            pos_x = pos_avatar.x() - self.width() - 15
            pos_y = pos_avatar.y() - self.height() + 80
            
            self.move(max(10, pos_x), max(10, pos_y))
            self.show()

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.drag_position = event.globalPosition().toPoint() - self.frameGeometry().topLeft()
            event.accept()

    def mouseMoveEvent(self, event):
        if event.buttons() == Qt.MouseButton.LeftButton:
            self.move(event.globalPosition().toPoint() - self.drag_position)
            event.accept()