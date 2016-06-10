# https://regexcrossword.com/challenges/beginner/puzzles/
import rectMap as rect
from crossObject import crossObject

cross = []

# Beatles 0
cross.append( crossObject(
    rect.getMap( 2, 2 ),
    rect.getLens( 2, 2 ),
    rect.getPrinter( 2, 2 ),
    [
        r"HE|LL|O+",
        r"[PLEASE]+",
        r"[^SPEAK]+",
        r"EP|IP|EF"
    ] ) )

# Naughty 1
cross.append( crossObject(
    rect.getMap( 2, 2 ),
    rect.getLens( 2, 2 ),
    rect.getPrinter( 2, 2 ),
    [
        r".*M?O.*",
        r"(AN|FE|BE)",
        r"(A|B|C)\1",
        r"(AB|OE|SK)"
    ] ) )

# Ghost 2
cross.append( crossObject(
    rect.getMap( 2, 2 ),
    rect.getLens( 2, 2 ),
    rect.getPrinter( 2, 2 ),
    [
        r"(.)+\1",
        r"[^ABRC]+",
        r"[COBRA]+",
        r"(AB|O|OR)+"
    ] ) )

# Symbolism 3
cross.append( crossObject(
    rect.getMap( 2, 2 ),
    rect.getLens( 2, 2 ),
    rect.getPrinter( 2, 2 ),
    [
        r"[*]+",
        r"/+",
        r".?.+",
        r".+"
    ] ) )
