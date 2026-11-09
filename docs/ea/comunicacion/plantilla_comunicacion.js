/* =====================================================================================================
 * FashionStore SaaS - Diagramas de comunicacion (ICONIX / UML 2.5) por caso de uso (CU1-CU30), EA 15
 *
 * Generado por docs/ea/comunicacion/generar_comunicacion.py (no editar a mano: cambie el .py y vuelva a generar).
 *
 * USO: en el Project Browser seleccione el paquete donde quiere los diagramas; Specialize > Tools > Scripting;
 *      clic derecho en un grupo > New JScript; pegue TODO este archivo; guarde y ejecute (Run).
 *
 * Cada mensaje sale del codigo: actor -> interfaz (metodo del componente Angular), interfaz -> control (ruta
 * FastAPI o servicio del frontend), control -> entidad (funcion de servicio que crea o consulta la entidad).
 * Una entidad nunca llama a otra. Numeracion 1, 1.1, 1.2 ... como en la referencia.
 * Cada caso de uso va en su propio paquete con sus objetos (sin "(from ...)"); HighlightImports = false.
 * Si el paquete ya existe (de una ejecucion anterior) lo borra y lo crea de nuevo.
 * ===================================================================================================== */

/*MODEL*/
var ROOT_NAME = "Diagramas de comunicacion - FashionStore SaaS";
var MARKER = "[generado: FashionStore_comunicacion.js]";
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
    var root = newPackage(parent, ROOT_NAME, "Diagramas de comunicacion generados desde el codigo. " + MARKER);
    var clsPkg = newPackage(root, "Clases de analisis", "Interfaces (boundary), controles (control) y entidades (entity).");

    var CLS = {};
    for (i = 0; i < MODEL.classifiers.length; i++) {
        var c = MODEL.classifiers[i];
        CLS[c.kind + ":" + c.name] = newElement(clsPkg, c.name, "Class", c.kind);
    }

    for (i = 0; i < MODEL.diagrams.length; i++) {
        var dg = MODEL.diagrams[i];
        var pkg = newPackage(root, dg.cu, "Comunicacion " + dg.cu);
        STEP = "diagrama " + dg.cu;
        var d = pkg.Diagrams.AddNew(dg.cu + " - Diagrama de comunicacion", "Collaboration");
        d.Notes = "Mensajes trazados desde el codigo. " + MARKER;
        if (!d.Update()) { throw new Error("No se pudo crear el diagrama " + dg.cu + ": " + d.GetLastError()); }
        pkg.Diagrams.Refresh();
        d.HighlightImports = false;
        d.Update();

        /* texto vacio en la esquina superior: EA ajusta el marco a los objetos, no a las etiquetas apiladas;
           asi el marco empieza arriba y ninguna etiqueta queda cortada */
        var anchor = pkg.Elements.AddNew("", "Text");
        anchor.Notes = " ";             /* con contenido EA no dibuja el recuadro punteado del texto vacio */
        anchor.Update();
        place(d, anchor, 10, 5, 10, 10);
        var OBJ = {};
        var bottom = 0;
        for (k in dg.objs) {
            if (!has(dg.objs, k)) { continue; }
            var o = dg.objs[k];
            var p = dg.pos[k];
            var el;
            if (o.kind === "actor") {
                el = newElement(pkg, o.name, "Actor", "");
                place(d, el, p[0], p[1], 50, 90);
            } else {
                el = newElement(pkg, "", "Object", o.kind);
                el.ClassifierID = CLS[o.kind + ":" + o.name].ElementID;
                el.Update();
                place(d, el, p[0], p[1], 90, 70);
            }
            OBJ[k] = el;
            bottom = Math.max(bottom, p[1] + (o.kind === "actor" ? 90 : 70));
        }
        /* el mismo texto vacio debajo del objeto mas bajo: el nombre de ese objeto (bajo su figura) queda dentro del marco */
        var anchorBottom = pkg.Elements.AddNew("", "Text");
        anchorBottom.Notes = " ";
        anchorBottom.Update();
        place(d, anchorBottom, 10, bottom + 30, 10, 10);
        for (j = 0; j < dg.links.length; j++) {
            STEP = "enlace " + dg.links[j][0] + " - " + dg.links[j][1] + " en " + dg.cu;
            var a = OBJ[dg.links[j][0]], b = OBJ[dg.links[j][1]];
            if (a.ElementID === b.ElementID) { continue; }
            var lk = a.Connectors.AddNew("", "Association");
            lk.SupplierID = b.ElementID;
            if (!lk.Update()) { throw new Error("No se pudo crear " + STEP + ": " + lk.GetLastError()); }
        }
        /* un conector de colaboracion por mensaje, con su numero; varios mensajes sobre el mismo enlace se
           apilan desplazando la etiqueta (SY en PDATA5, comprobado en EA 15) */
        var stack = {};
        for (j = 0; j < dg.msgs.length; j++) {
            var m = dg.msgs[j];
            STEP = "mensaje " + m.num + " en " + dg.cu;
            var key = m.from < m.to ? m.from + "|" + m.to : m.to + "|" + m.from;
            var level = has(stack, key) ? stack[key] + 1 : 0;
            stack[key] = level;
            var con = OBJ[m.from].Connectors.AddNew(m.label, "Collaboration");
            con.SupplierID = OBJ[m.to].ElementID;
            con.DiagramID = d.DiagramID;
            con.SequenceNo = j + 1;
            con.Direction = "Source -> Destination";
            if (!con.Update()) { throw new Error("No se pudo crear " + STEP + ": " + con.GetLastError()); }
            /* desplazamiento de la etiqueta calculado por el generador segun la inclinacion de la linea */
            Repository.Execute("UPDATE t_connector SET PDATA4='" + m.num + "', PDATA5='SX=" + m.sx + ";SY=" + m.sy +
                ";EX=" + m.sx + ";EY=" + m.sy + ";EDGE=2;' WHERE Connector_ID=" + con.ConnectorID);
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
    log("FashionStore - generando los diagramas de comunicacion...");
    Repository.EnableUIUpdates = false;
    var ok = false;
    try {
        ok = run();
    } catch (e) {
        log("[ERROR] " + (e.message || e.description || e) + " | paso: " + STEP);
    }
    Repository.EnableUIUpdates = true;
    if (ok) {
        log("[OK] " + MODEL.diagrams.length + " diagramas de comunicacion creados en '" + ROOT_NAME + "'.");
        Session.Prompt("Diagramas de comunicacion generados correctamente.", 1);
    }
}

if (typeof Repository !== "undefined") { main(); }
