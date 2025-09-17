import cv2
import numpy as np
import mediapipe as mp
from typing import Dict, Tuple, List

# ---------------- FaceMesh ----------------
_mp_face_mesh = None
def get_face_mesh(static_image_mode: bool = True):
    global _mp_face_mesh
    if _mp_face_mesh is None:
        _mp_face_mesh = mp.solutions.face_mesh.FaceMesh(
            static_image_mode=static_image_mode,
            max_num_faces=1,
            refine_landmarks=True
        )
    return _mp_face_mesh

# ---------------- Landmark groups ----------------
FACE_OVAL = [10,338,297,332,284,251,389,356,454,323,361,288,397,365,379,378,400,377,152,
             148,176,149,150,136,172,58,132,93,234,127,162,21,54,103,67,109,10]
LIPS_OUTER = [61,146,91,181,84,17,314,405,321,375,291,308,324,318,402,317,14,87,178,88,95]
LIPS_INNER = [78,95,88,178,87,14,317,402,318,324,308,415,310,311,312,13,82,81,80,191,78]
CHEEKS = [425,205]
EYESHADOW_LEFT  = [33,246,161,160,159,158,157,173,243,190,56,28,27,29,30,247,33]
EYESHADOW_RIGHT = [263,466,388,387,386,385,384,398,362,414,286,258,257,259,260,467,263]
KOHL_LEFT  = [33,7,163,144,145,153,154,155,133]
KOHL_RIGHT = [263,249,390,373,374,380,381,382,362]

# ---------------- Utils ----------------
def hex_to_bgr(hex_color: str) -> Tuple[int,int,int]:
    h = hex_color.strip().lstrip("#")
    if len(h) == 3: h = "".join(c*2 for c in h)
    r,g,b = int(h[0:2],16), int(h[2:4],16), int(h[4:6],16)
    return (b,g,r)

def detect_landmarks_bgr(img_bgr: np.ndarray, is_stream=False):
    fm = get_face_mesh(static_image_mode=not is_stream)
    img_rgb = cv2.cvtColor(img_bgr, cv2.COLOR_BGR2RGB)
    res = fm.process(img_rgb)
    if not res.multi_face_landmarks:
        return None
    return res.multi_face_landmarks[0]

def landmark_dict(landmarks, shape) -> Dict[int,Tuple[int,int]]:
    h,w = shape[:2]
    return {i:(int(lm.x*w), int(lm.y*h)) for i,lm in enumerate(landmarks.landmark)}

def feather(mask,k,sigma):
    if mask.ndim==3:
        mask=cv2.cvtColor(mask,cv2.COLOR_BGR2GRAY)
    k = k + (1 - k % 2)
    return cv2.GaussianBlur(mask,(k,k),sigma)

def poly_mask(shape_hw, pts):
    m = np.zeros(shape_hw,dtype=np.uint8)
    if len(pts)>=3:
        cv2.fillPoly(m,[np.array(pts,np.int32)],255)
    return m

def _polyline_mask(shape_hw, pts, thickness):
    m = np.zeros(shape_hw,dtype=np.uint8)
    if len(pts)>=2:
        cv2.polylines(m,[np.array(pts,np.int32)],False,255,thickness,cv2.LINE_AA)
    return m

def _alpha(mask: np.ndarray, alpha: float) -> np.ndarray:
    if mask.ndim==3:
        mask=cv2.cvtColor(mask,cv2.COLOR_BGR2GRAY)
    a=(mask.astype(np.float32)/255.0)*float(alpha)
    return a[...,None]

# ---------------- Blend Modes ----------------
def blend_normal(base,color_bgr,mask,alpha):
    color=np.full_like(base,color_bgr)
    a=_alpha(mask,alpha)
    out=base.astype(np.float32)*(1-a)+color.astype(np.float32)*a
    return np.clip(out,0,255).astype(np.uint8)

def blend_multiply(base,color_bgr,mask,alpha):
    color=np.full_like(base,color_bgr)
    mul=(base.astype(np.float32)/255.0)*(color.astype(np.float32)/255.0)*255.0
    a=_alpha(mask,alpha)
    out=base.astype(np.float32)*(1-a)+mul*a
    return np.clip(out,0,255).astype(np.uint8)

