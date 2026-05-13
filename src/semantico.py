import sys
import os
sys.stdout.reconfigure(encoding='utf-8')

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from lexer import Lexer
from parser import (Parser, NodoPrograma, NodoDeclaracion, NodoAsignacion,
                    NodoBinario, NodoNumero, NodoID, NodoIf, NodoWhile,
                    NodoFuncion, NodoLlamada, NodoPrint, NodoReturn, NodoBooleano)

# --------------------------------------------------------------
#  TABLA DE SIMBOLOS
# --------------------------------------------------------------

class Simbolo:
    def __init__(self, nombre, tipo, categoria, linea=None, params=None, retorno=None):
        self.nombre    = nombre
        self.tipo      = tipo
        self.categoria = categoria
        self.linea     = linea
        self.params    = params
        self.retorno   = retorno


class TablaSimbolos:
    def __init__(self):
        self._scopes = [{}]
        self.scope_actual = 0

    def entrar_scope(self):
        self._scopes.append({})
        self.scope_actual += 1

    def salir_scope(self):
        if self.scope_actual > 0:
            self._scopes.pop()
            self.scope_actual -= 1

    def insertar(self, simbolo):
        scope = self._scopes[-1]
        if simbolo.nombre in scope:
            return False
        scope[simbolo.nombre] = simbolo
        return True

    def buscar(self, nombre):
        for scope in reversed(self._scopes):
            if nombre in scope:
                return scope[nombre]
        return None

    def imprimir(self):
        print("  Tabla de simbolos:")
        for nivel, scope in enumerate(self._scopes):
            etiq = "global" if nivel == 0 else f"scope {nivel}"
            print(f"    [{etiq}]")
            if not scope:
                print("      (vacio)")
            for nombre, sim in scope.items():
                if sim.categoria == 'funcion':
                    print(f"      {nombre}: funcion, params={sim.params}, "
                          f"retorno='{sim.retorno}', linea={sim.linea}")
                else:
                    print(f"      {nombre}: {sim.categoria}, "
                          f"tipo='{sim.tipo}', linea={sim.linea}")


# --------------------------------------------------------------
#  REGLAS DE TIPOS
# --------------------------------------------------------------

TIPO_RESULTADO = {
    ('int',   'int'):   'int',
    ('float', 'float'): 'float',
    ('int',   'float'): 'float',
    ('float', 'int'):   'float',
}

OPS_RELACIONALES = {'==', '!=', '<', '>'}
OPS_ARITMETICAS  = {'+', '-', '*', '/'}

def asignable(tipo_var, tipo_expr):
    if tipo_var == tipo_expr:
        return True
    if tipo_var == 'float' and tipo_expr == 'int':
        return True
    return False


# --------------------------------------------------------------
#  AST ANOTADO — impresion
# --------------------------------------------------------------

