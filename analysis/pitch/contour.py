import math

class PitchContour:
    def __init__(self, times, pitch, power):
        self.pitch = pitch
        self.power = power
        self.times = times
        self.window_size = (times[-1]-times[0])/len(times)

        # find weighted mode of pitch values
        self.mid_pitch = self.find_mode()
        print(self.mid_pitch," Hz")

        self.drift_pitch, self.drift_power = self.find_drift_modes()
        drift_step = math.floor(0.25/self.window_size) # number of windows per drift value

        # determine strong power level (max peak in distribution?)
        self.high_power = self.find_upper_power()
        print(self.high_power," power")

        # zero low-power pitch entries
        limit = self.high_power/50
        for i, p in enumerate(self.power):
            if p < limit:
                self.pitch[i] = 0
        # and in the drift
        limit = max(self.drift_power)/10
        for i, p in enumerate(self.drift_power):
            if p < limit:
                self.drift_pitch[i] = 0
            elif p > 0:
                # remove any unlikely pitch doubling too
                while p < self.mid_pitch/2:
                    p *= 2
                while p > self.mid_pitch*2:
                    p /= 2

        # interpolate across low-power regions for the drift
        first_pitch = [p for p in self.drift_pitch if p > 0][0]
        last_pitch =  [p for p in self.drift_pitch if p > 0][-1]
        for i, p in enumerate(self.drift_pitch):
            if p == 0:
                self.drift_pitch[i] = first_pitch
            else:
                break
        for i in range(len(self.drift_pitch)-1,0,-1):
            if self.drift_pitch[i] == 0:
                self.drift_pitch[i] = last_pitch
            else:
                break
        for i, p in enumerate(self.drift_pitch):
            if p == 0:
                end = i+1
                while self.drift_pitch[end] == 0:
                    end += 1
                for j in range(i,end):
                    f = (j-i+1) *1.0 / (end-i+1)
                    self.drift_pitch[j] = (1.0-f)*self.drift_pitch[i-1] + f*self.drift_pitch[end]

        # cleanup global pitch halvings and doublings, so everything spans 2 octaves at most
        for i, p in enumerate(self.pitch):
            # apply the global drift to determine the threshold here
            drifted = self.drift_pitch[ max(0,min((i-drift_step//2) // drift_step, len(self.drift_pitch)-1)) ]
            while p > 0 and p < drifted*0.66:
                p *= 2
            while p > drifted*1.5:
                p /= 2
            self.pitch[i] = p

        # clean up local pitch halvings and doublings, and zero any unclear
        for i, p in enumerate(self.pitch):
            if p == 0:
                continue
            # look forward and back to estimate pitch
            estimate, support = self.estimate_local(i)
            if estimate == 0 or support < self.high_power/8: # poor local pitch estimates
                #if self.power[i] < self.high_power/20:
                self.pitch[i] = 0
                continue
            if p/estimate < 0.8:
              while p/estimate < 0.66:
                p *= 2
              self.pitch[i] = p
              #if p/estimate < 0.8: # still far off
              #  self.pitch[i] = 0
            elif p/estimate > 1.25:
              while p/estimate > 1.5:
                p /= 2
              self.pitch[i] = p
              #if p/estimate > 1.25: # too distant
              #  self.pitch[i] = 0

        # TODO a final step: find any remaining doublings/halvings that appear as steps in adjacent pitch (skipping zeroes that will later be spanned by interpolation)
        # for each step up, see if there is a corresponding step down. Adjust a whole segment if this is found.
        steps = []
        prev_pitch = self.pitch[0]
        index = 0
        while index < len(self.pitch):
            # walk forward
            index += 1
            while index < len(self.pitch) and self.pitch[index] == 0:
                index += 1
            # compare the step
            if prev_pitch != 0 and index < len(self.pitch):
                ratio = self.pitch[index] / prev_pitch
                if ratio < 0.66 or ratio > 1.5:
                    steps.append( (index,ratio) )
        # TODO: check the step pairs

        # interpolate through zeroed values
        forward = [0 for _ in self.pitch]
        back = [0 for _ in self.pitch]
        prev = 0
        distance = 0
        for i, p in enumerate(self.pitch):
            if p == 0:
                distance += 1
                forward[i] = (prev,distance)
            else:
                distance = 0
                prev = p
        prev = 0
        distance = 0
        for i in range(len(self.pitch)-1,-1,-1):
            p = self.pitch[i]
            if p == 0:
                distance += 1
                back[i] = (prev,distance)
            else:
                distance = 0
                prev = p
        revisit = []
        for i, p in enumerate(self.pitch):
            if p == 0:
                df = forward[i][1]
                db = back[i][1]
                if df+db > 4:
                    continue
                # no interpolation when close to pitch doubling. Otherwise silly artefacts.
                if forward[i][0]/back[i][0] < 0.66 or forward[i][0]/back[i][0] > 1.5:
                    # TODO: revisit this -- test for double/halve on the adjacent regions
                    #revisit.append(
                    continue
                if forward[i][0] == 0:
                    self.pitch[i] = back[i][0]
                elif back[i][0] == 0:
                    self.pitch[i] = forward[i][0]
                else:
                    self.pitch[i] = (forward[i][0]/df + back[i][0]/db) / (1/df + 1/db)
        # smooth
        # weights: triangular window, convolved with power
        np = self.pitch[0:2]
        for i in range(2,len(self.pitch)-2):
            if self.pitch[i] == 0:
                np.append(0)
                continue
            w = [self.power[i-2], self.power[i-1]*2, self.power[i]*3, self.power[i+1]*2, self.power[i+2]]
            ps = self.pitch[i-2:i+3]
            tw = sum(ws for k,ws in enumerate(w) if ps[k] != 0) # weights for non-zero pitch only
            p = ps[0]*w[0] + ps[1]*w[1] + ps[2]*w[2] + ps[3]*w[3] + ps[4]*w[4]
            np.append(p/tw)
        np.append(self.pitch[-2])
        np.append(self.pitch[-1])
        self.pitch = np

    def get_pitch(self, time):
        return self.pitch[int((time-self.times[0])/self.window_size)]
    
    def get_power(self, time):
        #interpolate between bins
        t = time-self.times[0]
        index = int(t/self.window_size)
        if index >= len(self.power)-1:
            if index == len(self.power)-1:
                return self.power[-1]
            return 0
        fraction = t/self.window_size - index
        return self.power[index]*(1.0-fraction) + self.power[index+1]*fraction

    def estimate_local(self, i):
        """Estimate pitch from 10 neightbouring pitch marks"""
        start = max(0,i-5)
        end = min(len(self.pitch)-1,i+5)
        # power-weighted median
        total_power = 0
        weighted = 0
        # TODO: but we should weigh by power and distance incase of highly varying pitch?
        ps = [(a,b) for a,b in zip(self.pitch[start:end+1],self.power[start:end+1]) if a > 0]
        ps.sort(key=lambda x: x[1]) # sorted by power
        for p in ps:
            total_power += p[1]
        mid_power = total_power/2
        # step through to find
        for p in ps:
            mid_power -= p[1]
            if mid_power <= 0:
                return p[0],total_power
        return ps[-1][0],total_power

    def find_mode(self):
        counts = {}
        for pt,pw in zip(self.pitch,self.power):
            if not pt in counts:
                counts[pt] = pw
            else:
                counts[pt] += pw
        # just pick the single highest bin
        mode = max(counts, key=lambda x: counts[x])
        #bins = [ (p,counts[p]) for p in counts]
        #mode = max(bins, key=lambda x: x[1])
        return mode

    def find_drift_modes(self, window_size=1.0, step=0.25):
        # convert to indices
        window_size = math.floor(window_size/self.window_size)+1
        step = math.floor(step/self.window_size)+1
        # initialise counts
        counts = {}
        power = 0
        for pt,pw in zip(self.pitch[:window_size],self.power[:window_size]):
            if not pt in counts:
                counts[pt] = pw
            else:
                counts[pt] += pw
            power += pw
        modes = [max(counts, key=lambda x: counts[x])]
        powers = [power]
        # step through
        start = 0
        while start+window_size+step < len(self.pitch):
            index = 0
            while index < step:
                # remove
                pw = self.power[start+index]
                counts[ self.pitch[start+index] ] -= pw
                power -= pw
                # and add
                pt = self.pitch[start+index+window_size]
                pw = self.power[start+index+window_size]
                if not pt in counts:
                    counts[pt] = pw
                else:
                    counts[pt] += pw
                power += pw
                index += 1
            modes.append( max(counts, key=lambda x: counts[x]) )
            powers.append(power)
            start += step
        return modes,powers

    def find_upper_power(self):
        spower = [p for p in self.power if p > 0]
        spower.sort()
        return spower[len(spower)-1-len(spower)//20]

    def print_out(self):
        for time, pitch,power in zip(self.times, self.pitch, self.power):
            print(time,pitch,power)
    
    def voiced_regions(self):
        """ Start time, end time,generator across contiguous voiced regions."""
        in_region = False
        start = 0
        for i,p in enumerate(self.pitch):
            if p > 0 and not in_region:
                start = i
                in_region = True
            elif p == 0 and in_region:
                yield self.times[start], self.times[i-1]
                in_region = False
        if in_region:
          yield self.times[start], self.times[-1]

