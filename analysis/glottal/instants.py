import numpy as np
import math

# this is the home for functions taking a speech signal and its cleaned pitch contour then returning glottal closure (or opening?) instants as time/power pairs.

def find_instants(signal, contour, sampling_rate,frame_width=0.1):
    instants = []
    for start, end in contour.voiced_regions():
        print(start,end, int(start*sampling_rate),int(end*sampling_rate))
        # these are indices in the contour: convert to times
        instants += find_voiced_instants(signal, contour, max(0,start-frame_width), end+frame_width, sampling_rate)
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
    for i,cross in enumerate(crossings):
        if i < 2:
          prev_cross = cross
          continue
        length = cross[0] - prev_cross[0]
        # is t mismatched with prior?
        if prev_length > length*1.5 or prev_length*1.5 < length:
            # Test both directions and decide which values need removing (never add)
            win_start = max(0,i-3)
            win_end = min(len(crossings),i+4)
            # find weighted median pitch period
            candidates = [ (crossings[k][0]-crossings[k-1][0],(crossings[k-1][1]+crossings[k][1])/2) for k in range(win_start,win_end) if crossings[k][0] > crossings[k-1][0]]
            w_median = find_weighted_median(candidates)
            # if any two adjacent pitch periods are below median/1.5, merge them
            for k in range(win_start+1,win_end):
                if crossings[k][0] - crossings[k-1][0] < w_median/1.5 and crossings[k-1][0] - crossings[k-2][0] < w_median/1.5:
                    crossings[k] = (crossings[k][0],max(crossings[k][1],crossings[k-1][1]))
                    crossings[k-1] = (0,0)
                    break
        prev_cross = cross
        prev_length = length
    return [(c[0] + start_index, c[1]) for c in crossings if c[1] != 0]

