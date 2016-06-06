# https://regexcrossword.com/challenges/beginner/puzzles/
import rectMap as rect

class simpleCross():
    def __init__( self, values ):
        self.maps = values[ "maps" ]
        self.regexs = values[ "regexs" ]
        self.printer = values[ "printer" ]
        self.allLen = values[ "allLen" ]

cross = []

cross.append( simpleCross( {
    "maps":    rect.getMap( 2, 2 ),
    "allLen":  rect.getLens( 2, 2 ),
    "printer": rect.getPrinter( 2, 2 ),
    "regexs": [
        r"HE|LL|O+",
        r"[PLEASE]+",
        r"[^SPEAK]+",
        r"EP|IP|EF"
        ]
    } ) )
