# -*- coding: utf-8 -*-
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
    def __init__( self, regex, length, debug=False ):
        self.regex = regex   
        self.length = length
        self.debug = debug
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
        self.regex2 = re.compile( b"^" + bytes(self.regex2, "utf-8") + b"$" )
        self.variants = self.__getVariants() # генерация вариантов

    def __getVariants( self ):
        BEGIN = ord( 'A' )
        optim = self.__optimization() # пробуем применить оптимизации
        if optim: return optim
        if self.debug: print( "DEBUG: No optimization" )
        result = []
        maxv = len( self.units )+ BEGIN
        if len( self.units )==1: # если всего один символьный класс
            if self.regex2.match( bytes(self.unitsShort[0], "utf-8") * self.length ):
                result.append( self.units[0] * self.length )
        else:
            counter = [BEGIN] * self.length # алгоритм полного перебора массива
            label = 0                       # длиной length от 0 до maxv
            iterCounter = 1
            loop = True
            while loop:
                if self.regex2.match( bytes(counter) ): # проверям, что полученная строка соответствует "атомизированному" регулярному выражению, таким образом достигается поддержка регулярных варажений любой сложности
                    text = ""
                    for i in range( self.length ):
                        text+= self.units[ counter[i]-BEGIN ]
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
                return result
                if self.debug: print( "DEBUG: Used optimization: Alternative in end of string .*(A|B|C)" )
            
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
                print( cross.regexs[i], ":", time.time()-t1, "sec" )
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

    def optimReBack( self, regex, intersect ):
        if regex == r"(...?)\1*": # да и пофиг, что конкретное оптимизируем
            length = len( intersect )
            result = []
            for i in intersect[0]:
                for j in intersect[1]:
                    result.append( (i+j)*int(length/2) )
                    for k in intersect[2]:
                        result.append( (i+j+k)*int(length/3) )
            for i in range( len(result)-1, -1, -1 ):
                needDelete = False
                for j in range( length ):
                    if not result[i][j] in intersect[j]: needDelete = True
                if needDelete: del result[i]
            print( "Optimization for:", regex, "Variants:", len( result ) )
            return result

    def checkReBack( self, intersect ):
        for i in self.reBack:
            optim = self.optimReBack( self.cross.regexs[i], intersect[i] )
            if optim:
                self.allRegexs[i].variants = optim
                continue
            reC = re.compile( self.cross.regexs[i], re.I )
            textArr = [None]*len(intersect[i])
            counter = 0
            sets = []
            maxs = []
            cntmap=[]
            for j in intersect[i]:
                if len( j ) == 1:
                    textArr[counter]=list( j )[0]
                else:
                    cntmap.append( counter )
                    sets.append( list( j ) )
                    maxs.append( len( j ) )
                counter+= 1
            
            iters = 1
            for j in maxs: iters*= j
            print( "Backtracing Algoritm for:", self.cross.regexs[i], "Total iters:", iters )
            maxs.append( 0 )
            length = len( sets )
            counter = [0]*(length+2)
            label = 0
            iterCounter = 1
            result = []
            while counter[length] == 0:
                for j in range( length ):
                    textArr[cntmap[j]] = sets[j][ counter[j] ]
                textStr = "".join( textArr )
                if reC.fullmatch( textStr ):
                    result.append( textStr )
                
                counter[label]+= 1
                while counter[label] == maxs[label]:
                    label+=1
                    counter[label]+= 1
                while label>0:
                    label-=1
                    counter[label] = 0
                if iterCounter % 5000000 == 0:
                    print( "Work. Iteration:", iterCounter, "Progress:", int( iterCounter/iters*100 ), "%" )
                iterCounter+=1
            self.allRegexs[i].variants = result

if __name__ == "__main__":
    t1 = time.time()
    test = singleRegex( "C*MC(CCC|MM)*", 5, True )
    t2 = time.time()
    print( t2 - t1 )
    print( test.variants )
