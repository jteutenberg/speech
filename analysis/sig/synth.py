import math

def varying_sinusoid(samples, start_power, end_power, freq_change=0.0):
    """ Brute force construction of a modulated sinusoid"""
    # linear interpolation of power over time
    # linear frequency change optional (shouldn't be too large, e.g. < -0.33 or > 0.33)
    freq_change = max(-0.33, min(0.33, freq_change))

    data = []

    for i in range(samples):
        pos = i*2.0/samples # 0-2 how far through a cycle
        # offset by frequency shift
        power = (start_power*(2-pos) + end_power*pos) / 2
        if freq_change != 0.0:
            # maximum adjustment to pos is when it is halfway (at 1.0)
            d = 0.5 - math.cos(pos*math.pi)/2
            pos += 2*d*freq_change
        data.append( math.cos(pos*math.pi) * power )
    return data

# TODO: could turn instants into pitch periods with start/end power and change in freq to next pitch period
def sinusoid_f0(instants, sampling_rate, min_pitch=60):
  samples = [0 for _ in range(instants[-1][0]+10)]
  prev = (0,0)
  max_length = sampling_rate//min_pitch
  did_prev = False
  last_added = None
  for n,i in enumerate(instants):
    length = i[0] - prev[0]
    if length < max_length:
      freq = length/sampling_rate
      end_freq = freq
      if n < len(instants)-1:
        next_length = instants[n+1][0]-i[0]
        if next_length < max_length:
          end_freq = next_length/sampling_rate
      if length > 0:
        p = varying_sinusoid(length, prev[1], i[1], end_freq/freq-1.0)
        for j,s in enumerate(p):
          samples[j+prev[0]] = s
      if not did_prev:
        # if we didn't synthesise the previous pitch period and this has non-zero power...
        if prev[1] != 0:
          # add a warm-up pitch period.
          p = varying_sinusoid(length, 0, prev[1])
          for j, s in enumerate(p):
            samples[j+prev[0]-length] = s
        if last_added != None and last_added[1] != 0:
          # do the same for the prior pitch period (if any) with a warm-down
          p = varying_sinusoid(length, last_added[1],0)
          for j, s in enumerate(p):
            samples[j+last_added[0]] = s
      last_added = i
      did_prev = True
    else:
      did_prev = False
    prev = i
  return samples


