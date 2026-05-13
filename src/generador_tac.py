import sys
import os
sys.stdout.reconfigure(encoding='utf-8')

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from src.lexer import Lexer
from src.parser import (Parser, NodoPrograma, NodoDeclaracion, NodoAsignacion,
                    NodoBinario, NodoNumero, NodoID, NodoIf, NodoWhile,
                    NodoFuncion, NodoLlamada, NodoPrint, NodoReturn, NodoBooleano)
from src.semantico import AnalizadorSemantico

# --------------------------------------------------
#  INSTRUCCIONES TAC
# --------------------------------------------------

class Instruccion:
    """Instruccion de codigo de tres direcciones."""
    pass

class Asignar(Instruccion):
    # dest = src
    def __init__(self, dest, src):
        self.dest = dest
        self.src  = src
    def __str__(self):
        return f"    {self.dest} = {self.src}"

class Binaria(Instruccion):
    # dest = izq op der
    def __init__(self, dest, izq, op, der):
        self.dest = dest
        self.izq  = izq
        self.op   = op
        self.der  = der
    def __str__(self):
        return f"    {self.dest} = {self.izq} {self.op} {self.der}"

class Etiqueta(Instruccion):
    def __init__(self, nombre):
        self.nombre = nombre
    def __str__(self):
        return f"{self.nombre}:"

class SaltoIncondicional(Instruccion):
    def __init__(self, etiqueta):
        self.etiqueta = etiqueta
    def __str__(self):
        return f"    goto {self.etiqueta}"

class SaltoCondicional(Instruccion):
    # if NOT cond goto etiqueta
    def __init__(self, cond, etiqueta):
        self.cond     = cond
        self.etiqueta = etiqueta
    def __str__(self):
        return f"    if not {self.cond} goto {self.etiqueta}"

class Parametro(Instruccion):
    def __init__(self, valor):
        self.valor = valor
    def __str__(self):
        return f"    param {self.valor}"

class LlamarFuncion(Instruccion):
    def __init__(self, dest, nombre, n_args):
        self.dest   = dest
        self.nombre = nombre
        self.n_args = n_args
    def __str__(self):
        if self.dest:
            return f"    {self.dest} = call {self.nombre}, {self.n_args}"
        return f"    call {self.nombre}, {self.n_args}"

class InicioFuncion(Instruccion):
    def __init__(self, nombre):
        self.nombre = nombre
    def __str__(self):
        return f"\nfun {self.nombre}:"

class FinFuncion(Instruccion):
    def __init__(self, nombre):
        self.nombre = nombre
    def __str__(self):
        return f"    endfun {self.nombre}"

class Retornar(Instruccion):
    def __init__(self, valor):
        self.valor = valor
    def __str__(self):
        return f"    return {self.valor}"

class Imprimir(Instruccion):
    def __init__(self, valor):
        self.valor = valor
    def __str__(self):
        return f"    print {self.valor}"


# --------------------------------------------------
#  GENERADOR TAC
# --------------------------------------------------

