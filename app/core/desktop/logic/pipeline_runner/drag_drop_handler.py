import os

class DragDropHandler:
    def __init__(self, main_window):
        self.mw = main_window

    def dragEnterEvent(self, event):
        if event.mimeData().hasUrls():
            event.acceptProposedAction()
        else:
            event.ignore()

    def dragMoveEvent(self, event):
        if event.mimeData().hasUrls():
            event.acceptProposedAction()
        else:
            event.ignore()

    def dropEvent(self, event):
        if event.mimeData().hasUrls():
            for url in event.mimeData().urls():
                path = url.toLocalFile()
                if os.path.isdir(path):
                    self.mw._add_job_from_path(path)
                else:
                    self.mw.log("WARNING", f"Dropped item is not a directory: {path}")
            event.acceptProposedAction()
        else:
            event.ignore()
