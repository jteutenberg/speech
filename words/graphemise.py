#!/usr/bin/env python3

import re

# Functions to convert a series of English text characters into an ordered
# sequence of canonical graphemes.
# A canonical grapheme is a significant step towards a phoneme, having applied
# most standard English pronunciation rules, normalising homophones, ensuring temporal order etc.

# Functions operate on one of:
# - word: strong of original (or lowercased) text
# - cv tokens: text split into subsequences of consonants and vowels
# - graphemes: sequence of identifiers that roughly map to phonemes

#TODO: K/S with 'c' split digraphs. e.g. "faced" (currently word-final cases are ok)
#     note 'ucu' in 'mucus' vs 'uce' in 'puce'. Exception or rule?

def graphemise_text(text):
  # tokenise into sentences and words, handle various punctuation as breaks
  graphemes = []
  # 1. Split off quotations, flagging start/stop points

  # 2. Find all sentences: ! ? .
  sentences = re.split(r'([?!\.]+)', text)
  #print(sentences)
  for i,s in enumerate(sentences):
    if len(s) <= 1 or s.startswith('.'): # some kind of delimeter
        continue
    final_sentence = i == len(sentences)-1
    # 3. Pauses: ,-; each get their own token
    phrases = re.split(r'([,;])', s) # TODO: hyphenated words need to not be split..
    #print(phrases)
    for j,p in enumerate(phrases):
        if len(p) <= 1 or p.startswith('-'):
            continue
        final_phrase = j == len(phrases)-1
        first = True
        for word in p.split():
          if not first:
            graphemes.append('<WB>')
          first = False
          # pull prefix/suffix off and graphemise separately
          prefix,word,suffix = defix_word(word)
          for pre in prefix:
              graphemes = graphemes + graphemise_prefix(pre,graphemes)
          graphemes = graphemes + graphemise_word(word)
          #print(prefix,word,suffix)
          for suf in suffix:
              graphemes = graphemes + graphemise_suffix(suf,graphemes)
        if not final_phrase:
            graphemes.append(phrases[j+1])
    if not final_sentence:
        graphemes.append(sentences[i+1])

  # separate prefixes and suffixes from words. Including -ies into -ys; -ed to -d; -ility to il it y
  # find the grapheme series
  return graphemes

def defix_word(word):
    suffix = []
    prefix = []
    if word.endswith("es"):
        # check for doubled consonant prior (determine whether to leave an 'e' on the word)???
        if len(word) > 4 and (word[-3] == word[-4] or word[-3] == 'w' or word[-3] == 'h' or word[-3] == 'j' or word[-3] == 'q' or word[-3] == 'v' or word[-3] == 'x'):
            # fusses => fuss + s
            word = word[:-2]
        elif word[-3] == 'i':
            # flies => fly + s
            word = word[:-3]+'y'
        else:
            # fuses => fuse + s
            word = word[:-1]
        suffix.insert(0,'s')
    elif word.endswith("s") and word[-2] != 's': # any non-plurals that end in s and not ss or es?
        word = word[:-1]
        suffix.insert(0,'s')
    if word.endswith("ly") and len(word) > 4: # actually, should have a vowel (so we know it is a whole word)
        word = word[:-2]
        suffix.insert(0,'ly')
    if word.endswith("en") and len(word) > 2 and word[-3] != 'a' and word[-3] != 'e' and word[-3] != 'i' and word[-3] != 'o' and word[-3] != 'u' and word[-3] != 'w' and word[-3] != 'r':
        word = word[:-2]
        suffix.insert(0,'en')
    if word.endswith("er"):
        # later vs latter ? we need to keep the "e" in the first case
        # bower vs bower? Bow / Bowe, could go either way. These consonants cannot be doubled
        if len(word) > 4 and (word[-3] == word[-4] or word[-3] == 'w' or word[-3] == 'h' or word[-3] == 'j' or word[-3] == 'q' or word[-3] == 'v' or word[-3] == 'x'):
            word = word[:-2]
        elif len(word) > 4 and word[-3] == 'i':
            word = word[-3] + 'y'
        else:
            word = word[:-1]
        suffix.insert(0,'er')
    if word.endswith("ed") and len(word) > 2 and word[-3] != 'a' and word[-3] != 'e' and word[-3] != 'i' and word[-3] != 'o' and word[-3] != 'u' and word[-3] != 'w' and word[-3] != 'r':
        if word.endswith("ered"):
          word = word[:-4]
          suffix.insert('d')
          suffix.insert('er')
        elif word.endswith("ened"):
          word = word[:-4]
          suffix.insert('d')
          suffix.insert('en')
        else:
          word = word[:-2]
          suffix.insert(0,'ed')
    # then prefixes
    if word.startswith("re") and len(word) > 4:
        prefix.append('re')
        word = word[2:]
    if word.startswith("de") and len(word) > 4 and word[2] != 'a' and word[2] != 'e' and word[2] != 'i' and word[2] != 'o' and word[2] != 'u':
        prefix.append('de')
        word = word[2:]
    if word.startswith("pre") and len(word) > 5 and word[3] != 'a' and word[3] != 'e' and word[3] != 'i' and word[3] != 'o' and word[3] != 'u':
        prefix.append('pre')
        word = word[3:]
    return prefix,word,suffix

