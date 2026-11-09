/* =====================================================================================================
 * FashionStore SaaS - Diagrama de clases UML de toda la base de datos, para Enterprise Architect 15
 *
 * Generado por docs/ea/diagrama_clases/generar_clases.py (no editar a mano: cambie el .py y vuelva a generar).
 *
 * USO: en el Project Browser seleccione el paquete donde quiere el diagrama; Specialize > Tools > Scripting;
 *      clic derecho en un grupo > New JScript; pegue TODO este archivo; guarde y ejecute (Run).
 *
 * Crea el paquete "Diagrama de clases - FashionStore SaaS" con:
 *   - subpaquete "Clases": una clase por tabla real (mismo nombre en espanol que el modelo de dominio), con sus
 *     atributos (columnas y tipo) y sus operaciones (funciones reales de los servicios que trabajan sobre la tabla);
 *   - una relacion por clave foranea, con multiplicidades; composicion (rombo relleno del lado del todo) solo
 *     cuando la FK es obligatoria y el codigo borra en cascada; las tablas puente son asociaciones M:N;
 *   - un unico diagrama con todas las clases. Lineas ortogonales por pasillos: ninguna pasa sobre una clase.
 *     Para que se lea, no se dibujan (quedan ocultas, pero existen en el modelo) la linea hacia Empresa de las clases
 *     que tienen otras relaciones y las FK repetidas hacia una misma clase; una nota en el diagrama lo explica.
 * Cada clase muestra solo su nombre (sin "Paquete::"): HighlightImports = false.
 * Si el paquete ya existe (de una ejecucion anterior) lo borra y lo crea de nuevo.
 * ===================================================================================================== */

/*MODEL*/
var ROOT_NAME = "Diagrama de clases - FashionStore SaaS";
var MARKER = "[generado: FashionStore_diagrama_clases.js]";
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
        if (c.attrs[i].estereotipo) { a.StereotypeEx = c.attrs[i].estereotipo.replace(" ", ""); }   /* PK / FK */
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
    var root = newPackage(parent, ROOT_NAME, "Diagrama de clases de toda la base de datos, generado desde el codigo. " + MARKER);
    var entities = newPackage(root, "Clases", "Una clase por tabla real del sistema.");

    var EL = {};
    for (i = 0; i < MODEL.classes.length; i++) { EL[MODEL.classes[i].t] = newClass(entities, MODEL.classes[i]); }
    var CONN = {};
    for (i = 0; i < MODEL.relations.length; i++) { CONN[MODEL.relations[i].key] = relate(EL, MODEL.relations[i]); }

    var dg = MODEL.diagram;
    STEP = "diagrama " + dg.name;
    var d = root.Diagrams.AddNew(dg.name, "Logical");
    d.Notes = "Todas las tablas de la base de datos con sus relaciones. " + MARKER;
    d.ExtendedStyle = "OpParams=2;";            /* parametros como "nombre: tipo" */
    if (!d.Update()) { throw new Error("No se pudo crear " + dg.name + ": " + d.GetLastError()); }
    root.Diagrams.Refresh();
    d.HighlightImports = false;                 /* sin el prefijo "Paquete::" en cada clase */
    d.Update();
    for (k in dg.boxes) {
        if (has(dg.boxes, k)) { place(d, EL[k], dg.boxes[k]); }
    }
    d.Update();
    d.DiagramLinks.Refresh();
    for (j = 0; j < dg.links.length; j++) {
        var lk = dg.links[j];
        STEP = "linea " + lk.key;
        var link = d.DiagramLinks.AddNew("", "");
        link.ConnectorID = CONN[lk.key].ConnectorID;
        link.LineStyle = 3;
        var path = "";
        for (k = 0; k < lk.path.length; k++) { path += lk.path[k][0] + ":" + (-lk.path[k][1]) + ";"; }
        link.Path = path;
        link.Geometry = lk.geom;                /* punto exacto de conexion en cada clase */
        if (!link.Update()) { throw new Error("No se pudo trazar " + STEP + ": " + link.GetLastError()); }
    }
    /* relaciones del modelo que no se dibujan (lo explica la nota del diagrama) */
    for (j = 0; j < dg.hidden.length; j++) {
        STEP = "ocultar " + dg.hidden[j];
        var hl = d.DiagramLinks.AddNew("", "");
        hl.ConnectorID = CONN[dg.hidden[j]].ConnectorID;
        hl.IsHidden = true;
        if (!hl.Update()) { throw new Error("No se pudo ocultar " + STEP + ": " + hl.GetLastError()); }
    }
    STEP = "nota del diagrama";
    var nt = root.Elements.AddNew("", "Note");
    nt.Notes = dg.note.text;
    nt.Update();
    var nb = dg.note.box;
    var no = d.DiagramObjects.AddNew("l=" + nb[0] + ";r=" + (nb[0] + nb[2]) + ";t=" + nb[1] + ";b=" + (nb[1] + nb[3]) + ";", "");
    no.ElementID = nt.ElementID;
    no.Update();
    d.DiagramLinks.Refresh();
    d.Update();
    Repository.SaveDiagram(d.DiagramID);
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
    log("FashionStore - generando el diagrama de clases de la base de datos...");
    Repository.EnableUIUpdates = false;
    var ok = false;
    try {
        ok = run();
    } catch (e) {
        log("[ERROR] " + (e.message || e.description || e) + " | paso: " + STEP);
    }
    Repository.EnableUIUpdates = true;
    if (ok) {
        log("[OK] Diagrama de clases creado en '" + ROOT_NAME + "': " + MODEL.classes.length + " clases, " +
            MODEL.relations.length + " relaciones.");
        Session.Prompt("Diagrama de clases generado correctamente.", 1);
    }
}

if (typeof Repository !== "undefined") { main(); }
