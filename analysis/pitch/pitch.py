import math

def similarity(xs, sq_xs, delta, periods=4):
    """Normalised similarity amonst xs at delta offset"""
    corr = 0
    sq = 0
    start = (len(xs) - delta*(periods+1))//2
    if start < 0:
        start = 0
    end = min(len(xs)-delta,len(xs)-start)
    for i in range(start,end):
        corr += xs[i]*xs[i+delta]
        sq += sq_xs[i] + sq_xs[i+delta]
    return 2*corr/sq, math.sqrt(sq/(end-start))

def get_notes(xs, deltas, periods=4):
    """Gets similarity at each delta, assuming deltas are in descending order"""
    xs = [int(x) for x in xs] #increase bits to avoid overflow
    sq_xs = [x*x for x in xs]
    similarities = []
    power = []
    for delta in deltas:
        s,p = similarity(xs,sq_xs,delta,periods)
        similarities.append(s)
        power.append(p)
    #reduce_harmonics(similarities)
    return similarities, power

# the "notes" are just discrete pitch values to test from 65 to 550Hz
note_names = ["C2", "C#2","D2","D#2","E2","F2","F#2","G2","G#2","A2","Bb2","B2",  "C3","C#3","D3","D#3","E3","F3","F#3","G3","G#3","A3","Bb3","B3",  "C4","C#4","D4","D#4","E4","F4","F#4","G4","G#4","A4","Bb4","B4",  "C5","C#5","Others"]
notes = [65.41,69.3,73.42,77.78,82.41,87.31,92.5,98,103.83,110.0,116.54,123.47,  130.81,138.59,146.83,155.56,164.81,174.61,185.0,196.0,207.65,220.0,233.08,246.94,  261.625,277.1826,293.6684,311.1270,329.6276,349.2282,369.9944,391.9954,415.3047,440.0,466.1638,493.8833,  523.2511,554.3653,  587.3295]

def make_notes(factor=1):
    if factor == 1:
        return notes
    ns = [notes[0]]
    for n in notes[1:]:
        p = ns[-1]
        for i in range(1,factor):
            r = i * 1.0 / factor
            ns.append( p*(1.0-r) + n*r )
        ns.append(n)
    return ns

def get_deltas(frequency, ns):
    return [int(frequency/n) for n in ns]

def reduce_harmonics(similarities):
    # reduce the prior harmonic (one octave back) based on each value
    # and the ones at 1/3rd, 1/4th and 1/6th? indices are: -12, -19, -24, 
    minned = -0.1
    for i in range(len(similarities)-13,-1,-1):
        s = similarities[i]
        if s < minned:
            minned = s
        if s <= 0:
            continue
        si = similarities[i+12]
        if si > 0:
            similarities[i+12] += s/2
        if i < len(similarities)-19:
            si = similarities[i+19]
            if si > 0:
                similarities[i+19] += s/2
            if i < len(similarities)-24:
                si = similarities[i+24]
                if si > 0:
                    similarities[i+24] += s/2
    maxed = 1.0
    for s in similarities:
        if s < minned:
            minned = s
        if s > maxed:
            maxed = s
    maxed /= -minned
    for i,s in enumerate(similarities):
        similarities[i] = s/maxed