class GeneradorTAC:
    def __init__(self):
        self.instrucciones = []
        self._contador_temp  = 0
        self._contador_label = 0

    # -- Helpers ----------------------------------------------------─

    def _nuevo_temp(self):
        t = f"t{self._contador_temp}"
        self._contador_temp += 1
        return t

    def _nueva_etiqueta(self, prefijo="L"):
        l = f"{prefijo}{self._contador_label}"
        self._contador_label += 1
        return l

    def _emit(self, instr):
        self.instrucciones.append(instr)

    # -- Punto de entrada -----------------------------------------------

    def generar(self, ast):
        self._visitar(ast)

    def _visitar(self, nodo):
        if nodo is None:
            return None

        if isinstance(nodo, NodoPrograma):
            return self._g_Programa(nodo)
        elif isinstance(nodo, NodoDeclaracion):
            return self._g_Declaracion(nodo)
        elif isinstance(nodo, NodoAsignacion):
            return self._g_Asignacion(nodo)
        elif isinstance(nodo, NodoFuncion):
            return self._g_Funcion(nodo)
        elif isinstance(nodo, NodoReturn):
            return self._g_Return(nodo)
        elif isinstance(nodo, NodoIf):
            return self._g_If(nodo)
        elif isinstance(nodo, NodoWhile):
            return self._g_While(nodo)
        elif isinstance(nodo, NodoPrint):
            return self._g_Print(nodo)
        elif isinstance(nodo, NodoBinario):
            return self._g_BinOp(nodo)
        elif isinstance(nodo, NodoID):
            return nodo.nombre
        elif isinstance(nodo, NodoNumero):
            return str(nodo.valor)
        elif isinstance(nodo, NodoBooleano):
            return nodo.valor
        elif isinstance(nodo, NodoLlamada):
            return self._g_Llamada(nodo)
        return None

    # -- Programa --------------------------------------------------

    def _g_Programa(self, nodo):
        for stmt in nodo.sentencias:
            self._visitar(stmt)

    # -- Declaracion --------------------------------------------------

    def _g_Declaracion(self, nodo):
        src = self._visitar(nodo.valor)
        self._emit(Asignar(nodo.nombre, src))

    # -- Asignacion --------------------------------------------------

    def _g_Asignacion(self, nodo):
        src = self._visitar(nodo.valor)
        self._emit(Asignar(nodo.nombre, src))

    # -- Funcion --------------------------------------------------

    def _g_Funcion(self, nodo):
        self._emit(InicioFuncion(nodo.nombre))
        for stmt in nodo.cuerpo:
            self._visitar(stmt)
        self._emit(FinFuncion(nodo.nombre))

    # -- Return --------------------------------------------------

    def _g_Return(self, nodo):
        val = self._visitar(nodo.expresion)
        self._emit(Retornar(val))

    # -- If --------------------------------------------------─

    def _g_If(self, nodo):
        cond       = self._visitar(nodo.condicion)
        label_else = self._nueva_etiqueta("else_")
        label_fin  = self._nueva_etiqueta("fin_if_")

        self._emit(SaltoCondicional(cond, label_else))

        for stmt in nodo.bloque_if:
            self._visitar(stmt)

        if nodo.bloque_else:
            self._emit(SaltoIncondicional(label_fin))
            self._emit(Etiqueta(label_else))
            for stmt in nodo.bloque_else:
                self._visitar(stmt)
            self._emit(Etiqueta(label_fin))
        else:
            self._emit(Etiqueta(label_else))

    # -- While ----------------------------------------------------

    def _g_While(self, nodo):
        label_inicio = self._nueva_etiqueta("while_")
        label_fin    = self._nueva_etiqueta("fin_while_")

        self._emit(Etiqueta(label_inicio))
        cond = self._visitar(nodo.condicion)
        self._emit(SaltoCondicional(cond, label_fin))

        for stmt in nodo.bloque:
            self._visitar(stmt)

        self._emit(SaltoIncondicional(label_inicio))
        self._emit(Etiqueta(label_fin))

    # -- Print ----------------------------------------------------

    def _g_Print(self, nodo):
        val = self._visitar(nodo.expresion)
        self._emit(Imprimir(val))

    # -- Operacion binaria --------------------------------------------------

    def _g_BinOp(self, nodo):
        izq  = self._visitar(nodo.izquierda)
        der  = self._visitar(nodo.derecha)
        dest = self._nuevo_temp()
        self._emit(Binaria(dest, izq, nodo.operador, der))
        return dest

    # -- Llamada a funcion ------------------------------------------------

    def _g_Llamada(self, nodo):
        for arg in nodo.args:
            val = self._visitar(arg)
            self._emit(Parametro(val))
        dest = self._nuevo_temp()
        self._emit(LlamarFuncion(dest, nodo.nombre, len(nodo.args)))
        return dest

    # -- Mostrar TAC --------------------------------------------------

    def mostrar(self):
        print("\nCodigo de tres direcciones (TAC):")
        print("=" * 55)
        for instr in self.instrucciones:
            print(instr)


# --------------------------------------------------
#  OPTIMIZACION: PROPAGACION DE CONSTANTES
# --------------------------------------------------

def es_constante(valor):
    """Devuelve True si el valor es un literal numerico o booleano."""
    try:
        float(valor)
        return True
    except (ValueError, TypeError):
        pass
    return str(valor) in ('true', 'false')


