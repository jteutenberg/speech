# Turn the graphemes into feature vectors, roughly corresponding to "standard" phonetic properties

# binary features, in order
feature_list = ["Vowel","Voiced","Stop","Fricative","Nasal","Labial","Dental","Alveolar","Postalveolar","Dorsal","Rhotic","Glide","Close","Near close","Mid","Open","Front","Back","Rounded"]

# graphemes per feature
vowel = ["A","E","I","O","AH","OR","EE","UU","ER"]
voiced = vowels + ["B","D","G","V","TH","Z","ZH","M","N","NG","L","R","W"]

stop = ["P","B","T","D","K","G"]
fricative = ["F","V","TH","S","Z","SH","ZH","H"]
nasal = ["M","N","NG"]
labial = ["P","B","F","V","M","W"]
dental = ["TH"]
alveolar = ["T","D","S","Z","N","L"]
postalveolar = ["SH","ZH"]
dorsal = ["K","G","NG","W"]
rhotic = ["R"]
glide = ["W"]

close = ["EE","UU"]
near_close = ["I","W"]
mid = ["E","ER","R"]
near_open = ["A","O","OR"]
opens = ["AH"]

front = ["EE","I","E","A"]
back = ["UU","O","OR","AH"] 
# note: ER is neither front nor back (the sole central vowel in this spec. We're making "u" in "hut" a back AH) 

rounded = ["UU","OR","W"]
