/* =====================================================================================================
 * FashionStore SaaS - Diagramas de secuencia (ICONIX / UML 2.5) por caso de uso (CU1-CU30), EA 15
 *
 * Generado por docs/ea/secuencia/generar_secuencia.py (no editar a mano: cambie el .py y vuelva a generar).
 *
 * USO: en el Project Browser seleccione el paquete donde quiere los diagramas; Specialize > Tools > Scripting;
 *      clic derecho en un grupo > New JScript; pegue TODO este archivo; guarde y ejecute (Run).
 *
 * Lineas de vida: actor, interfaz (boundary), control y entidad. Cada mensaje es un metodo real del codigo; los
 * retornos (punteados) muestran el tipo de retorno declarado en el codigo. Una entidad nunca llama a otra.
 * Fragmentos solo donde el codigo tiene la estructura, con su condicion literal como guarda:
 *   alt / opt (if / else)  -> desde la interfaz hasta la ultima entidad
 *   loop (for / while)     -> desde el control hasta la ultima entidad
 * Si el paquete ya existe (de una ejecucion anterior) lo borra y lo crea de nuevo.
 * ===================================================================================================== */

/*MODEL*/
var ROOT_NAME = "Diagramas de secuencia - FashionStore SaaS";
var MARKER = "[generado: FashionStore_secuencia.js]";
var ACTORES = { "SA": "Superadministrador", "AD": "Administrador del tenant", "EN": "Encargado de sucursal",
                "PR": "Proveedor", "CL": "Cliente", "CA": "Cajero", "RE": "Repartidor" };
var TOP = 50;          /* borde superior de las lineas de vida */
var STEP = "inicio";

function log(msg) { Session.Output(msg); }
function has(obj, key) { return Object.prototype.hasOwnProperty.call(obj, key); }

function newPackage(parent, name, notes) {
    STEP = "paquete " + name;
    var p = parent.Packages.AddNew(name, "");
    p.Notes = notes || "";
    p.Update();
    parent.Packages.Refresh();
    return p;
}

function newElement(pkg, name, type, stereotype) {
    STEP = "elemento " + name;
    var e = pkg.Elements.AddNew(name, type);
    if (stereotype) { e.Stereotype = stereotype; }
    if (!e.Update()) { throw new Error("No se pudo crear " + name + ": " + e.GetLastError()); }
    return e;
}

function place(d, el, x, y, w, h) {
    var o = d.DiagramObjects.AddNew("l=" + x + ";r=" + (x + w) + ";t=" + y + ";b=" + (y + h) + ";", "");
    o.ElementID = el.ElementID;
    o.Update();
    return o;
}

