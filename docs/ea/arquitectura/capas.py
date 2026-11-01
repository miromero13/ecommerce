"""Dibujo por filas (Vista / Control / Modelo / Conexión) con el menor número de cruces de líneas.

Cada componente va en su fila; las líneas son ortogonales: salen por el lado inferior o superior de la caja,
bajan o suben hasta un carril horizontal propio en el espacio entre dos filas y llegan a la otra caja.
Una línea que salta filas pasa por un hueco reservado entre las cajas de la fila intermedia.
Dos componentes de la misma fila que se llaman (p. ej. OfflineSyncService -> OfflineQueueService) quedan uno al
lado del otro y se unen con una línea horizontal recta.

El orden de las cajas de cada fila y el orden de los carriles se eligen para reducir los cruces:
baricentros (Sugiyama) y luego intercambios de vecinos mientras bajen los cruces.
"""
import random
import time
from itertools import combinations

ALTO, GAP, GAP_HUECO, GAP_PAR = 64, 28, 22, 60     # alto de caja, separación entre cajas, hueco, par de la fila
CARRIL, MARGEN_CANAL, Y0, X0 = 10, 30, 50, 40


def ancho(nombre):
    return max(160, round(len(nombre) * 5.9) + 44)      # EA dibuja unos 5,3 px por letra en negrita


