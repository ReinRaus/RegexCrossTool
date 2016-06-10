# прямоугольний кроссворд с нумерацией регулярных выражений от 0 сверху-вниз,
# потом слева-направо
#    3  4  5  6      dimensions
# 0  .  .  .  .      0  →
# 1  .  .  .  .      1  ↓
# 2  .  .  .  .

def getMap( width, height, invers = [False, False] ):
    result = {}
    for x in range( width ):
        for y in range( height ):
            index = y * width + x
            result[ index ] = {
                0: [ y, x if not invers[0] else width - x - 1 ],
                1: [ height + x, y if not invers[1] else height - y - 1 ]
                }
    return result

def getPrinter( width, height ):
    def printer( maps, intersect ):
        text = ""
        for y in range( height ):
            for x in range( width ):
                index = y * width + x
                if index in maps.keys():
                    val = maps[ index ][1]
                    if len( intersect[val[0]][val[1]] ) == 1:
                        text += list( intersect[val[0]][val[1]] )[0]
                    else:
                        text += "*"
            text += "\n"
        print( text )
    return printer

def getLens( width, height ):
    return [ width ] * height + [height] * width

