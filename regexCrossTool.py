import re, time, os, pickle, hashlib

reChars = r"\[\^?[a-z]+\]|[a-z]|\."
reCharsC = re.compile( reChars, re.I )


# regex     исходное регулярное выражение               [ab]c*d?
# length    длина на которую оно распространяется       4
# regex2    измененное выражение с "атомизацией" сим-
#           вольных классов                             ^(?:\[ab\])(?:c)*(?:d)?$
# units     уникальные "атомные" символьные классы      [ab] , c , d
# variants  все возможные варианты                      [ab]ccc , [ab]ccd
class singleRegex:
    def __init__( self, regex, length ):
        self.regex = regex   
        self.length = length 
        self.__processEntitys()
        
    def __processEntitys( self ):
        def repl( m ):
            return "(?:"+re.escape( m.group(0) )+")"
        res = reCharsC.findall( self.regex ) # все симв.классы
        self.regex2 = reCharsC.sub( repl, self.regex ) # "атомизация" симв.классов
        self.regex2 = re.compile( "^" + self.regex2 + "$", re.I )
        self.units = list( set( res ) ) # только уникальные симв.классы
        self.variants = self.__getVariants() # генерация вариантов

    def __getVariants( self ):
        optim = self.__optimization() # пробуем применить оптимизации
        if optim: return optim
        result = []
        maxv = len( self.units )
        if maxv == 1: # если всего один символьный класс
            result.append( self.units[0]*self.length )
        else:
            counter = [0]*(self.length+1)   # алогритм полного перебора массива
            label = 0                       # длиной length от 0 до maxv
            iterCounter = 1
            while counter[self.length] == 0:
                text = ""
                for i in range( self.length ): # соединяем симв.классы в одну строку на основе массива в котором идет полный перебор
                    text+= self.units[ counter[i] ]
                if self.regex2.match( text ): # проверям, что полученная строка соответствует "атомизированному" регулярному выражению, таким образом достигается поддержка регулярных варажений любой сложности
                    result.append( text )

                counter[label]+= 1 # перебор +1, если достигли maxv, то увеличиваем элемент справа
                while counter[label] == maxv:
                    label+=1
                    counter[label]+= 1
                while label>0:
                    label-=1
                    counter[label] = 0
                if iterCounter % 10000000 == 0:
                    print( "I work. Iteration:", iterCounter )
                iterCounter+=1
        return result
    
    def __optimization( self ):
        result = []
        # оптимизация - альтернатива в конце строки одной длины
        result1 = []
        reCh = r"(?:"+reChars+")+"
        re1 = r"(?!^)\((?:"+reCh+r"\|)+"+reCh+r"\)$"
        opt1 = re.findall(re1, self.regex, re.I)
        if len( opt1 ) > 0:
            opt1 = opt1[0].replace( "(", "" ).replace( ")", "" )
            parts = opt1.split( "|" )
            count = list( set( [ len( re.findall( reChars, i, re.I ) ) for i in parts ] ) )
            if len( count ) == 1:
                count = count[0]
                left = re.sub( re1, "", self.regex, flags=re.I )
                result1 = singleRegex( left, self.length-count ).variants
                for i in result1:
                    for j in parts:
                        result.append( i + j )
                return result
            
        # оптимизация альтернативы с квантификатором и в регулярке больше ничего
        # использует переменные предыдущей оптимизация, ничего между ними в
        # коде не размещать

        def recur( arr, string, length ):
            res = []
            for i in arr:
                newstr = string + i
                lenChars = len( reCharsC.findall( newstr ) )
                if lenChars == length: res.append( newstr )
                elif lenChars > length: pass
                else:
                    recres = recur( arr, newstr, length )
                    for j in recres: res.append( j )
            return res
        re1 = r"^\(((?:"+reCh+r"\|)+"+reCh+r")\)[*+]$"
        opt1 = re.findall(re1, self.regex, re.I)
        if len( opt1 ) > 0:
            opt1 = opt1[0]
            parts = opt1.split( "|" )
            if len( parts ) > 0: return recur( parts, "", self.length )
        # несколько символов подряд (вне символьного класса) где нет скобок до вхождения и нет альтернативы
        regex1 = r"^((?:\[(?:\.|[^]])*\]|[^([])*?)([a-z]{2,})(?!\s*[?*+{])(?![^(]*\|)" # что-то внутри [] или [a-z]{2,} если справа не квантификатор 
        grp = re.findall( regex1, self.regex, flags=re.I )
        if len( grp ) > 0:
            counter = 1
            while "["+"a"*counter+"]" in self.units:
                counter+= 1
            opt = grp[0][1]
            replText = "["+"a"*counter+"]"
            def repl( m ):
                    return m.group(1) + replText
            regex = re.sub( regex1, repl, self.regex, flags=re.I )
            #print( "NewRegex", regex, self.regex )
            variants = singleRegex( regex, self.length-len(opt)+1 ).variants
            result = [ i.replace( replText, opt ) for i in variants ]
        if len( result ) > 0: return result
        return None

