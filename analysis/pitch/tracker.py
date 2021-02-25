import pitch.pitch as anp
import numpy as np
import math
import scipy.io.wavfile as wavfile 

class PitchTracker:
  def __init__(self, analysis_frequency):
    self.analysis_frequency = analysis_frequency
    self.sampling_rate = 0

  def setup(self,sampling_rate, note_factor=1):
    if sampling_rate == self.sampling_rate:
        return
    self.notes = anp.make_notes(note_factor)
    self.deltas = anp.get_deltas(sampling_rate,self.notes)
    self.sampling_rate = sampling_rate
    self.step_size = math.ceil(sampling_rate/self.analysis_frequency)
    self.window_size = sampling_rate//5 # want to capture as low as 60Hz, over 6 pitch periods

  def analyse_frame(self,xs):
    """Given a frame of raw numbers, find approximate pitch and power"""
    ns,power = anp.get_notes(xs,self.deltas,6) # use 6 pitch periods
    # TODO: estimate the voicing based on similarity
    # just take the best note
    best = max(enumerate(ns),key=lambda x:x[1])[0]
    if best >= len(self.notes)-1:
        # too high. Basically no pitch present.
        return 0,power[-1]
    return self.notes[best], power[best]

  def track(self,filename):
    """ Produce a time/pitch/power track from a mono wav file """
    offset = 0
    sampling_rate, data = wavfile.read(filename)
    self.setup(sampling_rate,1)
    while offset + self.window_size < len(data):
      frame = data[offset:offset+self.window_size]
      pitch,power = self.analyse_frame(frame)
      # update the power based on three pitch periods from the centre
      if pitch == 0:
          centre_size = len(frame) // 5 # a small local region
      else:
          centre_size = int(min(len(frame),(3*self.sampling_rate)//pitch))
      if centre_size == 0:
          power = 0
      else:
          centre = frame[(len(frame)-centre_size)//2 : (len(frame)+centre_size)//2]
          power = sum(abs(x) for x in centre) / centre_size
      yield float(offset+self.window_size/2)/self.sampling_rate, pitch, power, 0
      offset += self.step_size

# TODO: guess strong/weak/no voicing boundaries
# post-polishing: minimise octave-jumping through strongly voiced segments
# prefer lower octaves through weak voiced regions

