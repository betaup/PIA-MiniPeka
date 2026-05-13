import sys
sys.stdout.reconfigure(encoding='utf-8')

from lexer import Lexer, Token

# ------------------------------------------
#  NODOS DEL AST
# ------------------------------------------

class Nodo:
    pass

class NodoPrograma(Nodo):
    def __init__(self, sentencias):
        self.sentencias = sentencias

    def __repr__(self):
        return f'Programa({self.sentencias})'

class NodoDeclaracion(Nodo):
    def __init__(self, tipo, nombre, valor):
        self.tipo   = tipo
        self.nombre = nombre
        self.valor  = valor

    def __repr__(self):
        return f'Decl({self.tipo} {self.nombre} = {self.valor})'

class NodoAsignacion(Nodo):
    def __init__(self, nombre, valor):
        self.nombre = nombre
        self.valor  = valor

    def __repr__(self):
        return f'Asign({self.nombre} = {self.valor})'

class NodoBinario(Nodo):
    def __init__(self, izquierda, operador, derecha):
        self.izquierda = izquierda
        self.operador  = operador
        self.derecha   = derecha

    def __repr__(self):
        return f'({self.izquierda} {self.operador} {self.derecha})'

class NodoNumero(Nodo):
    def __init__(self, valor, tipo):
        self.valor = valor
        self.tipo  = tipo

    def __repr__(self):
        return f'{self.valor}'

class NodoID(Nodo):
    def __init__(self, nombre):
        self.nombre = nombre

    def __repr__(self):
        return f'{self.nombre}'

class NodoIf(Nodo):
    def __init__(self, condicion, bloque_if, bloque_else=None):
        self.condicion   = condicion
        self.bloque_if   = bloque_if
        self.bloque_else = bloque_else

    def __repr__(self):
        return f'If({self.condicion}, {self.bloque_if}, {self.bloque_else})'

class NodoWhile(Nodo):
    def __init__(self, condicion, bloque):
        self.condicion = condicion
        self.bloque    = bloque

    def __repr__(self):
        return f'While({self.condicion}, {self.bloque})'

class NodoFuncion(Nodo):
    def __init__(self, nombre, params, tipo_retorno, cuerpo):
        self.nombre       = nombre
        self.params       = params
        self.tipo_retorno = tipo_retorno
        self.cuerpo       = cuerpo

    def __repr__(self):
        return f'Fun({self.nombre}, {self.params}, {self.tipo_retorno})'

class NodoLlamada(Nodo):
    def __init__(self, nombre, args):
        self.nombre = nombre
        self.args   = args

    def __repr__(self):
        return f'Call({self.nombre}, {self.args})'

class NodoPrint(Nodo):
    def __init__(self, expresion):
        self.expresion = expresion

    def __repr__(self):
        return f'Print({self.expresion})'

class NodoReturn(Nodo):
    def __init__(self, expresion):
        self.expresion = expresion

    def __repr__(self):
        return f'Return({self.expresion})'

class NodoBooleano(Nodo):
    def __init__(self, valor):
        self.valor = valor

    def __repr__(self):
        return f'{self.valor}'

# ------------------------------------------
#  PARSER
# ------------------------------------------

