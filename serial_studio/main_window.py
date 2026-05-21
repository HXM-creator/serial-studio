"""Main application window."""

from collections import deque
from pathlib import Path

import numpy as np
import pyqtgraph as pg
from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtWidgets import (
    QApplication,
    QCheckBox,
    QComboBox,
    QFileDialog,
    QFrame,
    QHBoxLayout,
    QLabel,
    QMainWindow,
    QMessageBox,
    QPushButton,
    QScrollArea,
    QSpinBox,
    QVBoxLayout,
    QWidget,
)

from .parser import parse_line
from .serial_thread import SerialReader, available_ports

MAX_SAMPLES = 2000


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Serial Studio")
        self.resize(1000, 650)

        self._reader = SerialReader()
        self._reader.data_received.connect(self._on_data)
        self._reader.connection_error.connect(self._on_error)
        self._reader.connected_signal.connect(self._on_connected)
        self._reader.disconnected_signal.connect(self._on_disconnected)

        self._ch_data: list[deque] = []           # one deque per channel
        self._ch_curves: dict[int, pg.PlotDataItem] = {}
        self._ch_enabled: list[bool] = []
        self._ch_names: list[str] = []

        self._sample_count = 0
        self._setup_ui()
        self._refresh_ports()

        # Refresh port list every 3 s
        self._port_timer = QTimer()
        self._port_timer.timeout.connect(self._refresh_ports)
        self._port_timer.start(3000)

    # ── UI ──────────────────────────────────────────────────
    def _setup_ui(self):
        cw = QWidget()
        self.setCentralWidget(cw)
        layout = QHBoxLayout(cw)
        layout.setSpacing(6)

        # --- Left panel ---
        left = QFrame()
        left.setFixedWidth(220)
        left.setStyleSheet("QFrame { border: 0; }")
        left_layout = QVBoxLayout(left)
        left_layout.setSpacing(4)
        left_layout.setContentsMargins(4, 4, 4, 4)

        left_layout.addWidget(QLabel("Port"))
        self._port_combo = QComboBox()
        left_layout.addWidget(self._port_combo)

        left_layout.addWidget(QLabel("Baud rate"))
        self._baud_combo = QComboBox()
        for b in (9600, 19200, 38400, 57600, 115200, 230400, 460800, 921600):
            self._baud_combo.addItem(str(b), b)
        self._baud_combo.setCurrentText("115200")
        left_layout.addWidget(self._baud_combo)

        self._connect_btn = QPushButton("Connect")
        self._connect_btn.clicked.connect(self._toggle_connection)
        left_layout.addWidget(self._connect_btn)

        left_layout.addSpacing(12)

        left_layout.addWidget(QLabel("Channels"))
        self._ch_scroll = QScrollArea()
        self._ch_scroll.setWidgetResizable(True)
        self._ch_container = QWidget()
        self._ch_layout = QVBoxLayout(self._ch_container)
        self._ch_layout.setSpacing(2)
        self._ch_layout.setContentsMargins(0, 0, 0, 0)
        self._ch_layout.addStretch()
        self._ch_scroll.setWidget(self._ch_container)
        left_layout.addWidget(self._ch_scroll, stretch=1)

        left_layout.addSpacing(8)

        self._export_btn = QPushButton("Export CSV")
        self._export_btn.clicked.connect(self._export_csv)
        left_layout.addWidget(self._export_btn)

        self._clear_btn = QPushButton("Clear")
        self._clear_btn.clicked.connect(self._clear_data)
        left_layout.addWidget(self._clear_btn)

        # --- Right panel: plot ---
        self._plot = pg.PlotWidget()
        self._plot.setBackground("#1e1e1e")
        self._plot.showGrid(x=True, y=True, alpha=0.3)
        self._plot.setLabel("left", "Value")
        self._plot.setLabel("bottom", "Sample")
        self._plot.addLegend()
        layout.addWidget(self._plot, stretch=1)

        # --- Status bar ---
        self._status = self.statusBar()
        self._status_label = QLabel("Disconnected")
        self._status.addPermanentWidget(self._status_label)

        layout.addWidget(left)

    # ── Port refresh ────────────────────────────────────────
    def _refresh_ports(self):
        current = self._port_combo.currentText()
        self._port_combo.blockSignals(True)
        self._port_combo.clear()
        self._port_combo.addItems(available_ports())
        idx = self._port_combo.findText(current)
        if idx >= 0:
            self._port_combo.setCurrentIndex(idx)
        self._port_combo.blockSignals(False)

    # ── Connection ──────────────────────────────────────────
    def _toggle_connection(self):
        if self._reader.isRunning():
            self._reader.close()
            return
        port = self._port_combo.currentText()
        baud = self._baud_combo.currentData()
        if not port:
            return
        self._reader.configure(port, baud)
        err = self._reader.open()
        if err:
            QMessageBox.warning(self, "Error", err)

    def _on_connected(self):
        self._connect_btn.setText("Disconnect")
        self._port_combo.setEnabled(False)
        self._baud_combo.setEnabled(False)
        self._status_label.setText("Connected")
        self._port_timer.stop()

    def _on_disconnected(self):
        self._connect_btn.setText("Connect")
        self._port_combo.setEnabled(True)
        self._baud_combo.setEnabled(True)
        self._status_label.setText("Disconnected")
        self._port_timer.start(3000)

    def _on_error(self, msg):
        self._status_label.setText(msg)

    # ── Data handling ───────────────────────────────────────
    def _on_data(self, line: str):
        values = parse_line(line)
        if not values:
            return

        # Auto-create channels
        if len(values) > len(self._ch_data):
            self._add_channels(len(values))

        self._sample_count += 1

        for i, v in enumerate(values):
            if i < len(self._ch_data) and self._ch_enabled[i]:
                self._ch_data[i].append(v)

        # Update curves at a sensible rate (every sample for simplicity)
        for i in range(min(len(values), len(self._ch_data))):
            if self._ch_enabled[i] and i in self._ch_curves:
                self._ch_curves[i].setData(np.array(self._ch_data[i]))

        self._status_label.setText(f"Connected — {self._sample_count} samples")

    def _add_channels(self, n: int):
        """Ensure we have at least n channels."""
        colours = ["#ff6b6b", "#4ecdc4", "#45b7d1", "#f9ca24",
                   "#a29bfe", "#fd79a8", "#00b894", "#e17055"]
        names = [f"CH{i+1}" for i in range(n)]

        while len(self._ch_data) < n:
            i = len(self._ch_data)
            self._ch_data.append(deque(maxlen=MAX_SAMPLES))
            self._ch_enabled.append(True)
            self._ch_names.append(names[i])

            colour = colours[i % len(colours)]
            curve = self._plot.plot([], [], pen=pg.mkPen(colour, width=1.5),
                                    name=names[i])
            self._ch_curves[i] = curve

            cb = QCheckBox(names[i])
            cb.setChecked(True)
            cb.setStyleSheet(f"color: {colour}")
            cb.toggled.connect(lambda checked, idx=i: self._toggle_ch(idx, checked))
            self._ch_layout.insertWidget(len(self._ch_data) - 1, cb)

    def _toggle_ch(self, idx: int, enabled: bool):
        self._ch_enabled[idx] = enabled
        if idx in self._ch_curves:
            self._ch_curves[idx].setVisible(enabled)

    # ── Clear / Export ──────────────────────────────────────
    def _clear_data(self):
        self._sample_count = 0
        for dq in self._ch_data:
            dq.clear()
        for curve in self._ch_curves.values():
            curve.setData([])

    def _export_csv(self):
        if all(len(dq) == 0 for dq in self._ch_data):
            QMessageBox.information(self, "Export", "No data to export.")
            return

        path, _ = QFileDialog.getSaveFileName(self, "Save CSV", "", "CSV (*.csv)")
        if not path:
            return

        header = "sample," + ",".join(self._ch_names)
        n = max(len(dq) for dq in self._ch_data)
        with open(path, "w") as f:
            f.write(header + "\n")
            for i in range(n):
                row = [str(i)]
                for dq in self._ch_data:
                    row.append(str(dq[i]) if i < len(dq) else "")
                f.write(",".join(row) + "\n")

        self._status_label.setText(f"Exported {n} rows to {Path(path).name}")


def launch():
    import sys
    app = QApplication(sys.argv)
    win = MainWindow()
    win.show()
    sys.exit(app.exec())
