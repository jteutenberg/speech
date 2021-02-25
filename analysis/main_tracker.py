#!/usr/bin/env python3

import pitch.tracker as tracker

import sys
if __name__ == '__main__':
  if len(sys.argv) < 2:
    print("Usage:",sys.argv[0],"<wav file>")
    sys.exit(0)
  track = tracker.PitchTracker(40)
  for t,pitch,power,voicing in track.track(sys.argv[1]):
    print(t,pitch,power,voicing)