class Tool:
    def __init__( self, cross ):
        tStart = time.time()
        self.cross = cross
        self.reBack = [ i for i in range( len(cross.regexs) ) if re.search("\\\\\\d", cross.regexs[i] ) ]
        self.loadOrCalcVariants()
        self.fullABC = self.getFullABC()
        changed = True
        countUn, count = 0, 0
        while changed or countUn < 5:
            union = self.unionDiaps()
            intersect = self.intersectMapping( union )
            changed = self.filterDiaps( intersect )
            if countUn  == 2:
                self.checkReBack( intersect )
            if not changed:
                countUn+=1
            else:
                countUn = 0
            count+= 1
            print( "Algoritm step:", count )
        def printer():
            self.cross.printer( self.cross.maps, intersect )
        self.print = printer
        print( "Total time:", time.time() - tStart, "sec" )

    def loadOrCalcVariants( self ):
        cross = self.cross
        hash1 = hashlib.md5( "\n".join( cross.regexs + list( map( str, cross.allLen ) ) ).encode() ).hexdigest()
        fname = "cross-"+hash1+".cache"
        if os.path.isfile( fname ):
            with open( fname, "rb" ) as rfile:
                self.allRegexs = pickle.load( rfile )
                print( "Cache from:", fname, "loaded." )
        else:
            tStart = time.time()
            self.allRegexs = []
            for i in range( len( cross.regexs ) ):
                t1 = time.time()
                self.allRegexs.append( singleRegex( cross.regexs[i], cross.allLen[i] ) )
                print( cross.regexs[i], ":", time.time()-t1, "sec", self.allRegexs[i].variants )
            with open( fname, "wb" ) as rfile:
                pickle.dump( self.allRegexs, rfile )
            print( "Total time:", time.time()-tStart, "sec" )

    def getFullABC( self ):
        result = set()
        for i in self.cross.regexs:
            for j in reCharsC.findall( i ):
                if not re.match( r"\[\^", j ) and not j == ".":
                    result = result.union( self.char2set( j ) )
        return result

    def char2set( self, char ):
        char=char.lower()
        result = None
        def convDiap( diap ):
            return re.sub( r"([a-z])\-([a-z])", repl, diap, flags=re.I )
        def repl( m ): # d-h -> defgh
            res = ""
            for i in range( ord( m.group(1) ), ord( m.group(2) )+1 ):
                res+= chr( i )
            return res
        char = char.replace( ".", "[a-z]" )
        char = convDiap( char )
        if re.fullmatch( "[a-z]", char, re.I ):
            result = set( [char] )
        elif re.fullmatch( r"\[[a-z]+\]", char, re.I ):
            result = set( char.replace( "[", "" ).replace( "]", "" ) )
        elif re.fullmatch( r"\[\^[a-z]+\]", char, re.I ):
            result = set( char.replace( "[", "" ).replace( "]", "" ).replace( "^", "" ) )
            result = self.fullABC - result
        return result

    def unionDiaps( self ):
        # перебираем все варианты и делаем сеты конкретных символов в конкретных позициях
        result = [None]*len(self.allRegexs)
        for i in range( len(self.allRegexs) ): # перебор наборов вариантов
            sets = [ set() ] * self.allRegexs[i].length
            for j in self.allRegexs[i].variants: # конкретные варианты
                chars = reCharsC.findall( j )
                for k in range( len(chars) ):
                    s2 = self.char2set( chars[k] )
                    if len(sets) != len(chars):
                        print( j, chars )
                    sets[k] = sets[k].union( s2 )
            result[i] = sets
        return result

    def intersectMapping( self, union ):
        for i in self.cross.maps:
            res = None
            text = ""
            for j in self.cross.maps[i]: # пересечения в соответствии с картой
                iRe  = self.cross.maps[i][j][0]
                iPos = self.cross.maps[i][j][1]
                text+= str( union[iRe][iPos] )+"\n"
                if res == None:
                    res = union[iRe][iPos].copy()
                else:
                    res = res & union[iRe][iPos]
            for j in self.cross.maps[i]: # записываем результат пересечений обратно 
                iRe  = self.cross.maps[i][j][0]
                iPos = self.cross.maps[i][j][1]
                if len( res ) ==0: print( union[iRe][iPos] )
                union[iRe][iPos] = res.copy()
            text+="inter: "+str(res)+"\n"
            #print( text )
            if len( res ) == 0:
                for j in self.cross.maps[i]:  
                    iRe  = self.cross.maps[i][j][0]
                    iPos = self.cross.maps[i][j][1]
                    print( "null set", iRe, iPos )
                print()
        return union
                
    def filterDiaps( self, intersect ):
        changed = False
        for i in range( len(self.allRegexs) ):
            toDel = []
            for k in range( len( self.allRegexs[i].variants ) ):
                ch = reCharsC.findall( self.allRegexs[i].variants[k] )
                mark = False
                for j in range( len( ch ) ):
                    ls = "".join( list( intersect[i][j] ) )
                    if not re.search( ch[j], ls, re.I ): mark = True
                if mark: toDel.append( k )
            if len( toDel ) > 0:
                changed = True
                toDel.reverse()
                for k in toDel: del self.allRegexs[i].variants[k]
        return changed

    def checkReBack( self, intersect ):
        for i in self.reBack:
            print( "Backtracing Algoritm for:", self.cross.regexs[i] )
            text = ""
            counter = 0
            sets = []
            maxs = []
            for j in intersect[i]:
                if len( j ) == 1:
                    text+= list( j )[0]
                else:
                    text+= "("+str(counter)+ ")"
                    sets.append( list( j ) )
                    maxs.append( len( j ) )
                    counter+= 1

            iters = 1
            for j in maxs: iters*= j
            maxs.append( 0 )
            length = len( sets )
            counter = [0]*(length+2)
            label = 0
            iterCounter = 1
            result = []
            while counter[length] == 0:
                text2 = text
                for j in range( length ):
                    text2= text2.replace( "("+str(j)+")", sets[j][ counter[j] ], 1 )
                if re.fullmatch( self.cross.regexs[i], text2, re.I ):
                    result.append( text2 )
                
                counter[label]+= 1
                while counter[label] == maxs[label]:
                    label+=1
                    counter[label]+= 1
                while label>0:
                    label-=1
                    counter[label] = 0
                if iterCounter % 5000000 == 0:
                    print( "Work. Iteration:", iterCounter )
                iterCounter+=1
            self.allRegexs[i].variants = result
