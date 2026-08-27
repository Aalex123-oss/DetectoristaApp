"""Captura de vídeo OpenCV con un único fotograma pendiente."""

from collections import deque
import threading
import time
from typing import Any, Optional

import cv2


class VideoCaptureThread:
    """Mantiene el fotograma más reciente para reducir la latencia."""

    def __init__(self, source: Any = 0) -> None:
        self.source = source
        self.capture = None
        self.frames = deque(maxlen=1)
        self.lock = threading.Lock()
        self.thread: Optional[threading.Thread] = None
        self.running = False
        self.last_error = ""
        self.fps = 0.0

    def start(self) -> bool:
        """Inicia la captura si hay una fuente configurada."""
        if self.source is None:
            return False
        self.running = True
        self.thread = threading.Thread(target=self._run, name="captura-video", daemon=True)
        self.thread.start()
        return True

    def _run(self) -> None:
        try:
            source = int(self.source) if isinstance(self.source, str) and self.source.isdigit() else self.source
            self.capture = cv2.VideoCapture(source)
            if not self.capture.isOpened():
                self.last_error = f"No se pudo abrir la fuente de vídeo: {source}"
                self.running = False
                return
            previous = time.monotonic()
            count = 0
            while self.running:
                ok, frame = self.capture.read()
                if not ok:
                    self.last_error = "Se perdió la captura de vídeo"
                    time.sleep(0.1)
                    continue
                with self.lock:
                    self.frames.append(frame)
                count += 1
                elapsed = time.monotonic() - previous
                if elapsed >= 1.0:
                    self.fps = count / elapsed
                    count = 0
                    previous = time.monotonic()
        except Exception as exc:
            self.last_error = str(exc)
        finally:
            if self.capture is not None:
                self.capture.release()
            self.capture = None

    def latest(self) -> Optional[Any]:
        """Devuelve el fotograma más reciente sin esperar."""
        with self.lock:
            return self.frames[-1].copy() if self.frames else None

    def stop(self) -> None:
        """Detiene el hilo y libera la cámara."""
        self.running = False
        if self.thread and self.thread.is_alive():
            self.thread.join(timeout=1.0)
        self.thread = None
