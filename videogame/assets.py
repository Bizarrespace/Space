

import os
import pygame

main_dir = os.path.split(os.path.abspath(__file__))[0]
data_dir = os.path.join(main_dir, "data")

asset_dict = {
  'soundtrack': '8bp051-06-random-happy_ending_after_all.mp3',
  'soundfx': 'Pillsbury.aif',
}

def get(key):
  value = asset_dict.get(key, None)
  assert value
  if value:
    value = os.path.join(data_dir, value)
  return value


