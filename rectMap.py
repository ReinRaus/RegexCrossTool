# прямоугольний кроссворд с нумерацией регулярных выражений от 0 сверху-вниз,
# потом слева-направо
#

def getMap( width, height ):
    result = {}
    for x in range( width ):
        for y in range( height ):
            index = y * width + x
            result[ index ] = {
                1: [ y, x ],
                2: [ height + x, y ]
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