class Capas:
    def __init__(self, filas, aristas, ancho_min=None):
        """filas: lista de listas de (id, nombre, estereotipo, alineado).
        aristas: (cliente, proveedor): la flecha va del cliente al proveedor (p. ej. control -> vista)."""
        self.nodo = {}
        for i, fila in enumerate(filas):
            for nid, nombre, st, alineado in fila:
                self.nodo[nid] = {"id": nid, "name": nombre, "st": st, "fila": i, "w": ancho(nombre),
                                  "alineado": alineado, "falso": False}
        self.n_filas = len(filas)
        self.aristas = list(aristas)
        self.pares = []                  # aristas dentro de una misma fila
        self.tramos = []                 # (arriba, abajo, indice_arista) entre filas consecutivas
        self.cadena = {}                 # arista -> nodos de arriba hacia abajo (con huecos)
        for k, (a, b) in enumerate(self.aristas):
            fa, fb = self.nodo[a]["fila"], self.nodo[b]["fila"]
            if fa == fb:
                self.pares.append((a, b))
                continue
            arriba, abajo = (a, b) if fa < fb else (b, a)
            cad = [arriba]
            for f in range(min(fa, fb) + 1, max(fa, fb)):
                hid = f"_h{k}_{f}"
                self.nodo[hid] = {"id": hid, "name": "", "st": "", "fila": f, "w": 0, "alineado": False, "falso": True}
                cad.append(hid)
            cad.append(abajo)
            self.cadena[k] = cad
            for u, v in zip(cad, cad[1:]):
                self.tramos.append((u, v, k))
        # unidades: un par de la misma fila se mueve junto
        self.orden = []
        for i in range(self.n_filas):
            ids = [n for n, d in self.nodo.items() if d["fila"] == i]
            unidades, usados = [], set()
            for a, b in self.pares:
                if self.nodo[a]["fila"] == i:
                    assert a not in usados and b not in usados, "un componente con dos pares en la fila"
                    unidades.append([a, b]); usados |= {a, b}
            unidades += [[n] for n in ids if n not in usados]
            self.orden.append(unidades)
        for u, v in self.pares:
            self.nodo[u]["w"] = self.nodo[v]["w"] = max(self.nodo[u]["w"], self.nodo[v]["w"])
        self._grado = {}
        for u, v, _ in self.tramos:
            self._grado[u] = self._grado.get(u, 0) + 1
            self._grado[v] = self._grado.get(v, 0) + 1
        puertos = {}
        for u, v, _ in self.tramos:
            puertos[(u, "B")] = puertos.get((u, "B"), 0) + 1
            puertos[(v, "T")] = puertos.get((v, "T"), 0) + 1
        for (n, _), c in puertos.items():
            if not self.nodo[n]["falso"]:
                self.nodo[n]["w"] = max(self.nodo[n]["w"], 16 * (c + 1))
        self.ancho_min = ancho_min

    # ------------------------------------------------------------------ posiciones
    def _sep(self, prev, n, mismo_par):
        if mismo_par:
            return GAP_PAR
        return GAP_HUECO if self.nodo[n]["falso"] or self.nodo[prev]["falso"] else GAP

    def _colocar(self, unidades, deseado, w):
        """x de una fila: cada unidad lo más cerca posible de su centro deseado, sin encimarse."""
        bloques = []                      # (unidad, ancho del bloque, desplazamientos internos)
        for u in unidades:
            off, cur = [], 0
            for j, n in enumerate(u):
                if j:
                    cur += GAP_PAR
                off.append(cur)
                cur += w[n]
            bloques.append((u, cur, off))
        # Regresión isotónica (PAVA): bloque i en izq_i = y_i + desplazamiento_i con y no decreciente, de modo
        # que ningún bloque se encima con el anterior, minimizando sum(peso * (izq - ideal)^2).
        desp, objetivo, peso, acum, prev_n = [], [], [], 0.0, None
        for u, ancho_b, _ in bloques:
            if prev_n is not None:
                acum += self._sep(prev_n, u[0], False)
            ideal = sum(deseado[n] for n in u) / len(u) - ancho_b / 2
            desp.append(acum)
            objetivo.append(ideal - acum)
            peso.append(1 + sum(self._grado.get(n, 0) for n in u))
            acum += ancho_b
            prev_n = u[-1]
        grupos = []                       # [valor, peso, cantidad]
        for t, p in zip(objetivo, peso):
            grupos.append([t, p, 1])
            while len(grupos) > 1 and grupos[-2][0] > grupos[-1][0]:
                v2, p2, c2 = grupos.pop()
                v1, p1, c1 = grupos.pop()
                grupos.append([(v1 * p1 + v2 * p2) / (p1 + p2), p1 + p2, c1 + c2])
        ys = [v for v, _, c in grupos for _ in range(c)]
        x = {}
        for y, dsp, (u, _, off) in zip(ys, desp, bloques):
            for n, o in zip(u, off):
                x[n] = y + dsp + o
        return x

    def _x(self, orden):
        w = {n: d["w"] for n, d in self.nodo.items()}
        arriba, abajo = {n: [] for n in self.nodo}, {n: [] for n in self.nodo}
        for u, v, _ in self.tramos:
            abajo[u].append(v)
            arriba[v].append(u)
        x = {}
        # fila 0 centrada; luego cada fila se acerca a sus vecinos de arriba, y se repite hacia arriba y hacia abajo
        cur = X0
        for u in orden[0]:
            for n in u:
                x[n] = cur
                cur += w[n] + GAP
        centro = lambda n: x[n] + w[n] / 2
        for pasada in range(3):
            filas = list(range(1, self.n_filas)) if pasada % 2 == 0 else list(range(self.n_filas - 2, -1, -1))
            for f in filas:
                vec = arriba if pasada % 2 == 0 else abajo
                deseado = {}
                for unidad in orden[f]:
                    for n in unidad:
                        cs = [centro(m) for m in vec[n] if m in x]
                        if self.nodo[n]["alineado"]:          # caja ancha justo debajo de lo que conecta
                            todos = [centro(m) for m in arriba[n] + abajo[n] if m in x]
                            if todos:
                                w[n] = max(self.nodo[n]["w"], max(todos) - min(todos) + 60)
                        deseado[n] = sum(cs) / len(cs) if cs else (centro(n) if n in x else X0)
                x.update(self._colocar(orden[f], deseado, w))
        # dos pasos por huecos (de líneas distintas) en filas vecinas nunca a la misma x: sus tramos se encimarían
        cadena_de = {n: k for k, cad in self.cadena.items() for n in cad if self.nodo[n]["falso"]}
        for f in range(1, self.n_filas):
            arriba_x = [(x[n], cadena_de[n]) for u in orden[f - 1] for n in u if n in cadena_de]
            for u in orden[f]:
                for n in u:
                    if n in cadena_de:
                        while any(abs(x[n] - xx) < 4 and k != cadena_de[n] for xx, k in arriba_x):
                            x[n] += 6
        x = {n: round(v) for n, v in x.items()}
        minimo = min(x.values())
        x = {n: v - minimo + X0 for n, v in x.items()}
        self._w = w
        total = max(x[n] + w[n] for n in x) - X0
        return x, total

    def _puertos(self, x):
        """x de cada extremo de tramo: repartidos en el lado de la caja, ordenados por la otra punta."""
        centro = {n: x[n] + self._w[n] / 2 for n in self.nodo}
        lados = {}
        for t, (u, v, _) in enumerate(self.tramos):
            # frente a una caja ancha (alineada) la línea sale del centro propio: la caja ancha se acomoda a ella
            lados.setdefault((u, "B"), []).append((centro[u] if self.nodo[v]["alineado"] else centro[v], t))
            lados.setdefault((v, "T"), []).append((centro[v] if self.nodo[u]["alineado"] else centro[u], t))
        px = {}
        # primero las cajas normales; después las anchas, que apuntan al puerto ya elegido en la otra punta
        for (n, lado), lista in sorted(lados.items(), key=lambda kv: self.nodo[kv[0][0]]["alineado"]):
            d = self.nodo[n]
            if d["alineado"]:
                otro_lado = "T" if lado == "B" else "B"
                lista = [(px.get((t, otro_lado), o), t) for o, t in lista]
            lista.sort()
            if d["falso"]:
                for _, t in lista:
                    px[(t, lado)] = centro[n]
                continue
            izq, der = x[n] + 8, x[n] + self._w[n] - 8
            # cada línea apunta a la otra punta (así quedan rectas las que pueden), con 12 px entre puertos
            xs = []
            for otro, _ in lista:
                xs.append(max(min(otro, der), izq if not xs else max(izq, xs[-1] + 12)))
            for i in range(len(xs) - 2, -1, -1):
                if xs[i + 1] > der:
                    xs[i + 1] = der
                xs[i] = min(xs[i], xs[i + 1] - 12)
            for (_, t), xx in zip(lista, xs):
                px[(t, lado)] = round(xx)
        # en un mismo canal, dos líneas distintas nunca bajan por la misma x (sus tramos se encimarían);
        # los pasos por huecos quedan fijos y se corren los puertos de las cajas
        for f in range(self.n_filas - 1):
            ts = [t for t, (u, _, _) in enumerate(self.tramos) if self.nodo[u]["fila"] == f]
            usados = []                                   # (x, tramo)
            extremos = []
            for t in ts:
                u, v, _ = self.tramos[t]
                for lado, n in (("B", u), ("T", v)):
                    if self.nodo[n]["falso"]:
                        usados.append((px[(t, lado)], t))
                    else:
                        extremos.append((t, lado))
            for t, lado in extremos:
                while any(abs(px[(t, lado)] - xx) < 4 and tt != t for xx, tt in usados):
                    px[(t, lado)] += 5
                usados.append((px[(t, lado)], t))
        return px

    @staticmethod
    def _costo(e, f):
        """Cruces si el carril de e queda encima del de f (e = (x_arriba, x_abajo))."""
        def dentro(xv, s):
            lo, hi = sorted(s)
            return lo < xv < hi
        return int(dentro(f[0], e)) + int(dentro(e[1], f))

    def _carriles(self, segs):
        """Orden de carriles de un canal (de arriba hacia abajo) y sus cruces."""
        rectos = [s for s in segs if s[1][0] == s[1][1]]
        quebrados = [s for s in segs if s[1][0] != s[1][1]]
        quebrados.sort(key=lambda s: (s[1][0] < s[1][1], s[1][0] if s[1][0] < s[1][1] else -s[1][0]))
        cambio = True
        while cambio:
            cambio = False
            for i in range(len(quebrados) - 1):
                e, f = quebrados[i][1], quebrados[i + 1][1]
                if self._costo(f, e) < self._costo(e, f):
                    quebrados[i], quebrados[i + 1] = quebrados[i + 1], quebrados[i]
                    cambio = True
        cruces = sum(self._costo(a[1], b[1]) for a, b in combinations(quebrados, 2))
        cruces += sum(1 for r in rectos for q in quebrados if min(q[1]) < r[1][0] < max(q[1]))
        return quebrados, cruces

    def _evaluar(self, orden):
        x, total = self._x(orden)
        px = self._puertos(x)
        cruces, largo, canales = 0, 0, {}
        for t, (u, v, _) in enumerate(self.tramos):
            canales.setdefault(self.nodo[u]["fila"], []).append((t, (px[(t, "B")], px[(t, "T")])))
            largo += abs(px[(t, "B")] - px[(t, "T")])
        pistas = {}
        for c, segs in canales.items():
            q, k = self._carriles(segs)
            pistas[c] = q
            cruces += k
        return cruces, largo, x, px, pistas, total

    # ------------------------------------------------------------------ orden
    def _baricentros(self, orden, vecinos):
        def pos():
            p = {}
            for unidades in orden:
                i = 0
                for u in unidades:
                    for n in u:
                        p[n] = i
                        i += 1
            return p

        mejor, mc = [list(map(list, f)) for f in orden], self._evaluar(orden)[:2]
        for barrido in range(8):
            p = pos()
            filas = range(1, self.n_filas) if barrido % 2 == 0 else range(self.n_filas - 2, -1, -1)
            lado = "up" if barrido % 2 == 0 else "down"
            for i in filas:
                def bari(u):
                    vs = [p[w] for n in u for w in vecinos[n][lado]]
                    return sum(vs) / len(vs) if vs else sum(p[n] for n in u) / len(u)
                orden[i].sort(key=bari)
                p = pos()
            c = self._evaluar(orden)[:2]
            if c < mc:
                mejor, mc = [list(map(list, f)) for f in orden], c
        return mejor, mc

    def _busqueda_local(self, orden, mc, limite):
        """Mueve cada unidad a la mejor posición de su fila (y da vuelta los pares) mientras bajen los cruces."""
        mejora = True
        while mejora and time.time() < limite:
            mejora = False
            for i in range(self.n_filas):
                fila = orden[i]
                for j in range(len(fila)):
                    u = fila.pop(j)
                    mejor_k, mejor_c = j, None
                    for k in range(len(fila) + 1):
                        fila.insert(k, u)
                        c = self._evaluar(orden)[:2]
                        fila.pop(k)
                        if mejor_c is None or c < mejor_c:
                            mejor_k, mejor_c = k, c
                    fila.insert(mejor_k, u)
                    if mejor_c < mc:
                        mc, mejora = mejor_c, True
                for u in fila:                        # el par también puede ir en el otro sentido
                    if len(u) == 2:
                        u.reverse()
                        c = self._evaluar(orden)[:2]
                        if c < mc:
                            mc, mejora = c, True
                        else:
                            u.reverse()
        return orden, mc

    def ordenar(self, segundos=None, arranques=40):
        """Baricentros y búsqueda local desde el orden dado y desde varios órdenes al azar (semilla fija,
        el resultado es siempre el mismo); se queda con el de menos cruces y, a igualdad, líneas más cortas."""
        vecinos = {n: {"up": [], "down": []} for n in self.nodo}
        for u, v, _ in self.tramos:
            vecinos[v]["up"].append(u)
            vecinos[u]["down"].append(v)
        azar = random.Random(2026)
        if segundos is None:            # más tiempo de búsqueda para los diagramas con más cajas
            segundos = 5 + 0.25 * sum(not d["falso"] for d in self.nodo.values())
        limite = time.time() + segundos
        mejor, mc = None, None
        for intento in range(arranques):
            orden = [list(map(list, f)) for f in self.orden]
            if intento:
                for f in orden:
                    azar.shuffle(f)
            orden, c = self._baricentros(orden, vecinos)
            orden, c = self._busqueda_local(orden, c, limite)
            if mc is None or c < mc:
                mejor, mc = orden, c
            if mc[0] == 0 or time.time() > limite:
                break
        self.orden = mejor
        return mc[0]

    # ------------------------------------------------------------------ dibujo
    def dibujar(self, d):
        cruces, _, x, px, pistas, total = self._evaluar(self.orden)
        y_fila, y = [], Y0
        for f in range(self.n_filas):
            y_fila.append(y)
            y += ALTO + 2 * MARGEN_CANAL + CARRIL * max(0, len(pistas.get(f, [])) - 1)
        y_carril = {}
        for f, q in pistas.items():
            for k, (t, _) in enumerate(q):
                y_carril[t] = y_fila[f] + ALTO + MARGEN_CANAL + CARRIL * k
        for n, nd in self.nodo.items():
            if not nd["falso"]:
                d.caja(n, "component", nd["name"], round(x[n]), y_fila[nd["fila"]], round(self._w[n]), ALTO, nd["st"])
        for t, (u, v, _) in enumerate(self.tramos):           # tramos rectos: sin carril
            if t not in y_carril:
                y_carril[t] = None
        for k, (a, b) in enumerate(self.aristas):
            if (a, b) in self.pares:
                xa, xb = x[a], x[b]
                yy = y_fila[self.nodo[a]["fila"]] + ALTO // 2
                pa = round(xa + self._w[a]) if xa < xb else round(xa)
                pb = round(xb) if xa < xb else round(xb + self._w[b])
                d.linea(a, b, "use", "", [(pa, yy), (pb, yy)])
                continue
            pts = []
            for u, v, kk in self.tramos:
                if kk != k:
                    continue
                t = self.tramos.index((u, v, kk))
                xu, xv = px[(t, "B")], px[(t, "T")]
                yu = y_fila[self.nodo[u]["fila"]] + (ALTO if not self.nodo[u]["falso"] else ALTO)
                yv = y_fila[self.nodo[v]["fila"]]
                if not pts:
                    pts.append((xu, y_fila[self.nodo[u]["fila"]] + ALTO))
                else:
                    pts.append((xu, yu))
                if xu != xv:
                    pts += [(xu, y_carril[t]), (xv, y_carril[t])]
                pts.append((xv, yv))
            limpio = [pts[0]]
            for p in pts[1:]:
                if p == limpio[-1]:
                    continue
                if len(limpio) >= 2 and (limpio[-2][0] == limpio[-1][0] == p[0] or limpio[-2][1] == limpio[-1][1] == p[1]):
                    limpio[-1] = p
                else:
                    limpio.append(p)
            if self.nodo[a]["fila"] > self.nodo[b]["fila"]:      # la flecha sale de la caja de abajo
                limpio.reverse()
            d.linea(a, b, "use", "", limpio)
        return cruces


def distribuir(filas, aristas, max_por_fila=12, segundos=None):
    """Capas ya ordenadas; una fila con más de max_por_fila cajas se reparte en sub-filas intercaladas
    (1.ª, 2.ª, 3.ª caja... en sub-filas distintas) para que el diagrama no quede demasiado ancho en la página.
    Primero se ordena con las filas completas; ese orden se reparte y se vuelve a optimizar."""
    previa = Capas(filas, aristas)
    total = segundos if segundos is not None else 5 + 0.25 * sum(len(f) for f in filas)
    previa.ordenar(segundos=total * 0.4)
    datos = {t[0]: t for f in filas for t in f}
    nuevas = []
    for i, fila in enumerate(filas):
        orden = [n for u in previa.orden[i] for n in u if not previa.nodo[n]["falso"]]
        partes = -(-len(orden) // max_por_fila)
        if partes <= 1 or previa.pares and any(previa.nodo[a]["fila"] == i for a, _ in previa.pares):
            nuevas.append([datos[n] for n in orden])
            continue
        for k in range(partes):
            nuevas.append([datos[n] for j, n in enumerate(orden) if j % partes == k])
    capas = Capas(nuevas, aristas)
    capas.ordenar(segundos=total * 0.6)
    return capas
