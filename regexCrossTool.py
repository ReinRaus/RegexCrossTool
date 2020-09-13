# -*- coding: utf-8 -*-
import re, time, os, pickle, hashlib

reChars = r"\[\^?[a-z]+\]|[a-z]|\."
reCharsC = re.compile( reChars, re.I )

# вычисляет на какую длину может распространиться регулярное выражение от minLength до maxLength
def getRegexLength( regex, minLength, maxLength ):
    result = []  
    regex = re.compile( reCharsC.sub( ".", regex ), re.I )
    return [ i for i in range( minLength, maxLength + 1 ) if regex.fullmatch( "a" * i ) ]

# regex     исходное регулярное выражение               [ab]c*d?
# length    длина на которую оно распространяется       4
# regex2    измененное выражение с "атомизацией" сим-
#           вольных классов                             ^(?:\[ab\])(?:c)*(?:d)?$
# units     уникальные "атомные" символьные классы      [ab] , c , d
# variants  все возможные варианты                      [ab]ccc , [ab]ccd
class singleRegex:
    def __init__( self, regex, length, debug=False ):
        self.regex = regex   
        self.length = length
        self.debug = debug
        self.variants = []
        if self.debug: print( "DEBUG: Regex:", regex, "Length:", length )
        self.__processEntitys()
        
    def __processEntitys( self ):
        def repl( m ):
            return self.unitsShort[ self.units.index( m.group(0) ) ]
        res = reCharsC.findall( self.regex ) # все симв.классы
        self.units = list( set( res ) ) # только уникальные симв.классы
        if self.debug: print( "DEBUG: All symbols:", self.units )
        self.unitsShort = list((chr(i) for i in range(ord('A'),ord('A')+len(self.units))))
        self.regex2 = reCharsC.sub( repl, self.regex ) # "атомизация" симв.классов
        if self.debug:
            print( "DEBUG: Atomic regex:", self.regex2 )
            print( "DEBUG: Equivalents for symbols:" )
            for i in range( len( self.units ) ): print( "DEBUG:", self.unitsShort[i], "=", self.units[i] )
        self.regex2 = re.compile( bytes(self.regex2, "utf-8") )
        self.variants = self.__getVariants() # генерация вариантов

    def __getVariants( self ):
        if self.length < 1: return [] # чтобы не обрабатывать на правильность границ
        if self.regex == "": return []
        if not self.length in getRegexLength( self.regex, self.length, self.length ): return []
        optim = self.__optimization() # пробуем применить оптимизации
        if optim: return optim
        if self.debug: print( "DEBUG: No optimization" )
        BEGIN = ord( 'A' )
        result = []
        maxv = len( self.units ) + BEGIN
        if len( self.units )==1: # если всего один символьный класс
            if self.regex2.fullmatch( bytes( self.unitsShort[0], "utf-8" ) * self.length ):
                result.append( self.units[0] * self.length )
        else:
            counter = [BEGIN] * self.length # алгоритм полного перебора массива
            label = 0                       # длиной length от 0 до maxv
            iterCounter = 1
            loop = True
            while loop:
                if self.regex2.fullmatch( bytes(counter) ): # проверям, что полученная строка соответствует "атомизированному" регулярному выражению, таким образом достигается поддержка регулярных варажений любой сложности
                    text = ""
                    for i in range( self.length ):
                        text+= self.units[ counter[i] - BEGIN ]
                    result.append( text )

                counter[label]+= 1 # перебор +1, если достигли maxv, то увеличиваем элемент справа
                while counter[label] == maxv:
                    label+=1
                    if label == self.length: # перебор окончен
                        loop = False
                        break
                    else:
                        counter[label]+= 1
                while label>0:
                    label-=1
                    counter[label] = BEGIN
                if not iterCounter % 10000000:
                    print( "I work. Iteration:", iterCounter )
                iterCounter+=1
        if self.debug and len( result ) == 0: print( "DEBUG: No variants for regex:", self.regex, "Length:", self.length )
        return result # может быть пустой
    
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
                if self.debug: print( "DEBUG: Used optimization: Alternative in end of string .*(A|B|C)" )
                return result
            
        # оптимизация альтернативы с квантификатором и в регулярке больше ничего
        reCh = r"(?:"+reChars+")+"
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
        regex1 = r"^((?:\[(?:\.|[^]])*\]|[^|([])*?)([a-z]{2,})(?!\s*[?*+{])(?![^(]*\|)" # что-то внутри [] или [a-z]{2,} если справа не квантификатор 
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

        # оптимизация - атом в конце строки с квантификатором, если этого атома больше нет в регулярке
        test = re.fullmatch( "(.*)("+reChars+r")([*?+]|\{(\d*),?(\d*)\}|)$", self.regex, re.I )
        if test and ( not (test.group(2) in test.group(1)) or test.group(3) == "" ):
            if self.debug: print( "DEBUG: Used optimization: atom in the end of regex" )
            if test.group(3) == "?":
                rStart, rEnd = 0, 2
            elif test.group(3) == "*":
                rStart, rEnd = 0, self.length+1
            elif test.group(3) == "+":
                rStart, rEnd = 1, self.length+1
            elif test.group(3) == "":
                rStart, rEnd = 1, 2
            else:
                rStart = int( test.group(4) ) if test.group(4) else 0
                rEnd   = int( test.group(5) )+1 if test.group(5) else self.length+1
            availableLengths = getRegexLength( test.group(1), 0, self.length )
            for i in range( rStart, rEnd ):
                if self.length-i in availableLengths:
                    vari = singleRegex( test.group(1), self.length-i )
                    result+=[ j + test.group(2)*i for j in vari.variants ]
            return list(set(result))
        
        # оптимизация - атом в начале строки с квантификатором, если этого атома больше нет в регулярке
        test = re.fullmatch( "^("+reChars+r")([*?+]|\{(\d*),?(\d*)\}|)(.*)", self.regex, re.I )
        if test and ( not (test.group(1) in test.group(5)) or test.group(2) == "" ):
            if self.debug: print( "DEBUG: Used optimization: atom in the start of regex" )
            if test.group(2) == "?":
                rStart, rEnd = 0, 2
            elif test.group(2) == "*":
                rStart, rEnd = 0, self.length+1
            elif test.group(2) == "+":
                rStart, rEnd = 1, self.length+1
            elif test.group(2) == "":
                rStart, rEnd = 1, 2
            else:
                rStart = int( test.group(3) ) if test.group(3) else 0
                rEnd   = int( test.group(4) )+1 if test.group(4) else self.length+1
            availableLengths = getRegexLength( test.group(5), 0, self.length )
            for i in range( rStart, rEnd ):
                if self.length-i in availableLengths:
                    vari = singleRegex( test.group(5), self.length-i )
                    result+=[ test.group(1)*i + j for j in vari.variants ]
            return list(set(result))
        
        if len( result ) > 0: return result
        return None


