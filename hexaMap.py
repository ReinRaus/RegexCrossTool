# пусть есть гексагональная доска с длиной грани d - функция getMap создает
# карту этой доски, то есть номер линии в измерении и номер позиции в этой
# линии для каждого из трех измерений.
# одно из измерений разворачивается, потому что в эталонном кроссворде
# это измерение зеркально результатам функции dim3

lens = [] # глобализируем

def dim1( k, n, d ):
    y = k
    x = abs( k - d + 1) + 2 * n
    return [ y, x ]

def dim2( k, n, d ):
    t = k-d+1
    y = n
    if t>0: y+= t
    x = abs( 1-d )+2*k-n
    if t>0: x-= t
    return [ y, x ]

def dim3( k, n, d ):
    t1 = k - d + 1
    t2 = d - k - 1
    y = n
    if t2>0: y+=t2
    x = k + n
    if t1>0: x+=t1
    return [ y, x ]

def pushToRes( y, x, d, val, res, dimens ):
    ind = y*4*d+x
    index = (dimens-1)*(2*d-1)+val[0]
    if dimens==3: val[1] = lens[val[0]]-val[1]-1 # разворачиваем
    val = [ index, val[1] ]
    if ( not ind in res.keys() ): res[ind] = {}
    res[ind][ dimens ] = val

def getMap( d ):
    global lens
    res = {}
    lens = list(range(d,2*d))+list(range(2*d-2,d-1,-1)) # d=3, lens = [3,4,5,4,3]

    for i in range( 0, 2*d-1 ):
        for j in range( lens[i] ):
            d1 = dim1( i, j ,d )
            d2 = dim2( i, j ,d )
            d3 = dim3( i, j ,d )
            pushToRes( d1[0], d1[1], d, [i,j], res, 1 )
            pushToRes( d2[0], d2[1], d, [i,j], res, 2 )
            pushToRes( d3[0], d3[1], d, [i,j], res, 3 )

    return res

def getPrinter( d ):
    def printer( maps, intersect ):
        text = ""
        for y in range( d*2-1 ):
            for x in range( d * 4 ):
                if y*4*d+x in maps.keys():
                    val = maps[ y*4*d+x ][1]
                    if len( intersect[val[0]][val[1]] ) == 1:
                        text += list( intersect[val[0]][val[1]])[0]
                    else:
                        text += "*"
                else:
                    text += " "
            text += "\n"
        print( text )
    return printer
