#!/usr/bin/env python3

import pitch.tracker as tracker
import pitch.contour as contour
import sys

if __name__ == '__main__':
  if len(sys.argv) < 2:
    print("Usage:",sys.argv[0],"<wav file>")
    sys.exit(0)
  track = tracker.PitchTracker(40)
  times = []
  pitches = []
  powers = []
  for t,pitch,power,voicing in track.track(sys.argv[1]):
    times.append(t)
    pitches.append(pitch)
    powers.append(power)
  cont = contour.PitchContour(times, pitches, powers)
  cont.print_out()
