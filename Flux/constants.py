
FEATURE_DESCRIPTIONS = {
  'aalt': "Access All Alternates",
  'abvf': "Above-base Forms",
  'abvm': "Above-base Mark Positioning",
  'abvs': "Above-base Substitutions",
  'afrc': "Alternative Fractions",
  'akhn': "Akhands",
  'blwf': "Below-base Forms",
  'blwm': "Below-base Mark Positioning",
  'blws': "Below-base Substitutions",
  'calt': "Contextual Alternates",
  'case': "Case-Sensitive Forms",
  'ccmp': "Glyph Composition / Decomposition",
  'cfar': "Conjunct Form After Ro",
  'chws': "Contextual Half-width Spacing",
  'cjct': "Conjunct Forms",
  'clig': "Contextual Ligatures",
  'cpct': "Centered CJK Punctuation",
  'cpsp': "Capital Spacing",
  'cswh': "Contextual Swash",
  'curs': "Cursive Positioning",
  'c2pc': "Petite Capitals From Capitals",
  'c2sc': "Small Capitals From Capitals",
  'dist': "Distances",
  'dlig': "Discretionary Ligatures",
  'dnom': "Denominators",
  'dtls': "Dotless Forms",
  'expt': "Expert Forms",
  'falt': "Final Glyph on Line Alternates",
  'fin2': "Terminal Forms #2",
  'fin3': "Terminal Forms #3",
  'fina': "Terminal Forms",
  'flac': "Flattened accent forms",
  'frac': "Fractions",
  'fwid': "Full Widths",
  'half': "Half Forms",
  'haln': "Halant Forms",
  'halt': "Alternate Half Widths",
  'hist': "Historical Forms",
  'hkna': "Horizontal Kana Alternates",
  'hlig': "Historical Ligatures",
  'hngl': "Hangul",
  'hojo': "Hojo Kanji Forms (JIS X 0212-1990 Kanji Forms)",
  'hwid': "Half Widths",
  'init': "Initial Forms",
  'isol': "Isolated Forms",
  'ital': "Italics",
  'jalt': "Justification Alternates",
  'jp78': "JIS78 Forms",
  'jp83': "JIS83 Forms",
  'jp90': "JIS90 Forms",
  'jp04': "JIS2004 Forms",
  'kern': "Kerning",
  'lfbd': "Left Bounds",
  'liga': "Standard Ligatures",
  'ljmo': "Leading Jamo Forms",
  'lnum': "Lining Figures",
  'locl': "Localized Forms",
  'ltra': "Left-to-right alternates",
  'ltrm': "Left-to-right mirrored forms",
  'mark': "Mark Positioning",
  'med2': "Medial Forms #2",
  'medi': "Medial Forms",
  'mgrk': "Mathematical Greek",
  'mkmk': "Mark to Mark Positioning",
  'mset': "Mark Positioning via Substitution",
  'nalt': "Alternate Annotation Forms",
  'nlck': "NLC Kanji Forms",
  'nukt': "Nukta Forms",
  'numr': "Numerators",
  'onum': "Oldstyle Figures",
  'opbd': "Optical Bounds",
  'ordn': "Ordinals",
  'ornm': "Ornaments",
  'palt': "Proportional Alternate Widths",
  'pcap': "Petite Capitals",
  'pkna': "Proportional Kana",
  'pnum': "Proportional Figures",
  'pref': "Pre-Base Forms",
  'pres': "Pre-base Substitutions",
  'pstf': "Post-base Forms",
  'psts': "Post-base Substitutions",
  'pwid': "Proportional Widths",
  'qwid': "Quarter Widths",
  'rand': "Randomize",
  'rclt': "Required Contextual Alternates",
  'rkrf': "Rakar Forms",
  'rlig': "Required Ligatures",
  'rphf': "Reph Forms",
  'rtbd': "Right Bounds",
  'rtla': "Right-to-left alternates",
  'rtlm': "Right-to-left mirrored forms",
  'ruby': "Ruby Notation Forms",
  'rvrn': "Required Variation Alternates",
  'salt': "Stylistic Alternates",
  'sinf': "Scientific Inferiors",
  'size': "Optical size",
  'smcp': "Small Capitals",
  'smpl': "Simplified Forms",
  'ss01': "Stylistic Set 1",
  'ss02': "Stylistic Set 2",
  'ss03': "Stylistic Set 3",
  'ss04': "Stylistic Set 4",
  'ss05': "Stylistic Set 5",
  'ss06': "Stylistic Set 6",
  'ss07': "Stylistic Set 7",
  'ss08': "Stylistic Set 8",
  'ss09': "Stylistic Set 9",
  'ss10': "Stylistic Set 10",
  'ss11': "Stylistic Set 11",
  'ss12': "Stylistic Set 12",
  'ss13': "Stylistic Set 13",
  'ss14': "Stylistic Set 14",
  'ss15': "Stylistic Set 15",
  'ss16': "Stylistic Set 16",
  'ss17': "Stylistic Set 17",
  'ss18': "Stylistic Set 18",
  'ss19': "Stylistic Set 19",
  'ss20': "Stylistic Set 20",
  'ssty': "Math script style alternates",
  'stch': "Stretching Glyph Decomposition",
  'subs': "Subscript",
  'sups': "Superscript",
  'swsh': "Swash",
  'titl': "Titling",
  'tjmo': "Trailing Jamo Forms",
  'tnam': "Traditional Name Forms",
  'tnum': "Tabular Figures",
  'trad': "Traditional Forms",
  'twid': "Third Widths",
  'unic': "Unicase",
  'valt': "Alternate Vertical Metrics",
  'vatu': "Vattu Variants",
  'vchw': "Vertical Contextual Half-width Spacing",
  'vert': "Vertical Writing",
  'vhal': "Alternate Vertical Half Metrics",
  'vjmo': "Vowel Jamo Forms",
  'vkna': "Vertical Kana Alternates",
  'vkrn': "Vertical Kerning",
  'vpal': "Proportional Alternate Vertical Metrics",
  'vrt2': "Vertical Alternates and Rotation",
  'vrtr': "Vertical Alternates for Rotation",
  'zero': "Slashed Zero",
}

for i in range(1,100):
  FEATURE_DESCRIPTIONS["cv%02i" % i] = "Character variant "+str(i)