def imprimir_ast_anotado(nodo, nivel=0):
    if nodo is None:
        return
    sangria = "  " * nivel
    anotacion = getattr(nodo, 'tipo_anotado', '')
    sufijo    = f"  -> {anotacion}" if anotacion else ""

    if isinstance(nodo, NodoPrograma):
        print(f"{sangria}Programa")
        for s in nodo.sentencias:
            imprimir_ast_anotado(s, nivel + 1)

    elif isinstance(nodo, NodoDeclaracion):
        print(f"{sangria}Declaracion: {nodo.tipo} {nodo.nombre}{sufijo}")
        imprimir_ast_anotado(nodo.valor, nivel + 1)

    elif isinstance(nodo, NodoAsignacion):
        print(f"{sangria}Asignacion: {nodo.nombre}{sufijo}")
        imprimir_ast_anotado(nodo.valor, nivel + 1)

    elif isinstance(nodo, NodoBinario):
        print(f"{sangria}Operacion: {nodo.operador}{sufijo}")
        imprimir_ast_anotado(nodo.izquierda, nivel + 1)
        imprimir_ast_anotado(nodo.derecha,   nivel + 1)

    elif isinstance(nodo, NodoNumero):
        print(f"{sangria}Numero: {nodo.valor} ({nodo.tipo}){sufijo}")

    elif isinstance(nodo, NodoID):
        print(f"{sangria}ID: {nodo.nombre}{sufijo}")

    elif isinstance(nodo, NodoBooleano):
        print(f"{sangria}Booleano: {nodo.valor}{sufijo}")

    elif isinstance(nodo, NodoIf):
        print(f"{sangria}If")
        print(f"{sangria}  Condicion:")
        imprimir_ast_anotado(nodo.condicion, nivel + 2)
        print(f"{sangria}  Bloque if:")
        for s in nodo.bloque_if:
            imprimir_ast_anotado(s, nivel + 2)
        if nodo.bloque_else:
            print(f"{sangria}  Bloque else:")
            for s in nodo.bloque_else:
                imprimir_ast_anotado(s, nivel + 2)

    elif isinstance(nodo, NodoWhile):
        print(f"{sangria}While")
        print(f"{sangria}  Condicion:")
        imprimir_ast_anotado(nodo.condicion, nivel + 2)
        print(f"{sangria}  Bloque:")
        for s in nodo.bloque:
            imprimir_ast_anotado(s, nivel + 2)

    elif isinstance(nodo, NodoFuncion):
        print(f"{sangria}Funcion: {nodo.nombre} -> {nodo.tipo_retorno}")
        print(f"{sangria}  Parametros: {nodo.params}")
        print(f"{sangria}  Cuerpo:")
        for s in nodo.cuerpo:
            imprimir_ast_anotado(s, nivel + 2)

    elif isinstance(nodo, NodoLlamada):
        print(f"{sangria}Llamada: {nodo.nombre}{sufijo}")
        for a in nodo.args:
            imprimir_ast_anotado(a, nivel + 1)

    elif isinstance(nodo, NodoPrint):
        print(f"{sangria}Print")
        imprimir_ast_anotado(nodo.expresion, nivel + 1)

    elif isinstance(nodo, NodoReturn):
        print(f"{sangria}Return")
        imprimir_ast_anotado(nodo.expresion, nivel + 1)


# --------------------------------------------------------------
#  ANALIZADOR SEMANTICO
# --------------------------------------------------------------