def blend_softlight(base,color_bgr,mask,alpha):
    base_f=base.astype(np.float32)/255.0
    color_f=np.full_like(base_f,np.array(color_bgr,np.float32)/255.0)
    A=2*base_f*color_f+(base_f**2)*(1-2*color_f)
    soft=np.clip(A*255.0,0,255).astype(np.uint8)
    a=_alpha(mask,alpha)
    out=base.astype(np.float32)*(1-a)+soft.astype(np.float32)*a
    return np.clip(out,0,255).astype(np.uint8)

def tint_hsv_preserve_value(base,target_bgr,mask,alpha):
    base_hsv=cv2.cvtColor(base,cv2.COLOR_BGR2HSV).astype(np.float32)
    tgt_hsv=cv2.cvtColor(np.uint8([[target_bgr]]),cv2.COLOR_BGR2HSV)[0,0].astype(np.float32)
    H,S,_=tgt_hsv
    tint=base_hsv.copy()
    tint[...,0]=H
    tint[...,1]=np.clip(tint[...,1]*0.40+max(S,120)*0.60,0,255)
    tint[...,2]=np.clip(tint[...,2]*0.90+22,0,255)
    tint_bgr=cv2.cvtColor(tint.astype(np.uint8),cv2.COLOR_HSV2BGR)
    a=_alpha(mask,alpha)
    out=base.astype(np.float32)*(1-a)+tint_bgr.astype(np.float32)*a
    return np.clip(out,0,255).astype(np.uint8)

# ---------------- Masks ----------------
def lips_mask(shape,lmd):
    outer=[lmd[i] for i in LIPS_OUTER if i in lmd]
    inner=[lmd[i] for i in LIPS_INNER if i in lmd]
    m_outer=poly_mask(shape[:2],outer)
    m_inner=poly_mask(shape[:2],inner)
    m=cv2.subtract(m_outer,m_inner)
    k=cv2.getStructuringElement(cv2.MORPH_ELLIPSE,(7,7))
    m=cv2.morphologyEx(m,cv2.MORPH_CLOSE,k,iterations=1)
    m=cv2.dilate(m,k,iterations=1)
    return feather(m,11,5.0)

def cheeks_mask(shape,lmd,radius=30):
    m=np.zeros(shape[:2],dtype=np.uint8)
    for i in CHEEKS:
        if i in lmd:
            cv2.circle(m,lmd[i],radius,255,cv2.FILLED)
    return feather(m,33,18.0)

def eyeshadow_mask(shape,lmd,left=True):
    seq=EYESHADOW_LEFT if left else EYESHADOW_RIGHT
    pts=[lmd[i] for i in seq if i in lmd]
    m=poly_mask(shape[:2],pts)
    k=cv2.getStructuringElement(cv2.MORPH_ELLIPSE,(9,9))
    m=cv2.dilate(m,k,iterations=1)
    return feather(m,11,4.0)

