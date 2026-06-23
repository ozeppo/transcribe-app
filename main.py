import os
import subprocess
import sys
import threading
import shutil
from pathlib import Path
from datetime import timedelta


def add_common_tool_paths():
    """Make Homebrew tools visible when the app starts outside a login shell."""
    current_paths = os.environ.get("PATH", "").split(os.pathsep)
    extra_paths = [
        path for path in ("/opt/homebrew/bin", "/usr/local/bin")
        if Path(path).is_dir() and path not in current_paths
    ]

    if extra_paths:
        os.environ["PATH"] = os.pathsep.join(extra_paths + current_paths)


def relaunch_for_compatible_torch():
    """Relaunch direct IDE/script runs when the local Torch wheel is x86_64."""
    if sys.platform != "darwin" or os.uname().machine != "arm64":
        return

    if os.environ.get("WHISPERAI_ARCH_REEXEC") == "1":
        return

    try:
        if Path(sys.argv[0]).resolve() != Path(__file__).resolve():
            return
    except OSError:
        return

    project_dir = Path(__file__).resolve().parent
    venv_dir = project_dir / "venv"

    try:
        venv_resolved = venv_dir.resolve()
        prefix_resolved = Path(sys.prefix).resolve()
    except OSError:
        return

    if prefix_resolved != venv_resolved:
        return

    torch_deps = venv_dir / "lib/python3.9/site-packages/torch/lib/libtorch_global_deps.dylib"
    if not torch_deps.exists():
        return

    file_result = subprocess.run(["file", str(torch_deps)], capture_output=True, text=True)
    if "x86_64" not in file_result.stdout:
        return

    rosetta_result = subprocess.run(["arch", "-x86_64", "/usr/bin/true"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    if rosetta_result.returncode != 0:
        return

    env = os.environ.copy()
    env["WHISPERAI_ARCH_REEXEC"] = "1"
    os.execvpe("arch", ["arch", "-x86_64", sys.executable, *sys.argv], env)


add_common_tool_paths()
relaunch_for_compatible_torch()


from PyQt5.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
                             QGroupBox, QLabel, QLineEdit, QComboBox, QSpinBox, QPushButton,
                             QTextEdit, QProgressBar, QFileDialog, QMessageBox)
from PyQt5.QtCore import Qt, pyqtSignal, QObject
from PyQt5.QtGui import QFont, QColor

from formatter import format_time, format_text, split_segments_by_words


def check_ffmpeg():
    """Check if ffmpeg is installed on the system"""
    if shutil.which("ffmpeg") is None:
        print("ERROR: ffmpeg is not installed!")
        print("\nffmpeg is required for audio/video processing with Whisper.")
        print("\nPlease install it using:")
        print("  brew install ffmpeg")
        print("\nOr visit: https://ffmpeg.org/download.html")
        sys.exit(1)


class WorkerSignals(QObject):
    """Signals for worker thread"""
    status_changed = pyqtSignal(str, str)  # message, color
    info_added = pyqtSignal(str)
    processing_finished = pyqtSignal(bool, str)  # success, message (for QMessageBox)
    progress_started = pyqtSignal()
    progress_stopped = pyqtSignal()
    error_occurred = pyqtSignal(str, str)  # title, message


class WhisperSRTGenerator(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Whisper SRT Generator")
        self.setGeometry(100, 100, 900, 850)
        
        self.file_path = ""
        self.output_path = str(Path.home())  # Default to home directory
        self.model = None
        self.is_processing = False
        self.worker_signals = WorkerSignals()
        
        self.worker_signals.status_changed.connect(self.update_status)
        self.worker_signals.info_added.connect(self.add_info)
        self.worker_signals.progress_started.connect(self.start_progress)
        self.worker_signals.progress_stopped.connect(self.stop_progress)
        self.worker_signals.processing_finished.connect(self.on_processing_finished)
        self.worker_signals.error_occurred.connect(self.on_error)
        
        self.setup_ui()
        
    def setup_ui(self):
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)
        main_layout.setSpacing(10)
        main_layout.setContentsMargins(15, 15, 15, 15)
        
        # File selection
        file_group = QGroupBox("Plik audio/wideo")
        file_layout = QHBoxLayout()
        self.file_button = QPushButton("Wybierz plik")
        self.file_button.clicked.connect(self.select_file)
        self.file_label = QLabel("Brak wybranego pliku")
        self.file_label.setStyleSheet("color: blue;")
        file_layout.addWidget(self.file_button)
        file_layout.addWidget(self.file_label, 1)
        file_group.setLayout(file_layout)
        main_layout.addWidget(file_group)
        
        # Output directory selection
        output_group = QGroupBox("Katalog zapisu")
        output_layout = QHBoxLayout()
        self.output_button = QPushButton("Wybierz folder")
        self.output_button.clicked.connect(self.select_output_directory)
        self.output_label = QLabel(self.output_path)
        self.output_label.setStyleSheet("color: green;")
        self.output_label.setWordWrap(True)
        output_layout.addWidget(self.output_button)
        output_layout.addWidget(self.output_label, 1)
        output_group.setLayout(output_layout)
        main_layout.addWidget(output_group)
        
        # Model settings
        model_group = QGroupBox("Ustawienia modelu")
        model_layout = QVBoxLayout()
        
        # Model name
        model_name_layout = QHBoxLayout()
        model_name_layout.addWidget(QLabel("Model:"))
        self.model_combo = QComboBox()
        self.model_combo.addItems(["tiny", "base", "small", "medium", "large"])
        self.model_combo.setCurrentText("medium")
        model_name_layout.addWidget(self.model_combo)
        model_name_layout.addStretch()
        model_layout.addLayout(model_name_layout)
        
        # Device
        device_layout = QHBoxLayout()
        device_layout.addWidget(QLabel("Urządzenie:"))
        self.device_combo = QComboBox()
        self.device_combo.addItems(["cpu", "cuda"])
        self.device_combo.setCurrentText("cpu")
        device_layout.addWidget(self.device_combo)
        device_layout.addStretch()
        model_layout.addLayout(device_layout)
        
        # Language
        lang_layout = QHBoxLayout()
        lang_layout.addWidget(QLabel("Język:"))
        self.lang_combo = QComboBox()
        self.lang_combo.addItems(["auto", "pl", "en", "es", "fr", "de", "it", "pt", "ru", "zh"])
        self.lang_combo.setCurrentText("auto")
        lang_layout.addWidget(self.lang_combo)
        lang_layout.addStretch()
        model_layout.addLayout(lang_layout)
        
        model_group.setLayout(model_layout)
        main_layout.addWidget(model_group)
        
        # SRT formatting settings
        format_group = QGroupBox("Formatowanie SRT")
        format_layout = QVBoxLayout()
        
        # Max line count
        line_count_layout = QHBoxLayout()
        line_count_layout.addWidget(QLabel("Maksymalna liczba linii na napis:"))
        self.line_count_spin = QSpinBox()
        self.line_count_spin.setRange(1, 10)
        self.line_count_spin.setValue(1)
        line_count_layout.addWidget(self.line_count_spin)
        help_label = QLabel("(liczba linii tekstu w jednym napisie)")
        help_label.setStyleSheet("color: gray; font-size: 10px;")
        line_count_layout.addWidget(help_label)
        line_count_layout.addStretch()
        format_layout.addLayout(line_count_layout)
        
        # Max line width
        line_width_layout = QHBoxLayout()
        line_width_layout.addWidget(QLabel("Maksymalna szerokość linii (znaki):"))
        self.line_width_spin = QSpinBox()
        self.line_width_spin.setRange(20, 100)
        self.line_width_spin.setValue(25)
        line_width_layout.addWidget(self.line_width_spin)
        help_label2 = QLabel("(liczba znaków na linię)")
        help_label2.setStyleSheet("color: gray; font-size: 10px;")
        line_width_layout.addWidget(help_label2)
        line_width_layout.addStretch()
        format_layout.addLayout(line_width_layout)
        
        # Max words per line
        words_layout = QHBoxLayout()
        words_layout.addWidget(QLabel("Maksymalna liczba słów na napis:"))
        self.words_spin = QSpinBox()
        self.words_spin.setRange(1, 30)
        self.words_spin.setValue(3)
        words_layout.addWidget(self.words_spin)
        help_label3 = QLabel("(ile słów w każdym napisie)")
        help_label3.setStyleSheet("color: gray; font-size: 10px;")
        words_layout.addWidget(help_label3)
        words_layout.addStretch()
        format_layout.addLayout(words_layout)
        
        format_group.setLayout(format_layout)
        main_layout.addWidget(format_group)
        
        # Progress bar
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        main_layout.addWidget(self.progress_bar)
        
        # Status label
        self.status_label = QLabel("Gotowy")
        self.status_label.setStyleSheet("color: green; font-weight: bold;")
        main_layout.addWidget(self.status_label)
        
        # Buttons
        button_layout = QHBoxLayout()
        self.process_button = QPushButton("Generuj SRT")
        self.process_button.clicked.connect(self.process_file)
        self.process_button.setMinimumHeight(40)
        button_layout.addWidget(self.process_button)
        
        self.exit_button = QPushButton("Wyjście")
        self.exit_button.clicked.connect(self.close)
        self.exit_button.setMinimumHeight(40)
        button_layout.addWidget(self.exit_button)
        main_layout.addLayout(button_layout)
        
        # Info text area
        info_group = QGroupBox("Informacje")
        info_layout = QVBoxLayout()
        self.info_text = QTextEdit()
        self.info_text.setReadOnly(True)
        self.info_text.setMinimumHeight(200)
        info_layout.addWidget(self.info_text)
        info_group.setLayout(info_layout)
        main_layout.addWidget(info_group, 1)
        
    def select_file(self):
        file_filter = "Audio/Video (*.mp3 *.wav *.m4a *.mp4 *.avi *.mov *.mkv *.flac *.ogg);;All files (*.*)"
        file_path, _ = QFileDialog.getOpenFileName(self, "Wybierz plik audio/wideo", filter=file_filter)
        
        if file_path:
            self.file_path = file_path
            self.file_label.setText(file_path.split("/")[-1])
            self.add_info(f"Wybrany plik: {file_path}")
    
    def select_output_directory(self):
        directory = QFileDialog.getExistingDirectory(self, "Wybierz folder do zapisu SRT", self.output_path)
        
        if directory:
            self.output_path = directory
            self.output_label.setText(directory)
            self.add_info(f"Katalog zapisu: {directory}")
    
    def add_info(self, message):
        self.info_text.append(message)
        # Auto-scroll to bottom
        scrollbar = self.info_text.verticalScrollBar()
        scrollbar.setValue(scrollbar.maximum())
    
    def update_status(self, message, color):
        self.status_label.setText(message)
        self.status_label.setStyleSheet(f"color: {color}; font-weight: bold;")
    
    def start_progress(self):
        self.progress_bar.setVisible(True)
        self.progress_bar.setRange(0, 0)  # Indeterminate progress
        
    def stop_progress(self):
        self.progress_bar.setVisible(False)
    
    def on_processing_finished(self, success, message):
        """Handle processing finished signal from worker thread"""
        if success:
            QMessageBox.information(self, "Sukces", message)
        
    def on_error(self, title, message):
        """Handle error signal from worker thread"""
        QMessageBox.critical(self, title, message)
    
    def process_file(self):
        if not self.file_path:
            QMessageBox.critical(self, "Błąd", "Proszę wybrać plik!")
            return
        
        if self.is_processing:
            QMessageBox.warning(self, "Ostrzeżenie", "Przetwarzanie już trwa!")
            return
        
        self.is_processing = True
        self.process_button.setEnabled(False)
        self.file_button.setEnabled(False)
        
        thread = threading.Thread(target=self._process_file_thread)
        thread.daemon = True
        thread.start()
    
    def _process_file_thread(self):
        try:
            self.worker_signals.progress_started.emit()
            self.worker_signals.status_changed.emit("Przetwarzanie...", "orange")
            
            # Load model
            if not self.load_model():
                self.is_processing = False
                self.worker_signals.progress_stopped.emit()
                return
            
            self.worker_signals.info_added.emit("Transkrypcja w toku...")
            
            # Transcribe with word-level timestamps
            language = None if self.lang_combo.currentText() == "auto" else self.lang_combo.currentText()
            result = self.model.transcribe(self.file_path, language=language, word_timestamps=True, verbose=False)
            
            # Extract segments with word-level timings
            segments_list = result.get('segments', [])
            self.worker_signals.info_added.emit(f"Znalezione segmenty: {len(segments_list)}")
            for i, segment in enumerate(segments_list):
                words_count = len(segment.get('words', []))
                self.worker_signals.info_added.emit(f"Segment {i+1}: [{segment['start']:.1f}s - {segment['end']:.1f}s] ({words_count} słów) {segment['text']}")
            
            # Generate SRT with split segments
            result_with_splits = split_segments_by_words(
                segments_list,
                self.words_spin.value(),
                self.line_count_spin.value(),
                self.line_width_spin.value()
            )
            
            # Save SRT using whisper's srt_writer
            output_file = Path(self.output_path) / (Path(self.file_path).stem + ".srt")
            output_file.parent.mkdir(parents=True, exist_ok=True)
            
            from whisper.utils import get_writer
            srt_writer = get_writer("srt", str(output_file.parent))
            srt_writer(result_with_splits, self.file_path, {})
            
            self.worker_signals.info_added.emit(f"✓ SRT zapisany do: {output_file}")
            self.worker_signals.info_added.emit(f"Rozmiar pliku: {output_file.stat().st_size if output_file.exists() else 0} bajtów")
            self.worker_signals.status_changed.emit(f"Gotowe! SRT zapisany", "green")
            
            # Emit success signal (will be handled in main thread)
            self.worker_signals.processing_finished.emit(True, f"Plik SRT został wygenerowany:\n{output_file}")
            
        except Exception as e:
            self.worker_signals.status_changed.emit("Błąd!", "red")
            self.worker_signals.info_added.emit(f"BŁĄD: {str(e)}")
            # Emit error signal (will be handled in main thread)
            self.worker_signals.error_occurred.emit("Błąd", f"Błąd podczas przetwarzania:\n{str(e)}")
        
        finally:
            self.is_processing = False
            self.worker_signals.progress_stopped.emit()
            self.process_button.setEnabled(True)
            self.file_button.setEnabled(True)
    
    def load_model(self):
        if self.model is None:
            self.worker_signals.status_changed.emit(f"Ładowanie modelu {self.model_combo.currentText()}...", "orange")
            self.worker_signals.info_added.emit(f"Ładowanie modelu {self.model_combo.currentText()}...")
            try:
                import whisper
                device = "cuda" if self.device_combo.currentText() == "cuda" else "cpu"
                self.model = whisper.load_model(self.model_combo.currentText(), device=device)
                self.worker_signals.info_added.emit("Model załadowany pomyślnie!")
            except Exception as e:
                self.worker_signals.status_changed.emit("Błąd podczas ładowania modelu!", "red")
                self.worker_signals.info_added.emit(f"BŁĄD: {str(e)}")
                return False
        return True


if __name__ == "__main__":
    check_ffmpeg()
    
    app = QApplication(sys.argv)
    window = WhisperSRTGenerator()
    window.show()
    sys.exit(app.exec_())