def graphemise_prefix(prefix, word_graphemes):
    # TODO: anti-, dis-, pro-
    if prefix == 'pre':
      return ['P','R','EE']
    if prefix == 're':
      return ['R','EE']
    if prefix == 'de':
      return ['D','EE']
    return []

def graphemise_suffix(suffix, word_graphemes):
    if suffix == "s":
        if word_graphemes[-1] == 'S' or word_graphemes[-1] == 'Z':
            return ["I","Z"]
        return ["S"] # voicing here depends on voicing of the prior grapheme. TODO: do it here?
    elif suffix == 'ly':
        return ["L","EE"]
    elif suffix == 'er':
        return ["ER","R"]
    elif suffix == 'en':
        return ["E","N"]
    elif suffix == 'ed':
        return ["E","D"]
    elif suffix == 'd':
        return ["D"]
    return []

def graphemise_word(word):
  """Converts a string of characters representing one word into ordered graphemes"""
  tokens,vowels = split_cv(word) # tokens are runs of characters: either all vowel or all consonant

  # search for rhotic modifiers. These modify the last vowel token
  rhotics = [i < len(tokens)-1 and vowels[i] and tokens[i+1][0] == 'r' for i in range(len(tokens))]

  # treat following 'w' as a rounded modifier
  rounded = [i < len(tokens)-1 and vowels[i] and tokens[i+1][0] == 'w' for i in range(len(tokens))]

  # first convert consonant tokens to graphemes

  separates = [False for _ in tokens]
  for i,token in enumerate(tokens):
    if not vowels[i]:
      next_vowel = ''
      if i < len(tokens)-1:
        next_vowel = tokens[i+1][0]
        if i < len(tokens)-1 and (tokens[i+1] == 'io' or tokens[i+1] == 'ia'):
            next_vowel = tokens[i+1]
      tokens[i],separates[i] = graphemise_consonants(token, i == 0, i == len(tokens)-1,next_vowel)
  
  # assign split digraphs: vowels separated by a 1-length consonant.
  # these modifiers apply to the first vowel token
  split_digraphs = [i < len(tokens)-2 and vowels[i] and not separates[i+1] and vowels[i+2] for i in range(len(tokens))]

  # then prepare any vowel graphemes and collate them

  graphemes = []
  for i,token in enumerate(tokens):
      if vowels[i]:
          graphemes = graphemes + graphemise_vowels(token,split_digraphs[i],rhotics[i],rounded[i],i == len(vowels)-1)
          # special case, where trailing 'E' is the only vowel. Prevent dropping it.
          if len(tokens) == 2 and i == 1 and token == 'e':
              graphemes.append('EE')
      else:
          graphemes = graphemes + tokens[i] # the consonants
  return graphemes

