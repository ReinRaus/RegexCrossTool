import hexaMap
from crossObject import crossObject

cross = [ crossObject( 
    hexaMap.getMap( 7 ),
    [7,8,9,10,11,12,13,12,11,10,9,8,7,
     7,8,9,10,11,12,13,12,11,10,9,8,7,
     7,8,9,10,11,12,13,12,11,10,9,8,7],
    hexaMap.getPrinter( 7 ),
    [
        r".*H.*H.*",            # 0
        r"(DI|NS|TH|OM)*",      # 1 
        r"F.*[AO].*[AO].*",     # 2
        r"(O|RHH|MM)*",         # 3
        r".*",                  # 4
        r"C*MC(CCC|MM)*",       # 5
        r"[^C]*[^R]*III.*",     # 6
        r"(...?)\1*",           # 7
        r"([^X]|XCC)*",         # 8
        r"(RR|HHH)*.?",         # 9
        r"N.*X.X.X.*E",         # 10
        r"R*D*M*",              # 11
        r".(C|HH)*",            # 12
                
        r"(ND|ET|IN)[^X]*",     # 13
        r"[CHMNOR]*I[CHMNOR]*", # 14
        r"P+(..)\1.*",          # 15
        r"(E|CR|MN)*",          # 16
        r"([^MC]|MM|CC)*",      # 17
        r"[AM]*CM(RC)*R?",      # 18
        r".*",                  # 19
        r".*PRR.*DDC.*",        # 20
        r"(HHX|[^HX])*",        # 21
        r"([^EMC]|EM)*",        # 22
        r".*OXR.*",             # 23
        r".*LR.*RL.*",          # 24
        r".*SE.*UE.*",          # 25
              
        r".*G.*V.*H.*",         # 26
        r"[CR]*",               # 27
        r".*XEXM*",             # 28
        r".*DD.*CCM.*",         # 29
        r".*XHCR.*X.*",         # 30
        r".*(.)(.)(.)(.)\4\3\2\1.*", # 31
        r".*(IN|SE|HI)",        # 32 очень долгое, оптимизация 1
        r"[^C]*MMM[^C]*",       # 33
        r".*(.)C\1X\1.*",       # 34
        r"[CEIMU]*OH[AEMOR]*",  # 35
        r"(RX|[^R])*",          # 36
        r"[^M]*M[^M]*",         # 37
        r"(S|MM|HHH)*"          # 38
    ] ) ]
