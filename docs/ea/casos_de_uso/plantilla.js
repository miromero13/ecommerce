/* =====================================================================================================
 * FashionStore SaaS - Diagrama general de casos de uso (CU1-CU30) para Enterprise Architect 15
 *
 * Generado por docs/ea/casos_de_uso/generar.py (no editar a mano: cambie el .py y vuelva a generar).
 *
 * USO: en el Project Browser seleccione el paquete donde quiere el diagrama; Specialize > Tools > Scripting;
 *      clic derecho en un grupo > New JScript; pegue TODO este archivo; guarde y ejecute (Run).
 *
 * Crea el paquete "Casos de uso - FashionStore SaaS" con los 7 actores oficiales, los 30 casos de uso, sus
 * asociaciones, las relaciones include / extend, el diagrama general con el limite del sistema y un diagrama
 * por caso de uso (UML 2.5: <<include>> va del caso base al incluido; <<extend>> va de la extension al caso
 * que extiende). Cada subcaso es una operacion real del codigo; su endpoint o funcion queda en las notas.
 * Actores, casos de uso y diagrama viven en el MISMO paquete: asi EA no escribe "(from Paquete...)" debajo
 * de cada figura. Si el paquete ya existe (de una ejecucion anterior) lo borra y lo crea de nuevo.
 * ===================================================================================================== */

/*MODEL*/
var ROOT_NAME = "Casos de uso - FashionStore SaaS";
var MARKER = "[generado: FashionStore_casos_de_uso.js]";
var STEP = "inicio";

function log(msg) { Session.Output(msg); }
function has(obj, key) { return Object.prototype.hasOwnProperty.call(obj, key); }

function newElement(pkg, name, type, notes, alias) {
    STEP = "elemento " + name;
    var e = pkg.Elements.AddNew(name, type);
    if (notes) { e.Notes = notes; }
    if (alias) { e.Alias = alias; }
    if (!e.Update()) { throw new Error("No se pudo crear " + name + ": " + e.GetLastError()); }
    return e;
}

function place(d, el, left, top, width, height) {
    var o = d.DiagramObjects.AddNew("l=" + left + ";r=" + (left + width) + ";t=" + top + ";b=" + (top + height) + ";", "");
    o.ElementID = el.ElementID;
    o.Style = "NSL=0;";
    o.Sequence = 1 + Math.floor((width * height) / 100);  /* lo mas grande (limite del sistema) queda detras */
    o.Update();
    return o;
}

function associate(actor, uc) {
    STEP = "asociacion " + actor.Name + " - " + uc.Name;
    var c = actor.Connectors.AddNew("", "Association");
    c.SupplierID = uc.ElementID;
    if (!c.Update()) { throw new Error("No se pudo crear " + STEP + ": " + c.GetLastError()); }
    return c;
}

function relate(from, to, kind) {
    STEP = kind + " " + from.Name + " -> " + to.Name;
    var c = from.Connectors.AddNew("", "UseCase");
    c.SupplierID = to.ElementID;
    c.Subtype = kind === "include" ? "Includes" : "Extends";
    c.Stereotype = kind;
    c.Direction = "Source -> Destination";
    if (!c.Update()) { throw new Error("No se pudo crear " + STEP + ": " + c.GetLastError()); }
    return c;
}