function run() {
    var parent = Repository.GetTreeSelectedPackage();
    if (parent === null || parent === undefined) {
        Session.Prompt("Seleccione en el Project Browser el paquete donde crear los diagramas y vuelva a ejecutar.", 1);
        return false;
    }
    var i, j, k;
    for (i = 0; i < parent.Packages.Count; i++) {
        var old = parent.Packages.GetAt(i);
        if (old.Name !== ROOT_NAME) { continue; }
        if (old.Notes.indexOf(MARKER) < 0) {
            throw new Error("Ya existe un paquete '" + ROOT_NAME + "' que NO creo este script: renombrelo y vuelva a ejecutar.");
        }
        parent.Packages.DeleteAt(i, false);
        parent.Packages.Refresh();
        log("Paquete anterior eliminado; se crea de nuevo.");
        break;
    }
    var root = newPackage(parent, ROOT_NAME, "Diagramas de secuencia generados desde el codigo. " + MARKER);
    var clsPkg = newPackage(root, "Clases de analisis", "Interfaces (boundary), controles (control) y entidades (entity).");
    var CLS = {};
    for (i = 0; i < MODEL.classifiers.length; i++) {
        var c = MODEL.classifiers[i];
        CLS[c.kind + ":" + c.name] = newElement(clsPkg, c.name, "Class", c.kind);
    }

    for (i = 0; i < MODEL.diagrams.length; i++) {
        var dg = MODEL.diagrams[i];
        var pkg = newPackage(root, dg.cu, "Secuencia " + dg.cu);
        STEP = "diagrama " + dg.cu;
        var d = pkg.Diagrams.AddNew(dg.cu + " - Diagrama de secuencia", "Sequence");
        d.Notes = "Mensajes trazados desde el codigo. " + MARKER;
        if (!d.Update()) { throw new Error("No se pudo crear el diagrama " + dg.cu + ": " + d.GetLastError()); }
        pkg.Diagrams.Refresh();
        d.HighlightImports = false;
        d.Update();

        /* lineas de vida */
        var LIFE = {}, X = {};
        for (j = 0; j < dg.lifelines.length; j++) {
            var id = dg.lifelines[j];
            var o = dg.objs[id];
            var xw = dg.xs[id];
            var el;
            if (o.kind === "actor") {
                el = newElement(pkg, o.name, "Actor", "");
            } else {
                el = newElement(pkg, "", "Sequence", o.kind);
                el.ClassifierID = CLS[o.kind + ":" + o.name].ElementID;
                el.Update();
            }
            LIFE[id] = el;
            X[id] = { l: xw[0], r: xw[0] + xw[1] };
            place(d, el, xw[0], TOP, xw[1], dg.fin);
        }

        /* mensajes, en orden (EA los coloca uno debajo del otro). Llamada sincrona; el retorno lleva el numero de
           la llamada que responde y su valor devuelto ("1.2: list_plans(only_active):list[SubscriptionPlan]") */
        for (j = 0; j < dg.msgs.length; j++) {
            var m = dg.msgs[j];
            STEP = "mensaje " + (m.num || "retorno") + " en " + dg.cu;
            /* retorno (UML 2.5): "numero: operacion(argumentos)" de la llamada que responde; EA agrega ":valor devuelto" */
            var con = LIFE[m.from].Connectors.AddNew(m.ret ? m.num + ": " + m.op : (m.num ? m.num + ": " + m.label : m.label), "Sequence");
            con.SupplierID = LIFE[m.to].ElementID;
            con.DiagramID = d.DiagramID;
            con.SequenceNo = j + 1;
            if (!con.Update()) { throw new Error("No se pudo crear " + STEP + ": " + con.GetLastError()); }
            Repository.Execute("UPDATE t_connector SET PtStartY=" + (-dg.ys[j]) + ", PtEndY=" + (-dg.ys[j]) +
                ", PDATA1='Synchronous', PDATA2='retval=" + (m.ret ? m.label.replace(/'/g, "''") : "void") +
                ";', PDATA4='" + (m.ret ? "1" : "0") + "' WHERE Connector_ID=" + con.ConnectorID);
        }

        /* fragmentos (rectangulos calculados por el generador sobre las alturas de EA):
           alt / opt desde la interfaz, loop desde el control; todos hasta la ultima entidad */
        for (j = 0; j < dg.frames.length; j++) {
            var f = dg.frames[j];
            STEP = f.kind + " en " + dg.cu;
            var rc = f.rect;
            var frag = newElement(pkg, "", "InteractionFragment", "");
            frag.Subtype = f.kind === "alt" ? 0 : (f.kind === "opt" ? 1 : 4);
            frag.Update();
            var cortes = [rc[1]].concat(f.seps).concat([rc[3]]);
            for (k = 0; k < f.operands.length; k++) {
                var part = frag.Partitions.AddNew(f.operands[k].guard, "");
                part.Size = cortes[k + 1] - cortes[k];
            }
            frag.Update();
            frag.Partitions.Refresh();
            place(d, frag, rc[0], rc[1], rc[2] - rc[0], rc[3] - rc[1]);
        }
        d.Update();
        Repository.SaveDiagram(d.DiagramID);
    }
    Repository.RefreshModelView(parent.PackageID);
    return true;
}

function main() {
    Repository.EnsureOutputVisible("Script");
    Repository.ClearOutput("Script");
    if (typeof ScriptEngine === "undefined") {
        var msg = "Este script debe crearse como JScript, no como JavaScript: clic derecho en el grupo > New JScript.";
        log("[ERROR] " + msg);
        Session.Prompt(msg, 1);
        return;
    }
    log("FashionStore - generando los diagramas de secuencia...");
    Repository.EnableUIUpdates = false;
    var ok = false;
    try {
        ok = run();
    } catch (e) {
        log("[ERROR] " + (e.message || e.description || e) + " | paso: " + STEP);
    }
    Repository.EnableUIUpdates = true;
    if (ok) {
        log("[OK] " + MODEL.diagrams.length + " diagramas de secuencia creados en '" + ROOT_NAME + "'.");
        Session.Prompt("Diagramas de secuencia generados correctamente.", 1);
    }
}

if (typeof Repository !== "undefined") { main(); }
