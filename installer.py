import sys
import time
from pathlib import Path
from PyQt6.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
    QPushButton, QStackedWidget, QRadioButton, QLineEdit, 
    QFileDialog, QProgressBar, QListWidget, QListWidgetItem,
    QFrame, QSizePolicy
)
from PyQt6.QtGui import QFont, QPixmap, QColor, QPainter, QIcon, QPen, QPolygonF
from PyQt6.QtCore import Qt, QTimer, QThread, pyqtSignal, QSize, QPointF

class InstallThread(QThread):
    progress_update = pyqtSignal(int, int) # item_index, item_progress
    item_started = pyqtSignal(int)
    item_completed = pyqtSignal(int)
    finished_install = pyqtSignal()
    
    def __init__(self, num_items):
        super().__init__()
        self.num_items = num_items
        
    def run(self):
        for i in range(self.num_items):
            self.item_started.emit(i)
            # Simulate installation time for each component
            for p in range(0, 101, 10):
                self.progress_update.emit(i, p)
                time.sleep(0.05)
            self.item_completed.emit(i)
        self.finished_install.emit()

class InstallerWizard(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("ZeroTraceFS Setup")
        self.setFixedSize(650, 500)
        
        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(0, 0, 0, 0)
        self.layout.setSpacing(0)
        
        # Banner
        self.banner = QFrame()
        self.banner.setStyleSheet("background-color: white; border-bottom: 1px solid #ccc;")
        self.banner.setFixedHeight(70)
        banner_layout = QHBoxLayout(self.banner)
        
        self.banner_icon = QLabel()
        # Fallback if no logo
        logo_path = Path("logo.png")
        if logo_path.exists():
            pixmap = QPixmap(str(logo_path)).scaled(50, 50, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)
            self.banner_icon.setPixmap(pixmap)
        banner_layout.addWidget(self.banner_icon)
        
        self.banner_title = QLabel("ZeroTraceFS Setup")
        font = QFont("Arial", 16, QFont.Weight.Bold)
        self.banner_title.setFont(font)
        banner_layout.addWidget(self.banner_title)
        banner_layout.addStretch()
        
        self.layout.addWidget(self.banner)
        
        # Stacked Widget for pages
        self.stacked_widget = QStackedWidget()
        self.layout.addWidget(self.stacked_widget)
        
        # Bottom Bar
        self.bottom_bar = QFrame()
        self.bottom_bar.setStyleSheet("background-color: #f0f0f0; border-top: 1px solid #ccc;")
        self.bottom_bar.setFixedHeight(50)
        bottom_layout = QHBoxLayout(self.bottom_bar)
        bottom_layout.addStretch()
        
        self.btn_back = QPushButton("< Previous")
        self.btn_back.setFixedWidth(80)
        self.btn_back.clicked.connect(self.go_back)
        bottom_layout.addWidget(self.btn_back)
        
        self.btn_next = QPushButton("Next >")
        self.btn_next.setFixedWidth(80)
        self.btn_next.clicked.connect(self.go_next)
        bottom_layout.addWidget(self.btn_next)
        
        self.btn_cancel = QPushButton("Cancel")
        self.btn_cancel.setFixedWidth(80)
        self.btn_cancel.clicked.connect(self.close)
        bottom_layout.addWidget(self.btn_cancel)
        
        self.layout.addWidget(self.bottom_bar)
        
        # Setup pages
        self.setup_pages()
        self.update_buttons()

    def create_icon(self, status):
        pixmap = QPixmap(24, 24)
        pixmap.fill(Qt.GlobalColor.transparent)
        painter = QPainter(pixmap)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        if status == 'pending':
            painter.setPen(QPen(QColor('#888888'), 4))
            painter.drawLine(8, 6, 8, 18)
            painter.drawLine(16, 6, 16, 18)
        elif status == 'installing':
            painter.setPen(Qt.PenStyle.NoPen)
            painter.setBrush(QColor('#0066cc'))
            polygon = QPolygonF([QPointF(6, 4), QPointF(18, 12), QPointF(6, 20)])
            painter.drawPolygon(polygon)
        elif status == 'completed':
            painter.setPen(QPen(QColor('#00aa00'), 3))
            painter.drawLine(4, 12, 10, 18)
            painter.drawLine(10, 18, 20, 6)
            
        painter.end()
        return QIcon(pixmap)

    def setup_pages(self):
        # Page 1: Welcome
        page1 = QWidget()
        l1 = QVBoxLayout(page1)
        l1.setContentsMargins(30, 30, 30, 30)
        title1 = QLabel("Welcome to the ZeroTraceFS Setup Wizard")
        title1.setFont(QFont("Arial", 12, QFont.Weight.Bold))
        l1.addWidget(title1)
        l1.addWidget(QLabel("\nThe installer will guide you through the steps required to install ZeroTraceFS on your computer.\n\n\n\nWARNING: This computer program is protected by copyright law and international treaties."))
        l1.addStretch()
        self.stacked_widget.addWidget(page1)
        
        # Page 2: Select Folder
        page2 = QWidget()
        l2 = QVBoxLayout(page2)
        l2.setContentsMargins(30, 30, 30, 30)
        title2 = QLabel("Select Installation Folder")
        title2.setFont(QFont("Arial", 12, QFont.Weight.Bold))
        l2.addWidget(title2)
        l2.addWidget(QLabel("\nThe installer will install ZeroTraceFS to the following folder.\nTo install in this folder, click \"Next\". To install to a different folder, enter it below or click \"Browse\"."))
        
        folder_layout = QHBoxLayout()
        self.folder_input = QLineEdit("C:\\Program Files\\ZeroTraceFS\\")
        folder_layout.addWidget(self.folder_input)
        btn_browse = QPushButton("Browse...")
        btn_browse.clicked.connect(lambda: self.folder_input.setText(QFileDialog.getExistingDirectory(self, "Select Folder") or self.folder_input.text()))
        folder_layout.addWidget(btn_browse)
        btn_disk = QPushButton("Disk Cost...")
        folder_layout.addWidget(btn_disk)
        l2.addLayout(folder_layout)
        
        l2.addWidget(QLabel("\nInstall ZeroTraceFS for yourself, or for anyone who uses this computer:"))
        self.rb_everyone = QRadioButton("Everyone")
        self.rb_justme = QRadioButton("Just me")
        self.rb_justme.setChecked(True)
        l2.addWidget(self.rb_everyone)
        l2.addWidget(self.rb_justme)
        l2.addStretch()
        self.stacked_widget.addWidget(page2)
        
        # Page 3: Confirm
        page3 = QWidget()
        l3 = QVBoxLayout(page3)
        l3.setContentsMargins(30, 30, 30, 30)
        title3 = QLabel("Confirm Installation")
        title3.setFont(QFont("Arial", 12, QFont.Weight.Bold))
        l3.addWidget(title3)
        l3.addWidget(QLabel("\nThe installer is ready to install ZeroTraceFS on your computer.\nClick \"Next\" to start the installation."))
        l3.addStretch()
        self.stacked_widget.addWidget(page3)
        
        # Page 4: Install Progress (VS 2010 Style)
        page4 = QWidget()
        l4 = QVBoxLayout(page4)
        l4.setContentsMargins(20, 20, 20, 20)
        
        lbl_installing = QLabel("Installing Components:")
        lbl_installing.setFont(QFont("Arial", 10, QFont.Weight.Bold))
        l4.addWidget(lbl_installing)
        
        self.components_list = QListWidget()
        self.components_list.setStyleSheet("QListWidget { background-color: white; border: 1px solid #ccc; } QListWidget::item { padding: 5px; color: #555; } QListWidget::item:selected { background-color: transparent; color: #555; }")
        
        self.components = [
            "ZeroTraceFS Core Runtime",
            "ZeroTraceFS Cloud Sync Module",
            "ZeroTraceFS Encryption Engine",
            "PyQt6 GUI Components",
            "Virtual File System Drivers",
            "Setup Registry Keys",
            "Creating Shortcuts"
        ]
        
        self.icon_pending = self.create_icon('pending')
        self.icon_installing = self.create_icon('installing')
        self.icon_completed = self.create_icon('completed')
        
        for comp in self.components:
            item = QListWidgetItem(self.icon_pending, comp)
            self.components_list.addItem(item)
            
        l4.addWidget(self.components_list)
        
        info_layout = QHBoxLayout()
        self.lbl_dir = QLabel("Directory: C:\\Program Files\\ZeroTraceFS\\")
        info_layout.addWidget(self.lbl_dir)
        info_layout.addStretch()
        l4.addLayout(info_layout)
        
        self.lbl_file = QLabel("File: Waiting to start...")
        l4.addWidget(self.lbl_file)
        
        self.progress_bar = QProgressBar()
        self.progress_bar.setStyleSheet("""
            QProgressBar {
                border: 1px solid #bbb;
                background: #e6e6e6;
                height: 15px;
                text-align: center;
            }
            QProgressBar::chunk {
                background-color: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 #4caf50, stop:1 #388e3c);
            }
        """)
        self.progress_bar.setTextVisible(False)
        l4.addWidget(self.progress_bar)
        
        self.stacked_widget.addWidget(page4)
        
        # Page 5: Serial Key
        page5 = QWidget()
        l5 = QVBoxLayout(page5)
        l5.setContentsMargins(30, 30, 30, 30)
        title5 = QLabel("Type your product key")
        title5.setFont(QFont("Arial", 12, QFont.Weight.Bold))
        l5.addWidget(title5)
        
        info_box = QFrame()
        info_box.setStyleSheet("background-color: #f5f5f5; border: 1px solid #ddd; padding: 10px;")
        il = QVBoxLayout(info_box)
        il.addWidget(QLabel("You can find the ZeroTraceFS product key in the email we sent you. Activation will register the product key to this computer."))
        l5.addWidget(info_box)
        
        l5.addWidget(QLabel("\nProduct Key:"))
        self.key_input = QLineEdit()
        self.key_input.setPlaceholderText("XXXXX-XXXXX-XXXXX-XXXXX-XXXXX")
        l5.addWidget(self.key_input)
        l5.addStretch()
        self.stacked_widget.addWidget(page5)
        
        # Page 6: Finish
        page6 = QWidget()
        l6 = QVBoxLayout(page6)
        l6.setContentsMargins(30, 30, 30, 30)
        title6 = QLabel("Installation Complete")
        title6.setFont(QFont("Arial", 12, QFont.Weight.Bold))
        l6.addWidget(title6)
        l6.addWidget(QLabel("\nZeroTraceFS has been successfully installed.\nClick \"Finish\" to exit."))
        l6.addStretch()
        self.stacked_widget.addWidget(page6)

    def go_next(self):
        idx = self.stacked_widget.currentIndex()
        if idx == 2: # Going to install page
            self.stacked_widget.setCurrentIndex(3)
            self.lbl_dir.setText(f"Directory: {self.folder_input.text()}")
            self.start_installation()
        elif idx == 4: # Serial Key page
            self.stacked_widget.setCurrentIndex(5)
        elif idx == 5: # Finish page
            self.close()
        else:
            self.stacked_widget.setCurrentIndex(idx + 1)
        self.update_buttons()

    def go_back(self):
        idx = self.stacked_widget.currentIndex()
        if idx > 0:
            self.stacked_widget.setCurrentIndex(idx - 1)
        self.update_buttons()

    def update_buttons(self):
        idx = self.stacked_widget.currentIndex()
        self.btn_back.setEnabled(idx not in [0, 3, 5])
        
        if idx == 3: # Installing
            self.btn_next.setEnabled(False)
            self.btn_cancel.setEnabled(False)
        elif idx == 4: # Key validation
            self.btn_next.setText("Next")
            self.btn_cancel.setEnabled(True)
        elif idx == 5:
            self.btn_next.setText("Finish")
            self.btn_next.setEnabled(True)
            self.btn_cancel.setEnabled(False)
        else:
            self.btn_next.setText("Next >")
            self.btn_next.setEnabled(True)
            self.btn_cancel.setEnabled(True)

    def start_installation(self):
        self.update_buttons()
        self.thread = InstallThread(len(self.components))
        self.thread.item_started.connect(self.on_item_started)
        self.thread.progress_update.connect(self.on_item_progress)
        self.thread.item_completed.connect(self.on_item_completed)
        self.thread.finished_install.connect(self.on_install_finished)
        self.thread.start()

    def on_item_started(self, idx):
        item = self.components_list.item(idx)
        item.setIcon(self.icon_installing)
        font = item.font()
        font.setBold(True)
        item.setFont(font)
        item.setForeground(QColor("black"))
        self.lbl_file.setText(f"File: Installing {self.components[idx]}...")
        self.components_list.scrollToItem(item)

    def on_item_progress(self, idx, progress):
        total_progress = int(((idx * 100) + progress) / len(self.components))
        self.progress_bar.setValue(total_progress)

    def on_item_completed(self, idx):
        item = self.components_list.item(idx)
        item.setIcon(self.icon_completed)
        font = item.font()
        font.setBold(False)
        item.setFont(font)
        item.setForeground(QColor("#555555"))

    def on_install_finished(self):
        self.lbl_file.setText("File: Installation complete.")
        self.progress_bar.setValue(100)
        self.go_next() # Move to serial key page automatically after small delay
        # Or better, just wait 1 second
        QTimer.singleShot(1000, self.go_next)

if __name__ == "__main__":
    app = QApplication(sys.argv)
    
    # Force Fusion style to prevent Windows 11 native style artifacts
    app.setStyle("Fusion")
    
    # Force light theme globally to avoid dark mode issues on Windows 11
    app.setStyleSheet("""
        QWidget {
            background-color: #f0f0f0;
            color: black;
        }
        QFrame {
            background-color: transparent;
        }
        QLabel {
            background-color: transparent;
        }
        QPushButton {
            background-color: #e1e1e1;
            border: 1px solid #adadad;
            padding: 4px 15px;
            color: black;
        }
        QPushButton:hover {
            background-color: #e5f1fb;
            border: 1px solid #0078d7;
        }
        QPushButton:disabled {
            background-color: #f0f0f0;
            color: #a0a0a0;
            border: 1px solid #d0d0d0;
        }
        QLineEdit {
            background-color: white;
            color: black;
            border: 1px solid #ccc;
            padding: 2px;
        }
        QListWidget {
            background-color: white;
            color: black;
            border: 1px solid #ccc;
        }
        QRadioButton {
            background-color: transparent;
            color: black;
        }
    """)
    
    # Visual studio style application wide font
    app.setFont(QFont("Segoe UI", 9))
    
    wizard = InstallerWizard()
    wizard.show()
    sys.exit(app.exec())
