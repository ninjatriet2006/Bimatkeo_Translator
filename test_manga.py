import os, sys
sys.path.insert(0, os.path.abspath('.'))
from app.core.factories import InpainterFactory
import app.core.pipeline
cls = InpainterFactory.get_class("manga")
print("Manga class:", cls)
