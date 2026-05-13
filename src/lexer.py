import re
import sys

# ------------------------------------------
#  DEFINICION DE TOKENS
# ------------------------------------------

TOKEN_RULES = [
    # Comentarios (se descartan)
    ('COMMENT',     r'#.*'),

    # Palabras reservadas (deben ir antes que ID)
    ('INT',         r'\bint\b'),
    ('FLOAT_T',     r'\bfloat\b'),
    ('BOOL',        r'\bbool\b'),
    ('IF',          r'\bif\b'),
    ('ELSE',        r'\belse\b'),
    ('WHILE',       r'\bwhile\b'),
    ('FUN',         r'\bfun\b'),
    ('RETURN',      r'\breturn\b'),
    ('PRINT',       r'\bprint\b'),
    ('TRUE',        r'\btrue\b'),
    ('FALSE',       r'\bfalse\b'),

    # Literales numericos (float antes que int)
    ('NUM_FLOAT',   r'[0-9]+\.[0-9]+'),
    ('NUM_INT',     r'[0-9]+'),

    # Identificadores
    ('ID',          r'[a-zA-Z_][a-zA-Z0-9_]*'),

    # Operadores dobles (deben ir antes que los simples)
    ('EQ',          r'=='),
    ('NEQ',         r'!='),

    # Operadores simples
    ('ASSIGN',      r'='),
    ('PLUS',        r'\+'),
    ('MINUS',       r'-'),
    ('TIMES',       r'\*'),
    ('DIVIDE',      r'/'),
    ('LT',          r'<'),
    ('GT',          r'>'),

    # Delimitadores
    ('LPAREN',      r'\('),
    ('RPAREN',      r'\)'),
    ('LBRACE',      r'\{'),
    ('RBRACE',      r'\}'),
    ('SEMI',        r';'),
    ('COMMA',       r','),
    ('COLON',       r':'),

    # Espacios y saltos de linea (se descartan)
    ('NEWLINE',     r'\n'),
    ('WHITESPACE',  r'[ \t]+'),
]

# ------------------------------------------
#  CLASE TOKEN
# ------------------------------------------

class Token:
    def __init__(self, tipo, valor, linea, columna):
        self.tipo    = tipo
        self.valor   = valor
        self.linea   = linea
        self.columna = columna

    def __repr__(self):
        return f'Token({self.tipo}, {repr(self.valor)}, linea={self.linea}, col={self.columna})'

# ------------------------------------------
#  CLASE LEXER
# ------------------------------------------

class Lexer:
    def __init__(self, codigo):
        self.codigo   = codigo
        self.tokens   = []
        self.errores  = []
        self.linea    = 1
        self.columna  = 1

    def tokenizar(self):
        pos = 0
        codigo = self.codigo

        # Compilar todas las reglas en un solo patron
        patron_maestro = '|'.join(
            f'(?P<{nombre}>{regex})'
            for nombre, regex in TOKEN_RULES
        )
        regex_compilada = re.compile(patron_maestro)

        while pos < len(codigo):
            match = regex_compilada.match(codigo, pos)

            if match:
                tipo  = match.lastgroup
                valor = match.group()

                if tipo == 'NEWLINE':
                    self.linea   += 1
                    self.columna  = 1

                elif tipo in ('WHITESPACE', 'COMMENT'):
                    # Se descartan, solo se actualiza la columna
                    self.columna += len(valor)

                else:
                    token = Token(tipo, valor, self.linea, self.columna)
                    self.tokens.append(token)
                    self.columna += len(valor)

                pos = match.end()

            else:
                # Caracter no reconocido 'error lexico'
                caracter = codigo[pos]
                error = {
                    'caracter': caracter,
                    'linea':    self.linea,
                    'columna':  self.columna
                }
                self.errores.append(error)
                print(f'[Error lexico] Caracter invalido "{caracter}" '
                      f'en linea {self.linea}, columna {self.columna}')
                self.columna += 1
                pos += 1

        return self.tokens

    def mostrar_tokens(self):
        print('\n── Tokens generados ──────────────────────────')
        for token in self.tokens:
            print(f'  {token}')
        print(f'── Total: {len(self.tokens)} tokens ──────────────────────────\n')

    def mostrar_errores(self):
        if self.errores:
            print(f'\n── Errores lexicos: {len(self.errores)} ──────────────────')
            for e in self.errores:
                print(f'  Linea {e["linea"]}, columna {e["columna"]}: '
                      f'caracter invalido "{e["caracter"]}"')
        else:
            print('\n── Sin errores lexicos ────────────────────────\n')

# ------------------------------------------
#  PUNTO DE ENTRADA
# ------------------------------------------

def main():
    if len(sys.argv) != 2:
        print('Uso: python lexer.py <archivo.peka>')
        sys.exit(1)

    archivo = sys.argv[1]

    try:
        with open(archivo, 'r', encoding='utf-8') as f:
            codigo = f.read()
    except FileNotFoundError:
        print(f'Error: no se encontrO el archivo "{archivo}"')
        sys.exit(1)

    print(f'\nAnalizando: {archivo}')
    print('─' * 45)

    lexer  = Lexer(codigo)
    tokens = lexer.tokenizar()

    lexer.mostrar_tokens()
    lexer.mostrar_errores()

if __name__ == '__main__':
    main()