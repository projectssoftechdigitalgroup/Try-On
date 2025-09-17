import os
import cv2
import numpy as np
import tensorflow as tf

BASE_DIR = os.path.dirname(os.path.dirname(__file__))   # backend/
TEMPLATES_DIR = os.path.join(BASE_DIR, "data", "templates")
MODEL_PATH = os.path.join(BASE_DIR, "dmt.pb")
IMG_SIZE = 256

def get_template_path(occasion: str, filename: str = "sample1.png"):
    path = os.path.join(TEMPLATES_DIR, occasion, filename)
    return path if os.path.exists(path) else None

def _preprocess_rgb(img_rgb: np.ndarray) -> np.ndarray:
    x = img_rgb.astype(np.float32) / 255.0
    return (x - 0.5) * 2.0

def _deprocess_to_uint8_rgb(x: np.ndarray) -> np.ndarray:
    y = (x + 1.0) / 2.0
    return np.clip(y * 255.0, 0, 255).astype(np.uint8)

def _resize_to_model(img_bgr: np.ndarray) -> np.ndarray:
    img = cv2.resize(img_bgr, (IMG_SIZE, IMG_SIZE), interpolation=cv2.INTER_AREA)
    return cv2.cvtColor(img, cv2.COLOR_BGR2RGB)

# ------- Load BeautyGAN once -------
_graph = _sess = _X = _Y = _Xs = None
_load_error = None
try:
    tf.compat.v1.reset_default_graph()
    _graph = tf.Graph()
    with _graph.as_default():
        gd = tf.compat.v1.GraphDef()
        with open(MODEL_PATH, "rb") as f:
            gd.ParseFromString(f.read())
            tf.import_graph_def(gd, name="")
        _X  = _graph.get_tensor_by_name("X:0")
        _Y  = _graph.get_tensor_by_name("Y:0")
        _Xs = _graph.get_tensor_by_name("decoder_1/g:0")
        cfg = tf.compat.v1.ConfigProto()
        cfg.gpu_options.allow_growth = True
        _sess = tf.compat.v1.Session(graph=_graph, config=cfg)
except Exception as e:
    _load_error = e

def makeupTransfer(user_img_bgr: np.ndarray, template_img_bgr: np.ndarray) -> np.ndarray:
    if _load_error:
        raise RuntimeError(f"BeautyGAN failed to load: {_load_error}")
    if user_img_bgr is None or template_img_bgr is None:
        raise ValueError("Empty input images.")
    H, W = user_img_bgr.shape[:2]
    A = _preprocess_rgb(_resize_to_model(user_img_bgr))[None, ...]
    B = _preprocess_rgb(_resize_to_model(template_img_bgr))[None, ...]
    out = _sess.run(_Xs, feed_dict={_X: A, _Y: B})
    if out is None or out.shape[0] == 0:
        raise RuntimeError("BeautyGAN returned no output.")
    rgb_256 = _deprocess_to_uint8_rgb(out[0])
    return cv2.resize(rgb_256, (W, H), interpolation=cv2.INTER_CUBIC)
