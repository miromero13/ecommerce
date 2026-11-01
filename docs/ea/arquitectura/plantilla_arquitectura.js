/* =====================================================================================================
 * FashionStore SaaS - Arquitectura (EA 15): paquetes en tres capas y diagramas de componentes
 *
 * Generado por docs/ea/arquitectura/generar_arquitectura.py (no editar a mano: cambie el .py y vuelva a generar).
 *
 * USO: en el Project Browser seleccione el paquete donde quiere los diagramas; Specialize > Tools > Scripting;
 *      clic derecho en un grupo > New JScript; pegue TODO este archivo; guarde y ejecute (Run).
 *
 * Crea el paquete "Arquitectura - FashionStore SaaS" con un subpaquete por diagrama:
 *   1) Diseño lógico: paquetes en tres capas (Vista, Controlador, Modelo) y Persistencia, con los 6 paquetes de
 *      casos de uso; dependencias verticales dentro de cada paquete.
 *   2) Diagrama de componentes general del sistema: filas Vista («Componente:Vista»), Control
 *      («Componente:Control»), Modelo («Componente:Model») y Conexión («conexion»: PostgreSQL, almacenamientos
 *      locales y APIs externas).
 *   3) Componentes del backend FastAPI, 4) del frontend web Angular PWA y 5) de la app móvil Flutter, con el
 *      mismo estilo por filas: Vista, Control, Modelo y Conexión.
 *   6..11) Diagrama de componentes de cada módulo M1-M6, con el mismo estilo que el general.
 * Cada línea tiene su recorrido calculado: ninguna pasa sobre una caja ni se encima con otra.
 * Si el paquete ya existe (de una ejecución anterior) lo borra y lo crea de nuevo.
 * ===================================================================================================== */

/*MODEL*/
var ROOT_NAME = "Arquitectura - FashionStore SaaS";
var MARKER = "[generado: FashionStore_arquitectura.js]";
var STEP = "inicio";

function log(msg) { Session.Output(msg); }

function newPackage(parent, name, notes) {
    STEP = "paquete " + name;
    var p = parent.Packages.AddNew(name, "");
    p.Notes = notes || "";
    p.Update();
    parent.Packages.Refresh();
    return p;
}

function place(d, el, b) {
    var o = d.DiagramObjects.AddNew("l=" + b[0] + ";r=" + (b[0] + b[2]) + ";t=" + b[1] + ";b=" + (b[1] + b[3]) + ";", "");
    o.ElementID = el.ElementID;
    o.Update();
}

function crearElemento(pkg, e) {
    STEP = "elemento " + e.name;
    var el;
    if (e.kind === "package") {
        var sub = newPackage(pkg, e.name, "");
        el = sub.Element;
    } else {
        var tipo = e.kind === "frame" ? "Boundary" : (e.kind === "interface" ? "Interface" : "Component");
        el = pkg.Elements.AddNew(e.name, tipo);
        if (e.st) { el.Stereotype = e.st; }
        if (!el.Update()) { throw new Error("No se pudo crear " + e.name + ": " + el.GetLastError()); }
    }
    return el;
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
    var root = newPackage(parent, ROOT_NAME, "Arquitectura del sistema generada desde el codigo. " + MARKER);

    for (i = 0; i < MODEL.diagrams.length; i++) {
        var dg = MODEL.diagrams[i];
        var pkg = newPackage(root, (i + 1) + ". " + dg.name, "");
        STEP = "diagrama " + dg.name;
        var d = pkg.Diagrams.AddNew(dg.name, dg.type);
        d.Notes = MARKER;
        /* sin MetaType, EA 15 presenta el diagrama de paquetes como diagrama de clases */
        d.MetaType = "UML Structural::" + dg.type;
        if (!d.Update()) { throw new Error("No se pudo crear " + dg.name + ": " + d.GetLastError()); }
        pkg.Diagrams.Refresh();
        d.HighlightImports = false;
        d.Update();

        var EL = {};
        /* primero los marcos (quedan detras), luego el resto */
        for (k = 0; k < 2; k++) {
            for (j = 0; j < dg.elements.length; j++) {
                var e = dg.elements[j];
                var esMarco = (e.kind === "frame" || e.cont);
                if ((k === 0) !== esMarco) { continue; }
                EL[e.id] = crearElemento(pkg, e);
                place(d, EL[e.id], e.b);
            }
        }
        d.Update();
        for (j = 0; j < dg.links.length; j++) {
            var l = dg.links[j];
            STEP = "linea " + l.a + " -> " + l.b + " en " + dg.name;
            var tipoCon = l.type === "real" ? "Realisation" : "Dependency";
            var c = EL[l.a].Connectors.AddNew(l.label, tipoCon);
            c.SupplierID = EL[l.b].ElementID;
            if (!c.Update()) { throw new Error("No se pudo crear " + STEP + ": " + c.GetLastError()); }
            d.DiagramLinks.Refresh();
            var link = d.DiagramLinks.AddNew("", "");
            link.ConnectorID = c.ConnectorID;
            link.LineStyle = 3;
            var path = "";
            for (k = 0; k < l.path.length; k++) { path += l.path[k][0] + ":" + (-l.path[k][1]) + ";"; }
            link.Path = path;
            link.Geometry = l.geom;
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
    log("FashionStore - generando los diagramas de arquitectura...");
    Repository.EnableUIUpdates = false;
    var ok = false;
    try {
        ok = run();
    } catch (e) {
        log("[ERROR] " + (e.message || e.description || e) + " | paso: " + STEP);
    }
    Repository.EnableUIUpdates = true;
    if (ok) {
        log("[OK] " + MODEL.diagrams.length + " diagramas de arquitectura creados en '" + ROOT_NAME + "'.");
        Session.Prompt("Diagramas de arquitectura generados correctamente.", 1);
    }
}

if (typeof Repository !== "undefined") { main(); }
