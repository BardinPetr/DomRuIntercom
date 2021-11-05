import time
import webbrowser
from threading import Lock, Thread

import cv2
from flask import Flask, render_template_string
from flask import Response
from werkzeug.serving import make_server


class WebVideoStreamServer(Thread):
    def __init__(self, port=8998, open_browser=False):
        super().__init__(name='web-stream-thread')
        self.lock = Lock()
        self.running = True
        self.frame = None

        self.app = Flask(self.name)
        self.app.add_url_rule('/', 'index', self.index)
        self.app.add_url_rule('/video', 'video', self.video_feed)

        self.server = make_server('0.0.0.0', port, self.app)
        self.ctx = self.app.app_context()
        self.ctx.push()

        self.start()

        if open_browser:
            try:
                webbrowser.open_new_tab(f'http://0.0.0.0:{port}')
            except:
                pass

    def run(self):
        self.server.serve_forever()

    def stop(self):
        self.running = False
        self.server.shutdown()

    @staticmethod
    def index():
        return render_template_string(
            '<html><head><title>Stream</title></head><body><img src=\"{{ url_for(\'video\') }}\"></body></html>'
        )

    def video_feed(self):
        return Response(self.generate(), mimetype="multipart/x-mixed-replace; boundary=frame")

    def __call__(self, frame):
        with self.lock:
            self.frame = frame

    def _formatted_frame(self):
        ret, img = cv2.imencode(".jpg", self.frame)
        if not ret:
            return None
        self.frame = None
        return b'--frame\r\n' b'Content-Type: image/jpeg\r\n\r\n' + bytearray(img) + b'\r\n'

    def generate(self):
        while self.running:
            with self.lock:
                if self.frame is None:
                    time.sleep(0.01)
                    continue
                res = self._formatted_frame()
                if res is not None:
                    yield res


if __name__ == "__main__":
    srv = WebVideoStreamServer()

    cap = cv2.VideoCapture(0)

    while True:
        try:
            _, frame = cap.read()
            srv(frame.copy())
        except:
            break

    srv.stop()
    cap.release()
