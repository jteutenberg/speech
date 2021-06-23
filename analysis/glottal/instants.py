import numpy as np
import math

# this is the home for functions taking a speech signal and its cleaned pitch contour then returning glottal closure (or opening?) instants as time/power pairs.

def find_instants(signal, contour, sampling_rate,frame_width=0.1):
    instants = []
    for start, end in contour.voiced_regions():
        print(start,end, int(start*sampling_rate),int(end*sampling_rate))
        # these are indices in the contour: convert to times
        next_instants = find_voiced_instants(signal, contour, max(0,start-frame_width), end+frame_width, sampling_rate)
        # add an artificial zero-power instant at either end of the segment
        if len(next_instants) > 1:
            instants.append( (2*next_instants[0][0] - next_instants[1][0],0) )
        instants += next_instants
        if len(next_instants) > 1:
            instants.append( (2*next_instants[-1][0] - next_instants[-2][0],0) )
    return instants

def find_weighted_median(crossings):
    crossings.sort(key=lambda x: x[0]) # sort by pitch
    # don't take centre, take weighted centre
    ws = sum(x[1] for x in crossings)
    count = 0
    for c in crossings:
        count += c[1]
        if count > ws/2:
            return c[0]
    return crossings[-1][0]

def zfr(signal, pitch, sampling_rate):
    """ Finds a set of good instants expected to lie near the range earliest to latest"""
    # 1. take delta giving x(n)
    xs = [int(signal[i]-signal[i-1]) for i in range(1,len(signal))]
    ym1 = xs[1]
    ym2 = xs[0]

    for i,x in enumerate(xs):
        if i < 2:
            continue
        # 2. y1(n) = x(n) + 2y1(n-1) - y1(n-2)
        y = x + 2*ym1 - ym2
        ym2 = ym1
        ym1 = y
        xs[i] = y
    ym1 = xs[1]
    ym2 = xs[0]
    for i,x in enumerate(xs):
        if i < 2:
            continue
        # 3. y2(n) = y1(n) + 2y2(n-1) - y2(n-2) <- repeat of (2)
        y = x + 2*ym1 - ym2
        ym2 = ym1
        ym1 = y
        xs[i] = y
    # 4. remove mean: y(n) = y2(n) - sliding average(y2). Window size = 1.5*average contour pitch
    window_size = int(1.5 * sampling_rate / pitch)
    half_window = window_size // 2
    for n in range(2):
      s = sum( xs[:window_size] )
      filtered = [x for x in xs]
      for i in range(half_window,len(xs)+half_window):
        filtered[i-half_window] -= s/window_size
        if i >= window_size and i < len(xs):
            s += xs[i] - xs[i-window_size]
      xs = filtered
    return xs