def propagar_constantes(instrucciones):
    """
    Recorre las instrucciones TAC y sustituye variables que solo
    tienen un valor constante por ese valor directamente.
    Devuelve la lista optimizada.
    """
    constantes = {}   # nombre -> valor constante
    resultado  = []

    for instr in instrucciones:

        # Sustituir en instrucciones binarias
        if isinstance(instr, Binaria):
            izq = constantes.get(instr.izq, instr.izq)
            der = constantes.get(instr.der, instr.der)

            # Evaluacion en tiempo de compilacion si ambos son constantes
            if es_constante(izq) and es_constante(der):
                try:
                    val = eval(f"{izq} {instr.op} {der}")
                    # Convertir bool de Python a string minuscula
                    if isinstance(val, bool):
                        val = 'true' if val else 'false'
                    else:
                        val = int(val) if float(val) == int(val) else val
                    constantes[instr.dest] = str(val)
                    resultado.append(Asignar(instr.dest, str(val)))
                    continue
                except Exception:
                    pass

            nueva = Binaria(instr.dest, izq, instr.op, der)
            resultado.append(nueva)

        elif isinstance(instr, Asignar):
            src = constantes.get(instr.src, instr.src)
            if es_constante(src):
                constantes[instr.dest] = src
            nueva = Asignar(instr.dest, src)
            resultado.append(nueva)

        elif isinstance(instr, SaltoCondicional):
            cond = constantes.get(instr.cond, instr.cond)
            resultado.append(SaltoCondicional(cond, instr.etiqueta))

        elif isinstance(instr, Parametro):
            val = constantes.get(instr.valor, instr.valor)
            resultado.append(Parametro(val))

        elif isinstance(instr, Imprimir):
            val = constantes.get(instr.valor, instr.valor)
            resultado.append(Imprimir(val))

        elif isinstance(instr, Retornar):
            val = constantes.get(instr.valor, instr.valor)
            resultado.append(Retornar(val))

        else:
            resultado.append(instr)

    return resultado


def mostrar_optimizado(instrucciones):
    print("\nTAC optimizado (propagacion de constantes):")
    print("=" * 55)
    for instr in instrucciones:
        print(instr)

# ----------------------------------------------------------
#  OPTIMIZACION: ELIMINACION DE CODIGO MUERTO
# ----------------------------------------------------------

def eliminar_codigo_muerto(instrucciones):
    """
    Elimina instrucciones cuyo resultado nunca se usa.
    Una asignacion o binaria es muerta si su destino no aparece
    en ningun lado despues de ser definido.
    """
    # Recopilar todos los valores que se leen en alguna instruccion
    usados = set()
    for instr in instrucciones:
        if isinstance(instr, Binaria):
            usados.add(instr.izq)
            usados.add(instr.der)
        elif isinstance(instr, Asignar):
            usados.add(instr.src)
        elif isinstance(instr, SaltoCondicional):
            usados.add(instr.cond)
        elif isinstance(instr, Parametro):
            usados.add(instr.valor)
        elif isinstance(instr, Imprimir):
            usados.add(instr.valor)
        elif isinstance(instr, Retornar):
            usados.add(instr.valor)
        elif isinstance(instr, LlamarFuncion):
            if instr.dest:
                usados.add(instr.dest)

    resultado = []
    for instr in instrucciones:
        # Solo eliminar temporales (t0, t1...) nunca usados
        if isinstance(instr, (Binaria, Asignar)):
            dest = instr.dest
            es_temp = dest.startswith('t') and dest[1:].isdigit()
            if es_temp and dest not in usados:
                continue   # instruccion muerta, se descarta
        resultado.append(instr)

    return resultado


# ----------------------------------------------------------
#  VALIDACION DEL CODIGO GENERADO
# ----------------------------------------------------------