class AnalizadorSemantico:
    def __init__(self):
        self.tabla       = TablaSimbolos()
        self.errores     = []
        self._fun_actual = None

    def _error(self, mensaje):
        self.errores.append(f"Error semantico: {mensaje}")

    def analizar(self, ast):
        if ast is None:
            return
        self._visitar(ast)

    def _visitar(self, nodo):
        if nodo is None:
            return None

        if isinstance(nodo, NodoPrograma):
            return self._v_Programa(nodo)
        elif isinstance(nodo, NodoDeclaracion):
            return self._v_Declaracion(nodo)
        elif isinstance(nodo, NodoAsignacion):
            return self._v_Asignacion(nodo)
        elif isinstance(nodo, NodoFuncion):
            return self._v_Funcion(nodo)
        elif isinstance(nodo, NodoReturn):
            return self._v_Return(nodo)
        elif isinstance(nodo, NodoIf):
            return self._v_If(nodo)
        elif isinstance(nodo, NodoWhile):
            return self._v_While(nodo)
        elif isinstance(nodo, NodoPrint):
            return self._v_Print(nodo)
        elif isinstance(nodo, NodoBinario):
            return self._v_BinOp(nodo)
        elif isinstance(nodo, NodoID):
            return self._v_ID(nodo)
        elif isinstance(nodo, NodoNumero):
            return self._v_Numero(nodo)
        elif isinstance(nodo, NodoBooleano):
            return self._v_Booleano(nodo)
        elif isinstance(nodo, NodoLlamada):
            return self._v_Llamada(nodo)
        return None

    # -- Programa --------------------------------------------------------

    def _v_Programa(self, nodo):
        for stmt in nodo.sentencias:
            self._visitar(stmt)

    # -- Declaracion ------------------------------------------------------

    def _v_Declaracion(self, nodo):
        tipo      = nodo.tipo
        nombre    = nodo.nombre
        tipo_expr = self._visitar(nodo.valor)

        if tipo_expr is not None and not asignable(tipo, tipo_expr):
            self._error(
                f"No se puede asignar tipo '{tipo_expr}' a variable "
                f"'{nombre}' de tipo '{tipo}'"
            )

        nodo.tipo_anotado = tipo

        sim = Simbolo(nombre, tipo, 'variable')
        if not self.tabla.insertar(sim):
            self._error(f"Variable '{nombre}' ya fue declarada en este scope")

        return tipo

    # -- Asignacion ------------------------------------------------------─

    def _v_Asignacion(self, nodo):
        nombre = nodo.nombre
        sim = self.tabla.buscar(nombre)
        if sim is None:
            self._error(f"Variable '{nombre}' no declarada")
            return None

        tipo_expr = self._visitar(nodo.valor)
        if tipo_expr is not None and not asignable(sim.tipo, tipo_expr):
            self._error(
                f"Tipo '{tipo_expr}' incompatible con variable "
                f"'{nombre}' de tipo '{sim.tipo}'"
            )

        nodo.tipo_anotado = sim.tipo
        return sim.tipo

    # -- Funcion ------------------------------------------------─

    def _v_Funcion(self, nodo):
        nombre   = nodo.nombre
        retorno  = nodo.tipo_retorno
        # params es lista de tuplas (tipo, nombre)
        params   = nodo.params

        tipos_params = [p[0] for p in params]

        sim_fun = Simbolo(nombre, None, 'funcion', params=tipos_params, retorno=retorno)
        if not self.tabla.insertar(sim_fun):
            self._error(f"Funcion '{nombre}' ya fue declarada")

        self.tabla.entrar_scope()
        prev_fun = self._fun_actual
        self._fun_actual = {
            'nombre':       nombre,
            'retorno':      retorno,
            'tiene_return': False
        }

        for tipo_p, nombre_p in params:
            sim_p = Simbolo(nombre_p, tipo_p, 'parametro')
            if not self.tabla.insertar(sim_p):
                self._error(f"Parametro '{nombre_p}' duplicado en funcion '{nombre}'")

        for stmt in nodo.cuerpo:
            self._visitar(stmt)

        if retorno != 'void' and not self._fun_actual['tiene_return']:
            self._error(
                f"Funcion '{nombre}' con tipo de retorno '{retorno}' "
                f"no tiene instruccion return"
            )

        self._fun_actual = prev_fun
        self.tabla.salir_scope()

    # -- Return --------------------------------------------------

    def _v_Return(self, nodo):
        if self._fun_actual is None:
            self._error("Instruccion 'return' fuera de una funcion")
            return None

        tipo_expr = self._visitar(nodo.expresion)
        tipo_esp  = self._fun_actual['retorno']

        if tipo_expr is not None and not asignable(tipo_esp, tipo_expr):
            self._error(
                f"Funcion '{self._fun_actual['nombre']}' debe retornar "
                f"'{tipo_esp}', pero se retorna '{tipo_expr}'"
            )

        self._fun_actual['tiene_return'] = True
        return tipo_expr

    # -- If ------------------------------------------------------

    def _v_If(self, nodo):
        self._visitar(nodo.condicion)
        for stmt in nodo.bloque_if:
            self._visitar(stmt)
        if nodo.bloque_else:
            for stmt in nodo.bloque_else:
                self._visitar(stmt)

    # -- While --------------------------------------------------─

    def _v_While(self, nodo):
        self._visitar(nodo.condicion)
        for stmt in nodo.bloque:
            self._visitar(stmt)

    # -- Print --------------------------------------------------─

    def _v_Print(self, nodo):
        self._visitar(nodo.expresion)

    # -- Operacion binaria ------------------------------------------------

    def _v_BinOp(self, nodo):
        op    = nodo.operador
        t_izq = self._visitar(nodo.izquierda)
        t_der = self._visitar(nodo.derecha)

        if t_izq is None or t_der is None:
            return None

        if op in OPS_ARITMETICAS:
            if t_izq == 'bool' or t_der == 'bool':
                self._error(f"Operador '{op}' no es valido con tipo 'bool'")
                return None

        if op in OPS_RELACIONALES:
            if t_izq not in ('int', 'float') or t_der not in ('int', 'float'):
                self._error(
                    f"Operador '{op}' requiere operandos numericos, "
                    f"se encontraron '{t_izq}' y '{t_der}'"
                )
            nodo.tipo_anotado = 'bool'
            return 'bool'

        resultado = TIPO_RESULTADO.get((t_izq, t_der))
        if resultado is None:
            self._error(
                f"Operacion '{op}' no valida entre tipos '{t_izq}' y '{t_der}'"
            )
            return None

        nodo.tipo_anotado = resultado
        return resultado

    # -- ID ------------------------------------------------------

    def _v_ID(self, nodo):
        sim = self.tabla.buscar(nodo.nombre)
        if sim is None:
            self._error(f"Variable '{nodo.nombre}' no declarada")
            return None
        nodo.tipo_anotado = sim.tipo
        return sim.tipo

    # -- Numero ------------------------------------------------

    def _v_Numero(self, nodo):
        nodo.tipo_anotado = nodo.tipo
        return nodo.tipo

    # -- Booleano ------------------------------------------------

    def _v_Booleano(self, nodo):
        nodo.tipo_anotado = 'bool'
        return 'bool'

    # -- Llamada a funcion ------------------------------------------------

    def _v_Llamada(self, nodo):
        nombre = nodo.nombre
        args   = nodo.args

        sim = self.tabla.buscar(nombre)
        if sim is None:
            self._error(f"Funcion '{nombre}' no declarada")
            return None
        if sim.categoria != 'funcion':
            self._error(f"'{nombre}' no es una funcion")
            return None

        n_params = len(sim.params)
        n_args   = len(args)
        if n_args != n_params:
            self._error(
                f"Funcion '{nombre}' espera {n_params} argumento(s), "
                f"se recibieron {n_args}"
            )
        else:
            tipos_args = [self._visitar(a) for a in args]
            for i, (t_param, t_arg) in enumerate(zip(sim.params, tipos_args)):
                if t_arg is not None and not asignable(t_param, t_arg):
                    self._error(
                        f"Argumento {i+1} de '{nombre}': se esperaba "
                        f"'{t_param}', se recibio '{t_arg}'"
                    )

        nodo.tipo_anotado = sim.retorno
        return sim.retorno