class Parser:
    def __init__(self, tokens):
        self.tokens  = tokens
        self.pos     = 0
        self.errores = []

    def token_actual(self):
        if self.pos < len(self.tokens):
            return self.tokens[self.pos]
        return None

    def consumir(self, tipo_esperado):
        token = self.token_actual()
        if token and token.tipo == tipo_esperado:
            self.pos += 1
            return token
        else:
            tipo_actual  = token.tipo  if token else 'EOF'
            valor_actual = token.valor if token else ''
            linea        = token.linea if token else '?'
            error = (f'[Error sintactico] Linea {linea}: '
                     f'se esperaba {tipo_esperado}, '
                     f'se encontro {tipo_actual} ("{valor_actual}")')
            self.errores.append(error)
            print(error)
            return None

    def tipo_actual_es(self, *tipos):
        token = self.token_actual()
        return token is not None and token.tipo in tipos

    def parsear(self):
        sentencias = []
        while self.token_actual() is not None:
            s = self.sentencia()
            if s:
                sentencias.append(s)
        return NodoPrograma(sentencias)

    def sentencia(self):
        token = self.token_actual()
        if token is None:
            return None

        if token.tipo in ('INT', 'FLOAT_T', 'BOOL'):
            return self.declaracion()
        elif token.tipo == 'IF':
            return self.sentencia_if()
        elif token.tipo == 'WHILE':
            return self.sentencia_while()
        elif token.tipo == 'FUN':
            return self.definicion_funcion()
        elif token.tipo == 'PRINT':
            return self.sentencia_print()
        elif token.tipo == 'RETURN':
            return self.sentencia_return()
        elif token.tipo == 'ID':
            return self.asignacion()
        else:
            error = (f'[Error sintactico] Linea {token.linea}: '
                     f'sentencia invalida con token "{token.valor}"')
            self.errores.append(error)
            print(error)
            self.pos += 1
            return None

    def declaracion(self):
        tipo   = self.token_actual().valor
        self.pos += 1
        nombre = self.consumir('ID')
        self.consumir('ASSIGN')
        valor  = self.expresion()
        self.consumir('SEMI')
        if nombre:
            return NodoDeclaracion(tipo, nombre.valor, valor)
        return None

    def asignacion(self):
        nombre = self.consumir('ID')
        self.consumir('ASSIGN')
        valor  = self.expresion()
        self.consumir('SEMI')
        if nombre:
            return NodoAsignacion(nombre.valor, valor)
        return None

    def sentencia_if(self):
        self.consumir('IF')
        self.consumir('LPAREN')
        condicion   = self.expresion()
        self.consumir('RPAREN')
        bloque_if   = self.bloque()
        bloque_else = None
        if self.tipo_actual_es('ELSE'):
            self.consumir('ELSE')
            bloque_else = self.bloque()
        return NodoIf(condicion, bloque_if, bloque_else)

    def sentencia_while(self):
        self.consumir('WHILE')
        self.consumir('LPAREN')
        condicion = self.expresion()
        self.consumir('RPAREN')
        bloque    = self.bloque()
        return NodoWhile(condicion, bloque)

    def bloque(self):
        self.consumir('LBRACE')
        sentencias = []
        while not self.tipo_actual_es('RBRACE') and self.token_actual():
            s = self.sentencia()
            if s:
                sentencias.append(s)
        self.consumir('RBRACE')
        return sentencias

    def definicion_funcion(self):
        self.consumir('FUN')
        nombre = self.consumir('ID')
        self.consumir('LPAREN')
        params = self.parametros()
        self.consumir('RPAREN')
        self.consumir('COLON')
        tipo_retorno = self.token_actual().valor
        self.pos += 1
        cuerpo = self.bloque()
        if nombre:
            return NodoFuncion(nombre.valor, params, tipo_retorno, cuerpo)
        return None

    def parametros(self):
        params = []
        if self.tipo_actual_es('INT', 'FLOAT_T', 'BOOL'):
            tipo   = self.token_actual().valor
            self.pos += 1
            nombre = self.consumir('ID')
            if nombre:
                params.append((tipo, nombre.valor))
            while self.tipo_actual_es('COMMA'):
                self.consumir('COMMA')
                tipo   = self.token_actual().valor
                self.pos += 1
                nombre = self.consumir('ID')
                if nombre:
                    params.append((tipo, nombre.valor))
        return params

    def sentencia_print(self):
        self.consumir('PRINT')
        self.consumir('LPAREN')
        expr = self.expresion()
        self.consumir('RPAREN')
        self.consumir('SEMI')
        return NodoPrint(expr)

    def sentencia_return(self):
        self.consumir('RETURN')
        expr = self.expresion()
        self.consumir('SEMI')
        return NodoReturn(expr)

    def expresion(self):
        izquierda = self.termino()
        while self.tipo_actual_es(
            'PLUS', 'MINUS', 'TIMES', 'DIVIDE',
            'EQ', 'NEQ', 'LT', 'GT'
        ):
            operador  = self.token_actual().valor
            self.pos += 1
            derecha   = self.termino()
            izquierda = NodoBinario(izquierda, operador, derecha)
        return izquierda

    def termino(self):
        token = self.token_actual()
        if token is None:
            return None

        if token.tipo == 'NUM_INT':
            self.pos += 1
            return NodoNumero(int(token.valor), 'int')

        elif token.tipo == 'NUM_FLOAT':
            self.pos += 1
            return NodoNumero(float(token.valor), 'float')

        elif token.tipo in ('TRUE', 'FALSE'):
            self.pos += 1
            return NodoBooleano(token.valor)

        elif token.tipo == 'ID':
            nombre = token.valor
            self.pos += 1
            if self.tipo_actual_es('LPAREN'):
                self.consumir('LPAREN')
                args = self.argumentos()
                self.consumir('RPAREN')
                return NodoLlamada(nombre, args)
            return NodoID(nombre)

        elif token.tipo == 'LPAREN':
            self.consumir('LPAREN')
            expr = self.expresion()
            self.consumir('RPAREN')
            return expr

        else:
            error = (f'[Error sintactico] Linea {token.linea}: '
                     f'expresion invalida con token "{token.valor}"')
            self.errores.append(error)
            print(error)
            self.pos += 1
            return None

    def argumentos(self):
        args = []
        if not self.tipo_actual_es('RPAREN'):
            args.append(self.expresion())
            while self.tipo_actual_es('COMMA'):
                self.consumir('COMMA')
                args.append(self.expresion())
        return args

