/* =====================================================================================================
 * FashionStore SaaS - Modelo de dominio por modulo (M1-M6) para Enterprise Architect 15
 *
 * Generado por docs/ea/modelo_dominio/generar_dominio.py (no editar a mano: cambie el .py y vuelva a generar).
 *
 * USO: en el Project Browser seleccione el paquete donde quiere el modelo; Specialize > Tools > Scripting;
 *      clic derecho en un grupo > New JScript; pegue TODO este archivo; guarde y ejecute (Run).
 *
 * Crea el paquete "Modelo de dominio - FashionStore SaaS" con:
 *   - subpaquete "Entidades": una clase por tabla real (nombre en espanol, atributos con su tipo y operaciones
 *     reales de los servicios que crean o consultan la tabla);
 *   - las relaciones de las claves foraneas: asociacion con multiplicidades y, cuando la FK es obligatoria y el
 *     codigo borra en cascada, composicion (rombo relleno del lado del todo); las tablas puente son M:N;
 *   - un diagrama por modulo con SOLO las tablas que intervienen en sus casos de uso.
 * Cada diagrama muestra solo el nombre de la clase (sin "Paquete::"): HighlightImports = false.
 * Las lineas siguen pasillos entre las clases: ninguna pasa por encima de una clase.
 * Si el paquete ya existe (de una ejecucion anterior) lo borra y lo crea de nuevo.
 * ===================================================================================================== */

/*MODEL*/
var ROOT_NAME = "Modelo de dominio - FashionStore SaaS";
var MARKER = "[generado: FashionStore_modelo_dominio.js]";
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

function newClass(pkg, c) {
    STEP = "clase " + c.name;
    var e = pkg.Elements.AddNew(c.name, "Class");
    e.Notes = c.notes;
    if (!e.Update()) { throw new Error("No se pudo crear " + c.name + ": " + e.GetLastError()); }
    var i, j;
    for (i = 0; i < c.attrs.length; i++) {
        var a = e.Attributes.AddNew(c.attrs[i].nombre, c.attrs[i].tipo);
        a.Visibility = "Private";
        a.Pos = i;
        a.Notes = "Columna: " + c.attrs[i].columna;
        a.Update();
    }
    for (i = 0; i < c.ops.length; i++) {
        var o = c.ops[i];
        var m = e.Methods.AddNew(o.nombre, "");
        m.Visibility = "Public";
        m.Pos = i;
        m.Notes = "Definida en " + o.archivo;
        m.Update();
        for (j = 0; j < o.params.length; j++) {
            var p = m.Parameters.AddNew(o.params[j], o.tipos[j] || "");
            p.Position = j;
            p.Update();
        }
        m.Parameters.Refresh();
        m.Update();
    }
    e.Attributes.Refresh();
    e.Methods.Refresh();
    return e;
}

function relate(EL, r) {
    STEP = "relacion " + r.key;
    var part = EL[r.hijo], whole = EL[r.padre];
    var c = part.Connectors.AddNew(r.nombre, r.composicion ? "Aggregation" : "Association");
    c.SupplierID = whole.ElementID;
    c.Direction = "Unspecified";
    c.ClientEnd.Cardinality = r.mult_hijo;
    c.SupplierEnd.Cardinality = r.mult_padre;
    if (r.composicion) { c.SupplierEnd.Aggregation = 2; }   /* rombo relleno del lado del todo */
    c.ClientEnd.Navigable = "Unspecified";
    c.SupplierEnd.Navigable = "Unspecified";
    c.Notes = "FK " + r.hijo + "." + r.columna + " -> " + r.padre;
    if (!c.Update()) { throw new Error("No se pudo crear " + STEP + ": " + c.GetLastError()); }
    c.ClientEnd.Update();
    c.SupplierEnd.Update();
    return c;
}

function place(d, el, b) {
    var o = d.DiagramObjects.AddNew("l=" + b[0] + ";r=" + (b[0] + b[2]) + ";t=" + b[1] + ";b=" + (b[1] + b[3]) + ";", "");
    o.ElementID = el.ElementID;
    o.Update();
}

function run() {
    var parent = Repository.GetTreeSelectedPackage();
    if (parent === null || parent === undefined) {
        Session.Prompt("Seleccione en el Project Browser el paquete donde crear el modelo y vuelva a ejecutar.", 1);
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
    var root = newPackage(parent, ROOT_NAME, "Modelo de dominio por modulo, generado desde el codigo. " + MARKER);
    var entities = newPackage(root, "Entidades", "Una clase por tabla real del sistema.");

    var EL = {};
    for (i = 0; i < MODEL.classes.length; i++) { EL[MODEL.classes[i].t] = newClass(entities, MODEL.classes[i]); }
    var CONN = {};
    for (i = 0; i < MODEL.relations.length; i++) { CONN[MODEL.relations[i].key] = relate(EL, MODEL.relations[i]); }

    for (i = 0; i < MODEL.diagrams.length; i++) {
        var dg = MODEL.diagrams[i];
        STEP = "diagrama " + dg.name;
        var d = root.Diagrams.AddNew(dg.name, "Logical");
        d.Notes = "Tablas que intervienen en los casos de uso del modulo " + dg.code + ". " + MARKER;
        d.ExtendedStyle = "OpParams=2;";        /* parametros como "nombre: tipo" */
        if (!d.Update()) { throw new Error("No se pudo crear " + dg.name + ": " + d.GetLastError()); }
        root.Diagrams.Refresh();
        d.HighlightImports = false;             /* sin el prefijo "Paquete::" en cada clase */
        d.Update();
        for (k in dg.boxes) {
            if (has(dg.boxes, k)) { place(d, EL[k], dg.boxes[k]); }
        }
        d.Update();
        d.DiagramLinks.Refresh();
        for (j = 0; j < dg.links.length; j++) {
            var lk = dg.links[j];
            STEP = "linea " + lk.key + " en " + dg.code;
            var link = d.DiagramLinks.AddNew("", "");
            link.ConnectorID = CONN[lk.key].ConnectorID;
            link.LineStyle = 3;
            var path = "";
            for (k = 0; k < lk.path.length; k++) { path += lk.path[k][0] + ":" + (-lk.path[k][1]) + ";"; }
            link.Path = path;
            link.Geometry = lk.geom;            /* punto exacto de conexion en cada clase */
            if (!link.Update()) { throw new Error("No se pudo trazar " + STEP + ": " + link.GetLastError()); }
        }
        d.DiagramLinks.Refresh();
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
    log("FashionStore - generando el modelo de dominio por modulo...");
    Repository.EnableUIUpdates = false;
    var ok = false;
    try {
        ok = run();
    } catch (e) {
        log("[ERROR] " + (e.message || e.description || e) + " | paso: " + STEP);
    }
    Repository.EnableUIUpdates = true;
    if (ok) {
        log("[OK] " + MODEL.diagrams.length + " diagramas de modelo de dominio creados en '" + ROOT_NAME + "'.");
        Session.Prompt("Modelo de dominio generado correctamente.", 1);
    }
}

if (typeof Repository !== "undefined") { main(); }
