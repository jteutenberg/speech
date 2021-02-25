#!/usr/bin/env python3

import sys
import pitch.contour as contour
import pitch.tracker as tracker
import glottal.instants as instants
import scipy.io.wavfile as wavfile 

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
  # reload original file
  sampling_rate, data = wavfile.read(sys.argv[1])
  frame_width = 40.0 / sampling_rate
  gis = instants.find_instants(data, cont, sampling_rate, frame_width*2)

  for i in gis:
      print(i[0],i[1])