# --------------------------------------------------------------
#  MAIN
# --------------------------------------------------------------

def main():
    if len(sys.argv) < 2:
        print("Uso: python semantico.py <archivo.peka>")
        sys.exit(1)

    ruta = sys.argv[1]

    try:
        with open(ruta, 'r', encoding='utf-8') as f:
            codigo = f.read()
    except FileNotFoundError:
        print(f"Error: no se encontro el archivo '{ruta}'")
        sys.exit(1)

    lexer = Lexer(codigo)
    tokens = lexer.tokenizar()

    if lexer.errores:
        print("Errores lexicos encontrados. Analisis semantico abortado.")
        for e in lexer.errores:
            print(f"  Linea {e['linea']}, col {e['columna']}: "
                  f"caracter invalido '{e['caracter']}'")
        sys.exit(1)

    p = Parser(tokens)
    ast = p.parsear()

    if p.errores:
        print("Errores sintacticos encontrados. Analisis semantico abortado.")
        for e in p.errores:
            print(f"  {e}")
        sys.exit(1)

    analizador = AnalizadorSemantico()
    analizador.analizar(ast)

    print(f"\nAnalisis semantico de: {ruta}")
    print("=" * 55)
    analizador.tabla.imprimir()

    print("\nAST anotado:")
    print("-" * 55)
    imprimir_ast_anotado(ast)

    print()
    if analizador.errores:
        print(f"Se encontraron {len(analizador.errores)} error(es) semantico(s):")
        for e in analizador.errores:
            print(f"  {e}")
        sys.exit(1)
    else:
        print("Analisis semantico completado sin errores.")


if __name__ == "__main__":
    main()