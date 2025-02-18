#!/usr/bin/env python3
import argparse
import cv2
import numpy as np
import os
import time

from path_for_colab.keras_centernet.models.networks.hourglass import HourglassNetwork, normalize_image
from path_for_colab.keras_centernet.models.decode import CtDetDecode
from path_for_colab.keras_centernet.utils.utils import COCODrawer
from path_for_colab.keras_centernet.utils.letterbox import LetterboxTransformer


def main():
  parser = argparse.ArgumentParser()
  parser.add_argument('--video', default='webcam', type=str)
  parser.add_argument('--output', default='output', type=str)
  parser.add_argument('--inres', default='512,512', type=str)
  parser.add_argument('--outres', default='1080,1920', type=str)
  parser.add_argument('--max-frames', default=1000000, type=int)
  parser.add_argument('--fps', default=25.0 * 1.0, type=float)
  args, _ = parser.parse_known_args()
  args.inres = tuple(int(x) for x in args.inres.split(','))
  args.outres = tuple(int(x) for x in args.outres.split(','))
  os.makedirs(args.output, exist_ok=True)
  kwargs = {
    'num_stacks': 2,
    'cnv_dim': 256,
    'weights': 'ctdet_coco',
    'inres': args.inres,
  }
  heads = {
    'hm': 80,  # 3
    'reg': 2,  # 4
    'wh': 2  # 5
  }
  model = HourglassNetwork(heads=heads, **kwargs)
  model = CtDetDecode(model)
  drawer = COCODrawer()
  letterbox_transformer = LetterboxTransformer(args.inres[0], args.inres[1])
  cap = cv2.VideoCapture(0 if args.video == 'webcam' else args.video)
  out_fn = os.path.join(args.output, 'ctdet.' + os.path.basename(args.video)).replace('.mp4', '.avi')
  fourcc = cv2.VideoWriter_fourcc(*'XVID')
  
  #재생할 파일의 넓이 얻기
  width = cap.get(cv2.CAP_PROP_FRAME_WIDTH)
  #재생할 파일의 높이 얻기
  height = cap.get(cv2.CAP_PROP_FRAME_HEIGHT)
  #재생할 파일의 프레임 레이트 얻기
  fps = cap.get(cv2.CAP_PROP_FPS)

  out = cv2.VideoWriter(out_fn, fourcc, fps, (int(width), int(height)))
  
  # out = cv2.VideoWriter(out_fn, fourcc, args.fps, args.outres[::-1])
  
  k = 0
  tic = time.time()
  while cap.isOpened():
    if k > args.max_frames:
      print("Bye")
      break
    if k > 0 and k % 100 == 0:
      toc = time.time()
      duration = toc - tic
      print("[%05d]: %.3f seconds / 100 iterations" % (k, duration))
      tic = toc

    k += 1
    ret, img = cap.read()
    if not ret:
      print("Done")
      break
    pimg = letterbox_transformer(img)d
    pimg = normalize_image(pimg)
    pimg = np.expand_dims(pimg, 0)
    detections = model.predict(pimg)[0]
    for d in detections:
      x1, y1, x2, y2, score, cl = d
      if score < 0.3:
        break
      x1, y1, x2, y2 = letterbox_transformer.correct_box(x1, y1, x2, y2)
      img = drawer.draw_box(img, x1, y1, x2, y2, cl)

    out.write(img)
  print("Video saved to: %s" % out_fn)


if __name__ == '__main__':
  main()