def find_voiced_instants(signal, contour, start, end, sampling_rate):
    """ Find voiced instants from contour's voiced regions"""
    # extract sub-signal
    start_index = math.floor(start * sampling_rate+0.5)
    end_index = math.floor(end * sampling_rate+0.5)
    sub_signal = signal[start_index:end_index+1]

    # convert to ZFR using local pitch
    #print("local pitch:", contour.get_pitch( (end+start)/2 )," for voiced region at",(end+start)/2,"also:",contour.get_pitch(start),"-",contour.get_pitch(end))
    z = zfr(sub_signal, contour.get_pitch( (end+start)/2 ),sampling_rate)
    #print("Voiced region from ",start,"to",end," or ",start_index,"to",end_index)

    # select rising zero crossings: candidate list. Pair with power from the contour.
    crossings = [(i,contour.get_power(start + i/sampling_rate)) for i,x in enumerate(z) if i > 0 and x >= 0 and z[i-1] < 0]
    
    #print("Found ",len(crossings)," zero crossings, or ",len(crossings)/(end-start) ,"Hz sampling rate of ",sampling_rate)
    if len(crossings) < 2:
        return crossings
    # final test for pitch doublings: 5-width power-weighted median octave filter
    prev_length = crossings[1][0] - crossings[0][0]
    prev_cross = crossings[1]
    i = 2
    while i < len(crossings):
        cross = crossings[i]
        length = cross[0] - prev_cross[0]
        # is it mismatched with prior?
        if prev_length > length*1.5 or prev_length*1.5 < length:
            # NOTE: this means i-2:i-1 is different from i-1:i
            # Test both directions around i-1 and decide which values need removing (never add)
            win_start = max(0,i-3)
            win_end = min(len(crossings),i+3)
            # find weighted median pitch period
            candidates = [ (crossings[k][0]-crossings[k-1][0],(crossings[k-1][1]+crossings[k][1])/2) for k in range(win_start,win_end) if crossings[k][0] > crossings[k-1][0]]
            w_median = find_weighted_median(candidates)
            # select the merge side that results in a value closest to the median:
            #  either i-2:i-1 with i-1:i  or i-1:i with i:i+1
            if i < 2:
                w1 = 0
            else:
                w1 = abs( w_median - (crossings[i][0] - crossings[i-2][0]) )
            if i > len(crossings)-2:
                w2 = 0
            else:
                w2 = abs( w_median - (crossings[i+1][0] - crossings[i-1][0]) )
            if w1 < w_median//2 or w2 < w_median//2:
              if w1 <=  w2: # merge into w1
                crossings = crossings[:i-1]+crossings[i:]
              else:
                crossings = crossings[:i]+crossings[i+1:]
              if i < len(crossings):
                length = crossings[i][0] - crossings[i-1][0]
                cross = crossings[i]
            elif length > w_median * 1.66: # needs to be a pretty clear pitch halving
                if length > w_median * 2.5: # thirding?!
                  crossings = crossings[:i] + [ ( (crossings[i-1][0]*2+crossings[i][0])//3, (crossings[i-1][1]*2+crossings[i][1])/3), ((crossings[i-1][0]+2*crossings[i][0])//3, (crossings[i-1][1]+2*crossings[i][1])/3) ] + crossings[i:]
                  
                else:
                  # consider an extra artificial instant
                  crossings = crossings[:i] + [ ( (crossings[i-1][0]+crossings[i][0])//2, (crossings[i-1][1]+crossings[i][1])/2) ] + crossings[i:]
                length = crossings[i][0] - crossings[i-1][0]
                cross = crossings[i]
        i += 1
        prev_cross = cross
        prev_length = length
    # finally, in original signal-space, shift each crossing to one of two adjacent upward crossings
    temporal_crossings = []
    #all_cs = []
    for c in crossings:
        if c[1] == 0:
            continue
        pos = c[0]+start_index
        if signal[pos-1] < 0 and signal[pos+1] > 0:
            temporal_crossings.append( (pos, c[1]) )
        else:
          next_pos = pos+1
          while next_pos < len(signal)-1 and (signal[next_pos-1] > 0 or signal[next_pos+1] < 0):
              next_pos += 1
          prior_pos = pos-1
          while prior_pos > 0 and (signal[prior_pos-1] > 0 or signal[prior_pos+1] < 0):
              prior_pos -= 1
          if prior_pos < pos-100:
              if next_pos > pos+100:
                temporal_crossings.append( (pos, c[1]) )
              else:
                temporal_crossings.append( (next_pos, c[1]) )
          elif next_pos > pos+100:
            temporal_crossings.append( (prior_pos, c[1]) )
          else:
            temporal_crossings.append( (prior_pos, next_pos, c[1]) )
          #all_cs.append( (prior_pos, c[1]) )
          #all_cs.append( (next_pos, c[1]) )
          #print(prior_pos,next_pos)
    return select_marks(temporal_crossings)
    #return [(c[0] + start_index, c[1]) for c in crossings if c[1] != 0]

# two dynamic programming functions for best pitch and best pitch marks. Both optimise for smoothness.

def select_marks(choices):
  # choices are lists/tuples of pitch marks and a final power value
  # a state is an index in choices, the selected pitch mark, a cost, and previous state
  states = [None]# (0,p,0,None) for p in choices[0][:-1] ]
  for i,cs in enumerate(choices[1:]):
      next_states = []
      for mark in cs[:-1]:
          if i < 2: # first two have no cost, so put in all combinations
              for s in states:
                  next_states.append( (i,mark,0,s) )
          else:
            best_prior = None
            best_cost = -1
            for s in states:
              # cost is change in pitch period
              delta = (s[1] - s[3][1]) - (mark - s[1])
              cost = delta*delta + s[2]
              if best_prior == None or cost < best_cost:
                  best_cost = cost
                  best_prior = s
            next_states.append( (i, mark, best_cost, best_prior) )
      states = next_states
  # find the best final state and extract choices
  end_state = min(states, key=lambda s: s[2])
  best = []
  while end_state != None:
      best.append( (end_state[1], choices[end_state[0]][-1]) )
      end_state = end_state[3] # prev
  return best[::-1] # reverse