def graphemise_vowels(token, split_digraphed=False,rhotic=False,rounded=False,final=False):
    """ The sausage factory of low level rules"""
    if token == "igh":
        return ["AH","EE"] # ignores split digraphs and rhotics
    
    # trailing 'e' at the end of a word are ignored. Usually have been added for split digraphs
    if final and len(token) == 1 and token[0] == 'e':
        return []
    
    graphemes = []
    if split_digraphed and len(token) == 1:
        # modify the first vowel token and add it in
        if token[0] == 'a':
            graphemes.append('A')
            graphemes.append('EE') # ay
        elif token[0] == 'e':
            graphemes.append('EE')
        elif token[0] == 'i':
            graphemes.append('AH')
            graphemes.append('EE') #ai
        elif token[0] == 'o':
            graphemes.append('O')
            graphemes.append('UU')
        elif token[0] == 'u':
            graphemes.append('EE') # was Y
            graphemes.append('UU')
        elif token[0] == 'y':
            graphemes.append('AH')
            graphemes.append('EE') #ai
        #token = token[1:]
        return graphemes
    # run up to the end 
    i = 0
    vowel_count = 0
    while i < len(token):
        # find any regular digraphs
        if i < len(token)-1:
            c = token[i]
            nc = token[i+1]
            # peek
            if c == 'a':
                if nc == 'a':
                    graphemes.append('AH')
                    i += 2
                elif nc == 'e':
                    graphemes.append('A')
                    graphemes.append('EE') #ay
                    i += 2
                elif nc == 'i':
                    graphemes.append('A')
                    graphemes.append('EE') #ay
                    i += 2
                elif nc == 'o':
                    graphemes.append('AH')
                    graphemes.append('UU') #au
                    i += 2
                elif nc == 'u':
                    graphemes.append('OR')
                    i += 2
                vowel_count += 1
            elif c == 'e':
                if nc == 'a' or nc == 'e':
                    graphemes.append('EE')
                    i += 2
                elif nc == 'i':
                    graphemes.append('A')
                    graphemes.append('EE') #ay
                    i += 2
                elif nc == 'o':
                    graphemes.append('E')
                    graphemes.append('O')
                    graphemes.append('UU')
                    i += 2
                elif nc == 'u':
                    graphemes.append('EE')
                    graphemes.append('UU')
                    i += 2
                vowel_count += 1
            elif c == 'i':
                if nc == 'a':
                    graphemes.append('AH') #e.g. liar
                    graphemes.append('EE')
                    graphemes.append('AH')
                    i += 2
                elif nc == 'e':
                    graphemes.append('EE')
                elif nc == 'i':
                    graphemes.append('EE')
                    i += 2
                elif nc == 'u':
                    graphemes.append('EE')
                    i += 1
                vowel_count += 1
            elif c == 'o':
                if nc == 'a' or nc == 'e': 
                    graphemes.append('O')
                    graphemes.append('UU')
                    i += 2
                elif nc == 'i':
                    graphemes.append('OR')
                    graphemes.append('EE')
                    i += 2
                elif nc == 'o':
                    graphemes.append('UU')
                    i += 2
                elif nc == 'u':
                    # TODO: words like "should" don't have the AH. 
                    # but "ouch" does. What's the rule? Probably the 'L'. 
                    # found, 
                    # touch?? <- neither fits. In this case UU is dropped
                    # so.. leave it for pronunciation to choose one to drop
                    graphemes.append('AH')
                    graphemes.append('UU') #au
                    i += 2
                vowel_count += 1
            elif c == 'u':
                if nc == 'e':
                    graphemes.append('EE')
                    graphemes.append('UU')
                    i += 2
                elif nc == 'i':
                    graphemes.append('W')
                    i += 1
                elif nc == 'o' or nc == 'u':
                    graphemes.append('UU')
                    i += 1
                vowel_count += 1
        if i >= len(token):
            break

        c = token[i]

        # if we're at the end apply a rhotic if necessary
        if rhotic and i == len(token)-1:
            if c == 'a':
                graphemes.append('AH')
            elif c == 'e' or c == 'i' or c == 'u' or c == 'y':
                graphemes.append('ER')
            elif c == 'o':
                graphemes.append('OR')
            return graphemes
        # or a lip rounding
        if rounded and i == len(token)-1:
            if c == 'a':
                graphemes.append('OR')
            elif c == 'e':
                graphemes.append('EE')
            elif c == 'i':
                graphemes.append('I') # no change
            elif c == 'o':
                graphemes.append('AH')
            elif c == 'u':
                graphemes.append('UU') # examples? Huw?
            elif c == 'y':
                graphemes.append('EE') # ? 
            return graphemes

        # otherwise, just a regular vowel grapheme
        if c == 'a':
            graphemes.append('A')
            vowel_count += 1
        elif c == 'e':
            graphemes.append('E')
            vowel_count += 1
        elif c == 'i':
            graphemes.append('I')
            vowel_count += 1
        elif c == 'o':
            graphemes.append('O')
            vowel_count += 1
        elif c == 'u':
            graphemes.append('AH')
            vowel_count += 1
        elif c == 'y':
            # y at the beginning is a liquid, otherwise a long EE
            if i == 0 and len(token) > 1:
                graphemes.append('EE') # merge Y and EE
            else:
                # we have two choices: e.g. dowry vs wry. Polly vs Ply. <- if no vowels, go with AH EE
                if vowel_count == 0:
                    graphemes.append('AH')
                graphemes.append('EE')
            vowel_count += 1
        i += 1

    return graphemes

