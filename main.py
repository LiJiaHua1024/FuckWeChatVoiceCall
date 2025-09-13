import sys
import pyaudio
import queue
import socket

from PySide6.QtCore import QObject, Signal, Slot
from PySide6.QtWidgets import QApplication, QWidget, QVBoxLayout, QHBoxLayout
from qfluentwidgets import (setTheme, Theme, ComboBox, LineEdit, PushButton, SubtitleLabel, BodyLabel, InfoBar, InfoBarPosition)

from audio import AudioStreamer
from network import NetworkStreamer

# A custom QObject to handle signals from worker threads
class CommunicationManager(QObject):
    status_changed = Signal(str)
    peer_connected = Signal(str, int)

class VoiceChatWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Voice Chat")
        self.setGeometry(100, 100, 500, 350)

        self.audio_streamer = None
        self.network_streamer = None
        self.outgoing_queue = queue.Queue()
        self.incoming_queue = queue.Queue()

        # Communication manager for thread-safe GUI updates
        self.comm_manager = CommunicationManager()
        self.comm_manager.status_changed.connect(self.update_status)
        self.comm_manager.peer_connected.connect(self.on_peer_connected)

        self.init_ui()
        self.populate_audio_devices()

    def init_ui(self):
        self.layout = QVBoxLayout(self)

        self.title_label = SubtitleLabel("P2P Voice Chat", self)
        self.layout.addWidget(self.title_label)

        self.audio_layout = QHBoxLayout()
        self.mic_combo = ComboBox(self)
        self.speaker_combo = ComboBox(self)
        self.audio_layout.addWidget(BodyLabel("Microphone:", self))
        self.audio_layout.addWidget(self.mic_combo)
        self.audio_layout.addWidget(BodyLabel("Speaker:", self))
        self.audio_layout.addWidget(self.speaker_combo)
        self.layout.addLayout(self.audio_layout)

        self.ip_layout = QHBoxLayout()
        self.ip_input = LineEdit(self)
        self.ip_input.setPlaceholderText("Enter peer's IP (e.g., ::1 or 127.0.0.1)")
        self.port_input = LineEdit(self)
        self.port_input.setText("12345") # Default port
        self.port_input.setFixedWidth(80)
        self.ip_layout.addWidget(BodyLabel("Peer IP/Port:", self))
        self.ip_layout.addWidget(self.ip_input)
        self.ip_layout.addWidget(self.port_input)
        self.layout.addLayout(self.ip_layout)

        self.button_layout = QHBoxLayout()
        self.call_button = PushButton("Call", self)
        self.hangup_button = PushButton("Hang Up", self)
        self.hangup_button.setEnabled(False)
        self.button_layout.addWidget(self.call_button)
        self.button_layout.addWidget(self.hangup_button)
        self.layout.addLayout(self.button_layout)

        self.status_label = BodyLabel("Status: Idle", self)
        self.layout.addWidget(self.status_label)

        # Connect signals
        self.call_button.clicked.connect(self.start_call)
        self.hangup_button.clicked.connect(self.stop_call)

    def populate_audio_devices(self):
        p = pyaudio.PyAudio()
        for i in range(p.get_device_count()):
            dev = p.get_device_info_by_index(i)
            if dev['maxInputChannels'] > 0:
                self.mic_combo.addItem(dev['name'], userData=i)
            if dev['maxOutputChannels'] > 0:
                self.speaker_combo.addItem(dev['name'], userData=i)
        p.terminate()

    def start_call(self):
        peer_ip = self.ip_input.text()
        try:
            peer_port = int(self.port_input.text())
            if not (1024 <= peer_port <= 65535):
                raise ValueError("Port must be between 1024 and 65535")
        except ValueError as e:
            self.show_error_info(f"Invalid Port: {e}")
            return

        if not peer_ip:
            self.show_error_info("Peer IP address cannot be empty.")
            return

        self.comm_manager.status_changed.emit("Connecting...")

        # For simplicity, we'll use the same port for local and peer,
        # but in a real app this might be different.
        local_port = peer_port

        # Network
        # We bind to '::' to listen on all available IPv6 and IPv4 interfaces
        try:
            self.network_streamer = NetworkStreamer('::', local_port, self.outgoing_queue, self.incoming_queue, self.comm_manager)
            self.network_streamer.set_peer(peer_ip, peer_port)
            self.network_streamer.start()
        except Exception as e:
            print(f"Failed to start network streamer: {e}")
            self.update_ui_for_call(False)
            return

        # Audio
        mic_index = self.mic_combo.currentData()
        speaker_index = self.speaker_combo.currentData()
        self.audio_streamer = AudioStreamer(mic_index, speaker_index, self.outgoing_queue, self.incoming_queue)
        self.audio_streamer.start()

        self.update_ui_for_call(True)
        self.comm_manager.status_changed.emit("In Call")

    def stop_call(self):
        self.comm_manager.status_changed.emit("Disconnecting...")
        if self.audio_streamer:
            self.audio_streamer.stop()
        if self.network_streamer:
            self.network_streamer.stop()

        # Clear queues
        self.outgoing_queue = queue.Queue()
        self.incoming_queue = queue.Queue()

        self.update_ui_for_call(False)
        self.comm_manager.status_changed.emit("Idle")

    @Slot(str)
    def update_status(self, status):
        self.status_label.setText(f"Status: {status}")

    @Slot(str, int)
    def on_peer_connected(self, ip, port):
        self.ip_input.setText(ip)
        self.port_input.setText(str(port))
        self.show_success_info(f"Connected to {ip}:{port}")

    def update_ui_for_call(self, in_call):
        self.call_button.setEnabled(not in_call)
        self.hangup_button.setEnabled(in_call)
        self.ip_input.setEnabled(not in_call)
        self.port_input.setEnabled(not in_call)
        self.mic_combo.setEnabled(not in_call)
        self.speaker_combo.setEnabled(not in_call)

    def show_error_info(self, message):
        InfoBar.error("Error", message, duration=3000, position=InfoBarPosition.TOP, parent=self)

    def show_success_info(self, message):
        InfoBar.success("Success", message, duration=3000, position=InfoBarPosition.TOP, parent=self)

    def closeEvent(self, event):
        """Ensure threads are stopped when closing the window."""
        self.stop_call()
        event.accept()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    setTheme(Theme.DARK)
    window = VoiceChatWindow()
    window.show()
    sys.exit(app.exec())