def validar_tac(instrucciones):
    """
    Verifica que:
    1. Toda variable/temporal usada haya sido definida antes.
    2. Todo salto apunte a una etiqueta existente.
    Devuelve lista de errores encontrados.
    """
    definidos = set()
    etiquetas = set()
    saltos    = []
    errores   = []

    # Primera pasada: recopilar etiquetas definidas
    for instr in instrucciones:
        if isinstance(instr, Etiqueta):
            etiquetas.add(instr.nombre)

    # Recopilar parametros declarados en funciones del AST
    # Como el TAC no los emite explicitamente, los inferimos
    # buscando el patron: InicioFuncion seguido de uso de variables
    # que no son temporales ni fueron asignadas -> son parametros
    params_funcion = set()
    for i, instr in enumerate(instrucciones):
        if isinstance(instr, InicioFuncion):
            # Las variables usadas en binarias antes de cualquier
            # asignacion dentro de la funcion son parametros
            j = i + 1
            definidos_local = set()
            while j < len(instrucciones) and not isinstance(instrucciones[j], FinFuncion):
                sub = instrucciones[j]
                if isinstance(sub, Asignar):
                    definidos_local.add(sub.dest)
                elif isinstance(sub, Binaria):
                    for op in (sub.izq, sub.der):
                        if (not es_constante(op) and
                                op not in definidos_local and
                                not op.startswith('t')):
                            params_funcion.add(op)
                j += 1

    # Segunda pasada: verificar usos
    for i, instr in enumerate(instrucciones):

        if isinstance(instr, Asignar):
            # El src debe estar definido o ser constante
            if not es_constante(instr.src) and instr.src not in definidos:
                errores.append(
                    f"Variable '{instr.src}' usada antes de ser definida "
                    f"(instruccion {i+1})"
                )
            definidos.add(instr.dest)

        elif isinstance(instr, Binaria):
            for operando in (instr.izq, instr.der):
                if not es_constante(operando) and operando not in definidos:
                    errores.append(
                        f"Variable '{operando}' usada antes de ser definida "
                        f"(instruccion {i+1})"
                    )
            definidos.add(instr.dest)

        elif isinstance(instr, SaltoCondicional):
            if instr.etiqueta not in etiquetas:
                errores.append(
                    f"Salto a etiqueta '{instr.etiqueta}' no definida "
                    f"(instruccion {i+1})"
                )

        elif isinstance(instr, SaltoIncondicional):
            if instr.etiqueta not in etiquetas:
                errores.append(
                    f"Salto a etiqueta '{instr.etiqueta}' no definida "
                    f"(instruccion {i+1})"
                )

        elif isinstance(instr, Parametro):
            if not es_constante(instr.valor) and instr.valor not in definidos:
                errores.append(
                    f"Parametro '{instr.valor}' no definido "
                    f"(instruccion {i+1})"
                )

        elif isinstance(instr, Imprimir):
            if not es_constante(instr.valor) and instr.valor not in definidos:
                errores.append(
                    f"Variable '{instr.valor}' en print no definida "
                    f"(instruccion {i+1})"
                )

        elif isinstance(instr, LlamarFuncion):
            if instr.dest:
                definidos.add(instr.dest)

        elif isinstance(instr, InicioFuncion):
            definidos = set(params_funcion)

        elif isinstance(instr, FinFuncion):
            pass  # no hace nada, solo marca fin

    return errores


def mostrar_validacion(errores):
    print("\nValidacion del codigo generado:")
    print("=" * 55)
    if errores:
        print(f"  Se encontraron {len(errores)} problema(s):")
        for e in errores:
            print(f"  [!] {e}")
    else:
        print("  Codigo generado validado correctamente.")


# --------------------------------------------------
#  MAIN
# --------------------------------------------------

def main():
    if len(sys.argv) < 2:
        print("Uso: python generador_tac.py <archivo.peka>")
        sys.exit(1)

    ruta = sys.argv[1]

    # 1. Leer archivo
    try:
        with open(ruta, 'r', encoding='utf-8') as f:
            codigo = f.read()
    except FileNotFoundError:
        print(f"Error: no se encontro el archivo '{ruta}'")
        sys.exit(1)

    # 2. Lexico
    lexer  = Lexer(codigo)
    tokens = lexer.tokenizar()
    if lexer.errores:
        print("Errores lexicos. Generacion abortada.")
        sys.exit(1)

    # 3. Sintactico
    p   = Parser(tokens)
    ast = p.parsear()
    if p.errores:
        print("Errores sintacticos. Generacion abortada.")
        sys.exit(1)

    # 4. Semantico
    sem = AnalizadorSemantico()
    sem.analizar(ast)
    if sem.errores:
        print("Errores semanticos. Generacion abortada.")
        for e in sem.errores:
            print(f"  {e}")
        sys.exit(1)

    # 5. Generar TAC
    gen = GeneradorTAC()
    gen.generar(ast)
    gen.mostrar()

    # 6. Propagar constantes
    optimizado = propagar_constantes(gen.instrucciones)
    mostrar_optimizado(optimizado)

    # 7. Eliminar codigo muerto
    sin_muertos = eliminar_codigo_muerto(optimizado)
    print("\nTAC tras eliminacion de codigo muerto:")
    print("=" * 55)
    for instr in sin_muertos:
        print(instr)

    # 8. Validar
    errores_tac = validar_tac(sin_muertos)
    mostrar_validacion(errores_tac)


if __name__ == "__main__":
    main()