class Tool:
    def __init__( self, cross ):
        self.reUtils = [
            re.compile( "[a-z]", re.I ),       #0
            re.compile( r"\[[a-z]+\]", re.I ), #1
            re.compile( r"\[\^[a-z]+\]", re.I )#2
        ]
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
                print( cross.regexs[i], "Length:", cross.allLen[i], "Time:", time.time()-t1, "sec" )
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
        if self.reUtils[0].fullmatch( char ): # [a-z]
            result = set( [char] )
        elif self.reUtils[1].fullmatch( char ): # \[[a-z]+\]
            result = set( char.replace( "[", "" ).replace( "]", "" ) )
        elif self.reUtils[2].fullmatch( char ): # \[\^[a-z]+\]
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

    def brutforce( self, regex, intersect ):
            reC = re.compile( regex, re.I )
            textArr = [None]*len(intersect)
            counter = 0
            sets = []
            maxs = []
            cntmap=[]
            for i in intersect:
                if len( i ) == 1:
                    textArr[counter]=list( i )[0]
                else:
                    cntmap.append( counter )
                    sets.append( list( i ) )
                    maxs.append( len( i ) )
                counter+= 1
            
            iters = 1
            for i in maxs: iters*= i
            print( "Brutforce Algoritm for:", regex, "Length:", len(intersect), "Total iters:", iters )
            maxs.append( 0 )
            length = len( sets )
            counter = [0]*(length+2)
            label = 0
            iterCounter = 1
            result = []
            for i in range( length ):
                textArr[cntmap[i]] = sets[i][ counter[i] ]
            if iters == 1: # чтобы не загромождать полный перебор дополнительными проверками на границы массива
                result.append( "".join( [ list(i)[0] for i in intersect ] ) )
                return result
            while True:
                textStr = "".join( textArr )
                if reC.fullmatch( textStr ):
                    result.append( textStr )
                
                counter[label]+= 1
                if not counter[label] == maxs[label]:
                    textArr[cntmap[label]] = sets[label][counter[label] ]
                    continue
                while counter[label] == maxs[label]:
                    label+=1
                    counter[label]+= 1
                if counter[length] != 0: break # выход из перебора
                textArr[cntmap[label]] = sets[label][counter[label] ]
                while label>0:
                    label-=1
                    counter[label] = 0
                    textArr[cntmap[label]] = sets[label][counter[label] ]

                if iterCounter % 5000000 == 0:
                    print( "Work. Iteration:", iterCounter, "Progress:", int( iterCounter/iters*100 ), "%" )
                iterCounter+=1
            return result        

    def optimReBack( self, regex, intersect ):
        result = []
        length = len( intersect )
        reC = re.compile( regex, re.I )
        # регулярка начинается с группы, эта группа единственная и повторяется до конца строки (...?)\1*
        t1 = time.time()
        test = re.fullmatch( r"\((?![?])(.*)\)\\1(?:[*+?]|\{\d*,?\d*\})", regex )
        if test:
            print( "Optimization for:", regex, r"Type: one group to end (...?)\1*" )
            for i in range( 1, len( intersect )+1 ):
                if singleRegex( test.group(1), i ).variants:
                    brut = self.brutforce( test.group(1), intersect[:i] )
                    for j in brut: result.append( j * int( length / i ) )
        else: # если никакие оптимизации не подошли, то полный перебор
            result = self.brutforce( regex, intersect )

        # общий код для всех оптимизаций - фильтрация полученных вариантов
        # первое - проверка, что из множества intersect можно составить полученный текст
        for i in range( len(result)-1, -1, -1 ):
            needDelete = False
            for j in range( length ):
                if not result[i][j] in intersect[j]: needDelete = True
            if needDelete: del result[i]
        # второе - проверка, что полученные результаты соответствуют регулярному выражению
        for i in range( len(result)-1, -1, -1 ):
            if not reC.fullmatch( result[i] ): del result[i]
        t2 = time.time()
        if result: print( "Result for:", regex, "Variants:", len( result ), "Time:", t2-t1 )
        return result

    def checkReBack( self, intersect ):
        for i in self.reBack:
            optim = self.optimReBack( self.cross.regexs[i], intersect[i] )
            self.allRegexs[i].variants = optim

if __name__ == "__main__":
    t1 = time.time()
    test = singleRegex( r".*(IN|SE|HIPS)", 8, True )
    t2 = time.time()
    print( t2 - t1 )
    print( test.variants )
    print( "Len:", len(test.variants))
    print( getRegexLength( r"(aaa)\1*", 0, 12 ) )
    