def kohl_mask(shape,lmd,left=True,base_thickness=2,intensity=1.0):
    seq=KOHL_LEFT if left else KOHL_RIGHT
    pts=[lmd[i] for i in seq if i in lmd]
    if len(pts)<2: return np.zeros(shape[:2],np.uint8)
    shifted=[(x,y+2) for (x,y) in pts]  # lower line slightly under lashes
    mask=np.zeros(shape[:2],np.uint8)
    for i in range(len(shifted)-1):
        t=i/(len(shifted)-2)
        thick=int(base_thickness+3*t*intensity)
        cv2.line(mask,shifted[i],shifted[i+1],255,max(1,thick),cv2.LINE_AA)
    v=(shifted[-1][0]-shifted[-2][0],shifted[-1][1]-shifted[-2][1])
    norm=max(1,int(np.hypot(*v)))
    wing=(shifted[-1][0]+6*v[0]//norm,shifted[-1][1]+6*v[1]//norm)
    cv2.line(mask,shifted[-1],wing,255,int(base_thickness+3*intensity),cv2.LINE_AA)
    return feather(mask,3,0.9)

def _upper_eye_region(shape,lmd):
    L=[lmd[i] for i in EYESHADOW_LEFT if i in lmd]
    R=[lmd[i] for i in EYESHADOW_RIGHT if i in lmd]
    mL=poly_mask(shape[:2],L) if len(L)>=3 else np.zeros(shape[:2],np.uint8)
    mR=poly_mask(shape[:2],R) if len(R)>=3 else np.zeros(shape[:2],np.uint8)
    m=cv2.max(mL,mR)
    k=cv2.getStructuringElement(cv2.MORPH_ELLIPSE,(7,7))
    m=cv2.dilate(m,k,iterations=1)
    return feather(m,5,2.0)

def mascara_mask(shape,lmd,intensity=1.0):
    mL=_polyline_mask(shape[:2],[lmd[i] for i in KOHL_LEFT if i in lmd],2)
    mR=_polyline_mask(shape[:2],[lmd[i] for i in KOHL_RIGHT if i in lmd],2)
    base=cv2.max(mL,mR)
    k_v=int(10+8*intensity)
    k=np.zeros((k_v,3),np.uint8);k[:(k_v//2+1),1]=1
    dilated=cv2.dilate(base,k,iterations=1)
    eye_region=_upper_eye_region(shape,lmd)
    m=cv2.bitwise_and(dilated,eye_region)
    return feather(m,5,1.5)

def face_oval_mask(shape,lmd):
    pts=[lmd[i] for i in FACE_OVAL if i in lmd]
    m=poly_mask(shape[:2],pts)
    eyeL=eyeshadow_mask(shape,lmd,True)
    eyeR=eyeshadow_mask(shape,lmd,False)
    lip=lips_mask(shape,lmd)
    m=cv2.subtract(m,cv2.max(cv2.max(eyeL,eyeR),lip))
    return feather(m,51,22.0)

# ---------------- Public API ----------------
def apply_makeup_bgr(img_bgr: np.ndarray, feature: str, color_hex: str = "#ff1744",
                     is_stream: bool = False, intensity: float = 1.0) -> np.ndarray:
    lms=detect_landmarks_bgr(img_bgr,is_stream=is_stream)
    if lms is None: raise ValueError("No face landmarks detected.")
    lmd=landmark_dict(lms,img_bgr.shape)
    color_bgr=hex_to_bgr(color_hex)

    if feature=="lipstick":
        # Use full lips mask for both upper and lower lips
        m = lips_mask(img_bgr.shape,lmd)
        img_mul = blend_multiply(img_bgr,color_bgr,m,alpha=1.0*intensity)  # darker
        img_final = blend_softlight(img_mul,color_bgr,m,alpha=0.15*intensity)
        return img_final

    if feature=="lips":
        m=lips_mask(img_bgr.shape,lmd)
        return tint_hsv_preserve_value(img_bgr,color_bgr,m,alpha=0.80*intensity)

    if feature=="blush":
        m=cheeks_mask(img_bgr.shape,lmd,30)
        return blend_softlight(img_bgr,color_bgr,m,alpha=0.50*intensity)

    if feature=="eyeshadow":
        mL=eyeshadow_mask(img_bgr.shape,lmd,True)
        mR=eyeshadow_mask(img_bgr.shape,lmd,False)
        m=cv2.max(mL,mR)
        return blend_softlight(img_bgr,color_bgr,m,alpha=0.60*intensity)

    if feature=="kohl":
        mL=kohl_mask(img_bgr.shape,lmd,True,base_thickness=2,intensity=intensity)
        mR=kohl_mask(img_bgr.shape,lmd,False,base_thickness=2,intensity=intensity)
        m=cv2.max(mL,mR)
        return blend_normal(img_bgr,color_bgr,m,alpha=0.9*intensity)

    if feature=="mascara":
        m=mascara_mask(img_bgr.shape,lmd,intensity)
        return blend_multiply(img_bgr,color_bgr,m,alpha=0.90*intensity)

    if feature=="foundation":
        m=face_oval_mask(img_bgr.shape,lmd)
        hsv_color = cv2.cvtColor(np.uint8([[color_bgr]]), cv2.COLOR_BGR2HSV)[0,0]
        v = hsv_color[2]
        if v > 180:
            alpha = 0.28 * intensity; brighten = 1.08
        elif 100 < v <= 180:
            alpha = 0.38 * intensity; brighten = 1.02
        else:
            alpha = 0.55 * intensity; brighten = 0.90
        blended = blend_softlight(img_bgr,color_bgr,m,alpha=alpha)
        hsv = cv2.cvtColor(blended,cv2.COLOR_BGR2HSV).astype(np.float32)
        hsv[...,2] = np.clip(hsv[...,2]*brighten,0,255)
        return cv2.cvtColor(hsv.astype(np.uint8),cv2.COLOR_HSV2BGR)

    return img_bgr