# ------------------------------------------
#  IMPRIMIR AST
# ------------------------------------------

def imprimir_ast(nodo, nivel=0):
    sangria = '  ' * nivel

    if isinstance(nodo, NodoPrograma):
        print(f'{sangria}Programa')
        for s in nodo.sentencias:
            imprimir_ast(s, nivel + 1)

    elif isinstance(nodo, NodoDeclaracion):
        print(f'{sangria}Declaracion: {nodo.tipo} {nodo.nombre}')
        imprimir_ast(nodo.valor, nivel + 1)

    elif isinstance(nodo, NodoAsignacion):
        print(f'{sangria}Asignacion: {nodo.nombre}')
        imprimir_ast(nodo.valor, nivel + 1)

    elif isinstance(nodo, NodoBinario):
        print(f'{sangria}Operacion: {nodo.operador}')
        imprimir_ast(nodo.izquierda, nivel + 1)
        imprimir_ast(nodo.derecha,   nivel + 1)

    elif isinstance(nodo, NodoNumero):
        print(f'{sangria}Numero: {nodo.valor} ({nodo.tipo})')

    elif isinstance(nodo, NodoID):
        print(f'{sangria}ID: {nodo.nombre}')

    elif isinstance(nodo, NodoBooleano):
        print(f'{sangria}Booleano: {nodo.valor}')

    elif isinstance(nodo, NodoIf):
        print(f'{sangria}If')
        print(f'{sangria}  Condicion:')
        imprimir_ast(nodo.condicion, nivel + 2)
        print(f'{sangria}  Bloque if:')
        for s in nodo.bloque_if:
            imprimir_ast(s, nivel + 2)
        if nodo.bloque_else:
            print(f'{sangria}  Bloque else:')
            for s in nodo.bloque_else:
                imprimir_ast(s, nivel + 2)

    elif isinstance(nodo, NodoWhile):
        print(f'{sangria}While')
        print(f'{sangria}  Condicion:')
        imprimir_ast(nodo.condicion, nivel + 2)
        print(f'{sangria}  Bloque:')
        for s in nodo.bloque:
            imprimir_ast(s, nivel + 2)

    elif isinstance(nodo, NodoFuncion):
        print(f'{sangria}Funcion: {nodo.nombre} -> {nodo.tipo_retorno}')
        print(f'{sangria}  Parametros: {nodo.params}')
        print(f'{sangria}  Cuerpo:')
        for s in nodo.cuerpo:
            imprimir_ast(s, nivel + 2)

    elif isinstance(nodo, NodoLlamada):
        print(f'{sangria}Llamada: {nodo.nombre}')
        for a in nodo.args:
            imprimir_ast(a, nivel + 1)

    elif isinstance(nodo, NodoPrint):
        print(f'{sangria}Print')
        imprimir_ast(nodo.expresion, nivel + 1)

    elif isinstance(nodo, NodoReturn):
        print(f'{sangria}Return')
        imprimir_ast(nodo.expresion, nivel + 1)

    elif nodo is None:
        print(f'{sangria}(nulo)')

# ------------------------------------------
#  PUNTO DE ENTRADA
# ------------------------------------------

def main():
    if len(sys.argv) != 2:
        print('Uso: python parser.py <archivo.peka>')
        sys.exit(1)

    archivo = sys.argv[1]

    try:
        with open(archivo, 'r', encoding='utf-8') as f:
            codigo = f.read()
    except FileNotFoundError:
        print(f'Error: no se encontro el archivo "{archivo}"')
        sys.exit(1)

    print(f'\nAnalizando: {archivo}')
    print('-' * 45)

    lexer  = Lexer(codigo)
    tokens = lexer.tokenizar()

    if lexer.errores:
        print('Se encontraron errores lexicos, abortando analisis sintactico.')
        sys.exit(1)

    parser = Parser(tokens)
    ast    = parser.parsear()

    print('\n-- AST generado ------------------------------------------')
    imprimir_ast(ast)

    if parser.errores:
        print(f'\n-- Errores sintacticos: {len(parser.errores)} --------')
        for e in parser.errores:
            print(f'  {e}')
    else:
        print('\n-- Sin errores sintacticos -------------------------------')

if __name__ == '__main__':
    main()