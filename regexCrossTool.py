import re

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
        # несколько символов подряд (в строке нет скобок)
    ##    result2 = []
    ##    if not re.search( r"[()]", self.regex ):
    ##        grp = re.findall( r"(?<![\[])[a-z]{2,}(?![\]*+?{])", self.regex, re.I )
    ##        if len( grp ) >0 :
    ##            ent2 = getEntitys( self.regex.replace( grp[0], "#", 1 ) )
    ##            ent2[0].replace( "#", "(?:"+grp[0]+")" )
    ##            ent2[1] = re.compile( "^"+ent2[0]+"$", re.I )
    ##            ent2[2].append( grp[0] )
    ##            print( ent, "\n", ent2 )
        if len( result ) > 0: return result
        return None

class Tool:

    pass

x = singleRegex( r".*(as|sd|df)(IN|SE|HI)", 6 ).variants
print( x )