def graphemise_consonants(token,initial=False,final=False, next_vowel=''):
    #  TODO: consonant modified by: tion, cion(?), sion, tian, sure (SH,SH,ZH non-initial,T+SH non-initial, SH/ZH non-initial)
    graphemes = []
    i = 0
    separates = False # whether this separates vowels, preventing split digraphs 
    while i < len(token):
        # find any regular digraphs
        if i < len(token)-1:
            c = token[i]
            nc = token[i+1]
            if c == 's' and nc == 'h':
                graphemes.append('SH')
                i += 2
            elif c == 'c' and nc == 'h':
                graphemes.append('T')
                graphemes.append('SH')
                i += 2
            elif c == 't' and nc == 'h':
                graphemes.append('TH')
                i += 2
            elif c == 'z' and nc == 'h':
                graphemes.append('ZH') # voiced SH
                i += 2
            elif c == 'n' and nc == 'g':
                graphemes.append('NG')
                i += 2
            elif c == 'p' and nc == 'h':
                graphemes.append('F')
                i += 2
            elif c == 's' and nc == 's':
                graphemes.append('S')
                i += 2
            elif c == 'c' and nc == 'k':
                i += 1 # just skip the c
            elif c == 'k' and nc == 'n':
                i += 1 # silent k
            elif initial  and c == 'g' and nc == 'n':
                i += 1 # silent g
            elif initial and c == 'p' and nc == 's':
                i += 1 # silent p
            elif i == len(token)-2 and c == 'n' and nc == 'c':
                graphemes.append('N')
                graphemes.append('S')
                i += 2
            elif i == len(token)-2 and c == 'c' and nc == 'c':
                graphemes.append('K')
                graphemes.append('S')
                i += 2
            elif c == nc:
                # collapse any doublings
                i += 1
                separates = True
        if i >= len(token):
            return graphemes,separates or len(graphemes) > 1
        c = token[i]
        if c == 's' and (next_vowel == 'io' or next_vowel == 'ia'):
            if i == 0:
                graphemes.append('ZH') # e.g. fusion. But what about motion? Just 'u'?
            else:
                graphemes.append('SH') # e.g. tension
        elif c == 's' and not initial and len(token) == 1:
            graphemes.append('Z')
        elif c == 'q':
            graphemes.append('K')
            graphemes.append('W')
        elif c == 'x':
            graphemes.append('K')
            graphemes.append('S')
        elif c == 'c':
            if ((not initial) and (not final) and len(token) == 1) or (initial and (next_vowel == 'e' or next_vowel == 'i' or next_vowel == 'y' or next_vowel == 'io')):
                # initial 'c' => S only when followed by 'e' or 'y'
                graphemes.append('S')
            else:
                graphemes.append('K')
        elif c == 't' and (next_vowel == 'io' or next_vowel == 'ia'):
            graphemes.append('SH')
        else:
            graphemes.append( token[i].upper() )
        i += 1

    return graphemes,separates or len(graphemes) > 1


def is_vowel_char(c):
  return c == 'a' or c == 'e' or c == 'i' or c == 'o' or c == 'u' or c == 'y'

def split_cv(word):
    """Tokenises into runs of consonant or vowel characters"""
    word = word.lower()
    tokens = []
    voweled = []
    consonant = not is_vowel_char(word[0])
    start = 0
    end = 1
    while end < len(word):
      c = word[end]
      # test for an extension
      next_consonant = not is_vowel_char(c)
      if next_consonant != consonant:
          # a token has ended
          tokens.append( word[start:end] )
          voweled.append( not consonant )
          consonant = next_consonant
          start = end
      end += 1 # move to next character
      # special case: igh is a vowel sequence
      if c == 'i' and end < len(word)-1 and word[end] == 'g' and word[end+1] == 'h':
          end += 2
      if end == start+1 and word[start] == 'q' and word[end] == 'u':
          end += 1 # just clobber the consumed 'u'
    if end > start:
        # add the final token
        tokens.append( word[start:end] )
        voweled.append( not consonant )
    return tokens, voweled


if __name__ == '__main__':
    import sys
    words = sys.argv[1:]
    for word in words:
        print(graphemise_text(word))