function run() {
    var parent = Repository.GetTreeSelectedPackage();
    if (parent === null || parent === undefined) {
        Session.Prompt("Seleccione en el Project Browser el paquete donde crear el diagrama y vuelva a ejecutar.", 1);
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
    STEP = "paquete";
    var pkg = parent.Packages.AddNew(ROOT_NAME, "");
    pkg.Notes = "Actores oficiales y los 30 casos de uso de FashionStore SaaS. " + MARKER;
    pkg.Update();
    parent.Packages.Refresh();

    var EL = {};
    var CONN = {};  /* "desde|hacia" -> conector, para dibujar los quiebres */
    for (k in MODEL.actors) {
        if (has(MODEL.actors, k)) { EL[k] = newElement(pkg, MODEL.actors[k], "Actor", "", ""); }
    }
    for (i = 0; i < MODEL.cases.length; i++) {
        var c = MODEL.cases[i];
        EL[c.id] = newElement(pkg, c.id + " - " + c.name, "UseCase", c.notes, c.id);
        for (j = 0; j < c.actors.length; j++) { CONN[c.actors[j] + "|" + c.id] = associate(EL[c.actors[j]], EL[c.id]); }
    }
    for (i = 0; i < MODEL.relations.length; i++) {
        var r = MODEL.relations[i];
        CONN[r.from + "|" + r.to] = relate(EL[r.from], EL[r.to], r.kind);
    }

    STEP = "diagrama general";
    for (i = 0; i < MODEL.subs.length; i++) {
        var sb = MODEL.subs[i];
        EL[sb.key] = newElement(pkg, sb.name, "UseCase", sb.notes, "");
    }
    for (i = 0; i < MODEL.subLinks.length; i++) {
        var sl = MODEL.subLinks[i];
        relate(EL[sl.from], EL[sl.to], sl.kind);
    }

    var d = pkg.Diagrams.AddNew("Diagrama general de casos de uso - FashionStore SaaS", "Use Case");
    d.Notes = "Los 30 casos de uso con sus actores y relaciones include / extend. " + MARKER;
    if (!d.Update()) { throw new Error("No se pudo crear el diagrama: " + d.GetLastError()); }
    pkg.Diagrams.Refresh();
    var system = newElement(pkg, "FashionStore SaaS", "Boundary", "Limite del sistema", "");
    var B = MODEL.boundary;
    place(d, system, B[0], B[1], B[2], B[3]);
    for (k in MODEL.layout) {
        if (!has(MODEL.layout, k)) { continue; }
        var p = MODEL.layout[k];
        var size = has(MODEL.actors, k) ? MODEL.act : MODEL.uc;
        place(d, EL[k], p[0], p[1], size[0], size[1]);
    }
    d.Update();
    /* las lineas que chocarian con otro caso de uso pasan por el hueco libre entre dos figuras */
    for (i = 0; i < MODEL.routes.length; i++) {
        var rt = MODEL.routes[i];
        STEP = "quiebre " + rt.from + " - " + rt.to;
        var link = d.DiagramLinks.AddNew("", "");
        link.ConnectorID = CONN[rt.from + "|" + rt.to].ConnectorID;
        link.LineStyle = 3;
        var path = "";
        for (j = 0; j < rt.path.length; j++) { path += rt.path[j][0] + ":" + (-rt.path[j][1]) + ";"; }
        link.Path = path;
        if (!link.Update()) { throw new Error("No se pudo trazar " + STEP + ": " + link.GetLastError()); }
    }
    d.DiagramLinks.Refresh();
    d.Update();
    Repository.SaveDiagram(d.DiagramID);

    /* un diagrama por caso de uso: sus actores, el caso base y sus extensiones / inclusiones */
    for (i = 0; i < MODEL.diagrams.length; i++) {
        var dg = MODEL.diagrams[i];
        var base = EL[dg.cu];
        STEP = "diagrama " + base.Name;
        var cd = pkg.Diagrams.AddNew(base.Name, "Use Case");
        cd.Notes = base.Notes + " " + MARKER;
        if (!cd.Update()) { throw new Error("No se pudo crear el diagrama " + base.Name + ": " + cd.GetLastError()); }
        pkg.Diagrams.Refresh();
        for (k in dg.layout) {
            if (!has(dg.layout, k)) { continue; }
            var q = dg.layout[k];
            var sz = has(MODEL.actors, k) ? MODEL.act : MODEL.uc;
            place(cd, EL[k], q[0], q[1], sz[0], sz[1]);
        }
        for (j = 0; j < dg.hide.length; j++) {
            var hl = cd.DiagramLinks.AddNew("", "");
            hl.ConnectorID = CONN[dg.hide[j]].ConnectorID;
            hl.IsHidden = true;
            hl.Update();
        }
        cd.Update();
        Repository.SaveDiagram(cd.DiagramID);
    }
    Repository.RefreshModelView(parent.PackageID);
    Repository.OpenDiagram(d.DiagramID);
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
    log("FashionStore - generando el diagrama general de casos de uso...");
    Repository.EnableUIUpdates = false;
    var ok = false;
    try {
        ok = run();
    } catch (e) {
        log("[ERROR] " + (e.message || e.description || e) + " | paso: " + STEP);
    }
    Repository.EnableUIUpdates = true;
    if (ok) {
        log("[OK] Diagrama general y " + MODEL.diagrams.length + " diagramas por caso de uso creados en '" + ROOT_NAME + "'.");
        Session.Prompt("Diagramas de casos de uso generados correctamente.", 1);
    }
}

if (typeof Repository !== "undefined") { main(); }
