// ============================================================================
// Diagrama de Clases (Modelo de Datos) para Enterprise Architect — JScript
// Genera el modelo a partir del esquema PostgreSQL: schema_postgres.sql
// (Carpeta: documentationDocs\informes\)
//
// USO:
//   1. Abre Enterprise Architect.
//   2. Abre la ventana de Scripts: Add-In > Manage > Script (o Ctrl+9).
//   3. Crea un nuevo script tipo "JScript", pega este archivo y ejecútalo.
//   4. Selecciona (o deja seleccionado) el paquete destino en el Project Browser.
//
// GENERA:
//   - Paquete "Modelo de Datos FashionStore" con 23 clases (una por tabla).
//   - Atributos con tipo de dato EA (Guid, String, Integer, Currency, Boolean,
//     Date) y estereotipos PK / FK / enum según la columna SQL.
//   - 35 asociaciones entre clases con VERBO en español y CARDINALIDADES.
// ============================================================================

// Dentro de la ventana de Scripts de EA, "Repository" ya es un objeto global
// inyectado por EA (y es de solo lectura). NO se debe reasignar.
// Fuera de EA (con cscript.exe) se conecta a una instancia abierta de EA.
var Repo = (typeof Repository != "undefined") ? Repository : null;
if (Repo == null) {
    var eaApp = new ActiveXObject("EA.App");
    Repo = eaApp.Repository;
}

function Log(msg) {
    try { Session.Output(msg); } catch (e) { WScript.Echo(msg); }
}

// ---------------------------------------------------------------------------
// Tipos: mapeo SQL -> tipos EA
// ---------------------------------------------------------------------------
function eaType(sqlType) {
    var t = (sqlType + "").toLowerCase();
    if (t.indexOf("uuid") >= 0) return "Guid";
    if (t.indexOf("boolean") >= 0) return "Boolean";
    if (t.indexOf("integer") >= 0 || t.indexOf("serial") >= 0) return "Integer";
    if (t.indexOf("numeric") >= 0 || t.indexOf("decimal") >= 0 || t.indexOf("money") >= 0) return "Currency";
    if (t.indexOf("timestamp") >= 0 || t.indexOf("date") >= 0) return "Date";
    if (t.indexOf("text") >= 0 || t.indexOf("character") >= 0 || t.indexOf("char") >= 0 || t.indexOf("varchar") >= 0) return "String";
    return "String";
}

// ---------------------------------------------------------------------------
// VERBOS / cardinalidades. Cada relación: [claseOrigen, claseDestino, verbo,
// cardOrigen, cardDestino]. La lectura del verbo es del lado donde tiene
// sentido en el dominio: "un <claseDestino> <verbo> ... <claseOrigen>".
// ---------------------------------------------------------------------------
var RELACIONES = [
    ["users",              "branches",            "pertenece",        "0..*", "1"],
    ["providers",          "users",               "se_asocia_con",    "0..*", "0..1"],
    ["providers",          "branches",            "opera_en",         "0..*", "1"],
    ["collections",        "seasons",             "pertenece_a",      "0..*", "1"],
    ["products",           "collections",         "se_asocia_a",      "0..*", "1"],
    ["products",           "categories",          "se_clasifica_en",  "0..*", "1"],
    ["products",           "seasons",             "marca_temporada",  "0..*", "1"],
    ["providers",          "products",            "registra",         "1",    "0..*"],
    ["product_variants",   "products",            "pertenece_a",      "0..*", "1"],
    ["product_variants",   "sizes",               "tiene_talla",      "0..*", "1"],
    ["product_variants",   "colors",              "tiene_color",      "0..*", "1"],
    ["product_variants",   "inventory",           "posee_stock_en",   "1",    "0..*"],
    ["inventory",          "branches",            "se_ubica_en",      "0..*", "1"],
    ["inventory_movements","product_variants",    "afecta_stock",     "0..*", "1"],
    ["inventory_movements","branches",            "se_ejecuta_en",    "0..*", "1"],
    ["inventory_movements","branches",            "transfiere_a",     "0..*", "0..1"], // reference_branch_id
    ["inventory_movements","users",               "es_registrado_por","0..*", "0..1"], // created_by
    ["users",              "carts",               "posee",              "1",  "0..1"], // carrito único
    ["carts",              "cart_items",          "contiene",           "1",  "0..*"],
    ["cart_items",         "product_variants",    "incluye",          "0..*", "1"],
    ["reservations",       "branches",            "se_solicita_en",   "0..*", "1"],
    ["reservations",       "users",               "es_solicitada_por","0..*", "0..1"],
    ["reservations",       "reservation_items",   "contiene",           "1",  "0..*"],
    ["reservation_items",  "product_variants",    "reserva",          "0..*", "1"],
    ["users",              "orders",              "realiza",            "1",  "0..*"],
    ["orders",             "branches",            "se_recoge_en",     "0..*", "0..1"], // pickup_branch_id
    ["orders",             "order_items",         "agrupa",             "1",  "0..*"],
    ["order_items",        "product_variants",    "detalla",          "0..*", "1"],
    ["sales",              "branches",            "se_registra_en",   "0..*", "1"],
    ["sales",              "users",               "es_atendida_por",  "0..*", "1"],
    ["sales",              "reservations",        "convierte",        "0..*", "0..1"], // reserva única
    ["sales",              "sale_items",          "detalla",            "1",  "0..*"],
    ["sale_items",         "product_variants",    "vende",            "0..*", "1"],
    ["orders",             "payment_attempts",    "procesa_pago",       "1",  "0..*"],
    ["payment_attempts",   "carts",               "valida_carrito",   "0..*", "1"]
];

// ---------------------------------------------------------------------------
// Esquema relacional -> clases: [nombre, [ [atributo, tipoSQL, estereotipo], ... ]]
// Estereotipos: PK, FK o el nombre del enum (null si ninguno).
// ---------------------------------------------------------------------------
var TABLAS = [
    ["branches", [
        ["id", "UUID", "PK"], ["name", "VARCHAR", null], ["city", "VARCHAR", null],
        ["is_default", "BOOLEAN", null], ["is_active", "BOOLEAN", null]
    ]],
    ["users", [
        ["id", "UUID", "PK"], ["name", "VARCHAR", null], ["email", "VARCHAR", null],
        ["hashed_password", "VARCHAR", null], ["gender", "genderenum", "enum"],
        ["rol", "rolenum", "enum"], ["branch_id", "UUID", "FK"], ["is_active", "BOOLEAN", null]
    ]],
    ["providers", [
        ["id", "UUID", "PK"], ["user_id", "UUID", "FK"], ["business_name", "VARCHAR", null],
        ["contact_name", "VARCHAR", null], ["phone", "VARCHAR", null], ["branch_id", "UUID", "FK"],
        ["status", "providerstatusenum", "enum"]
    ]],
    ["categories", [["id", "UUID", "PK"], ["name", "VARCHAR", null]]],
    ["seasons",    [["id", "UUID", "PK"], ["name", "VARCHAR", null]]],
    ["collections",[["id", "UUID", "PK"], ["name", "VARCHAR", null], ["season_id", "UUID", "FK"]]],
    ["sizes",      [["id", "UUID", "PK"], ["name", "VARCHAR", null]]],
    ["colors",     [["id", "UUID", "PK"], ["name", "VARCHAR", null], ["hex_code", "VARCHAR", null]]],
    ["products", [
        ["id", "UUID", "PK"], ["name", "VARCHAR", null], ["description", "TEXT", null],
        ["category_id", "UUID", "FK"], ["collection_id", "UUID", "FK"], ["season_id", "UUID", "FK"],
        ["provider_id", "UUID", "FK"], ["created_at", "TIMESTAMP", null], ["updated_at", "TIMESTAMP", null]
    ]],
    ["product_variants", [
        ["id", "UUID", "PK"], ["product_id", "UUID", "FK"], ["sku", "VARCHAR", null],
        ["price", "NUMERIC(10,2)", null], ["size_id", "UUID", "FK"], ["color_id", "UUID", "FK"],
        ["image_url", "VARCHAR", null], ["image_public_id", "VARCHAR", null],
        ["status", "productstatusenum", "enum"]
    ]],
    ["inventory", [
        ["id", "UUID", "PK"], ["variant_id", "UUID", "FK"], ["branch_id", "UUID", "FK"],
        ["quantity", "INTEGER", null], ["reserved", "INTEGER", null]
    ]],
    ["inventory_movements", [
        ["id", "UUID", "PK"], ["variant_id", "UUID", "FK"], ["branch_id", "UUID", "FK"],
        ["movement_type", "inventorymovementtypeenum", "enum"], ["quantity", "INTEGER", null],
        ["reference_branch_id", "UUID", "FK"], ["note", "TEXT", null], ["created_by", "UUID", "FK"],
        ["created_at", "TIMESTAMP", null]
    ]],
    ["carts", [
        ["id", "UUID", "PK"], ["user_id", "UUID", "FK"], ["status", "cartstatusenum", "enum"],
        ["subtotal", "NUMERIC(10,2)", null], ["discount_amount", "NUMERIC(10,2)", null],
        ["total_amount", "NUMERIC(10,2)", null], ["created_at", "TIMESTAMP", null],
        ["updated_at", "TIMESTAMP", null]
    ]],
    ["cart_items", [
        ["id", "UUID", "PK"], ["cart_id", "UUID", "FK"], ["variant_id", "UUID", "FK"],
        ["quantity", "INTEGER", null], ["unit_price", "NUMERIC(10,2)", null]
    ]],
    ["reservations", [
        ["id", "UUID", "PK"], ["branch_id", "UUID", "FK"], ["user_id", "UUID", "FK"],
        ["visit_date", "DATE", null], ["expires_at", "TIMESTAMP", null],
        ["status", "reservationstatusenum", "enum"], ["total_amount", "NUMERIC(10,2)", null],
        ["created_at", "TIMESTAMP", null], ["updated_at", "TIMESTAMP", null]
    ]],
    ["reservation_items", [
        ["id", "UUID", "PK"], ["reservation_id", "UUID", "FK"], ["variant_id", "UUID", "FK"],
        ["quantity", "INTEGER", null], ["unit_price", "NUMERIC(10,2)", null]
    ]],
    ["orders", [
        ["id", "UUID", "PK"], ["user_id", "UUID", "FK"], ["status", "orderstatusenum", "enum"],
        ["payment_method", "paymentmethodenum", "enum"], ["payment_status", "paymentstatusenum", "enum"],
        ["stripe_payment_intent_id", "VARCHAR", null], ["cash_reference", "VARCHAR", null],
        ["pickup_branch_id", "UUID", "FK"], ["pickup_expires_at", "TIMESTAMP", null],
        ["pickup_code", "VARCHAR", null], ["fulfillment_status", "fulfillmentstatusenum", "enum"],
        ["subtotal", "NUMERIC(10,2)", null], ["discount_amount", "NUMERIC(10,2)", null],
        ["total_amount", "NUMERIC(10,2)", null], ["currency", "VARCHAR", null],
        ["created_at", "TIMESTAMP", null], ["updated_at", "TIMESTAMP", null]
    ]],
    ["order_items", [
        ["id", "UUID", "PK"], ["order_id", "UUID", "FK"], ["variant_id", "UUID", "FK"],
        ["quantity", "INTEGER", null], ["unit_price", "NUMERIC(10,2)", null],
        ["line_total", "NUMERIC(10,2)", null], ["product_id", "UUID", null],
        ["product_name", "VARCHAR", null], ["variant_sku", "VARCHAR", null], ["size_id", "UUID", null],
        ["color_id", "UUID", null], ["image_url", "VARCHAR", null], ["image_public_id", "VARCHAR", null]
    ]],
    ["sales", [
        ["id", "UUID", "PK"], ["branch_id", "UUID", "FK"], ["user_id", "UUID", "FK"],
        ["reservation_id", "UUID", "FK"], ["status", "salestatusenum", "enum"],
        ["payment_method", "paymentmethodenum", "enum"], ["payment_status", "paymentstatusenum", "enum"],
        ["cash_reference", "VARCHAR", null], ["subtotal", "NUMERIC(10,2)", null],
        ["discount_amount", "NUMERIC(10,2)", null], ["total_amount", "NUMERIC(10,2)", null],
        ["currency", "VARCHAR", null], ["created_at", "TIMESTAMP", null], ["updated_at", "TIMESTAMP", null]
    ]],
    ["sale_items", [
        ["id", "UUID", "PK"], ["sale_id", "UUID", "FK"], ["variant_id", "UUID", "FK"],
        ["quantity", "INTEGER", null], ["unit_price", "NUMERIC(10,2)", null],
        ["line_total", "NUMERIC(10,2)", null], ["product_id", "UUID", null],
        ["product_name", "VARCHAR", null], ["variant_sku", "VARCHAR", null], ["size_id", "UUID", null],
        ["color_id", "UUID", null], ["image_url", "VARCHAR", null], ["image_public_id", "VARCHAR", null]
    ]],
    ["payment_attempts", [
        ["id", "UUID", "PK"], ["order_id", "UUID", "FK"], ["cart_id", "UUID", "FK"],
        ["stripe_payment_intent_id", "VARCHAR", null], ["status", "VARCHAR", null],
        ["idempotency_key", "VARCHAR", null], ["created_at", "TIMESTAMP", null],
        ["updated_at", "TIMESTAMP", null]
    ]],
    ["stripe_events", [
        ["id", "UUID", "PK"], ["stripe_event_id", "VARCHAR", null], ["created_at", "TIMESTAMP", null]
    ]]
];

// ---------------------------------------------------------------------------
// Generación del modelo en EA
// ---------------------------------------------------------------------------
function Main() {
    var pkgDestino = Repo.GetTreeSelectedPackage();
    if (pkgDestino == null) pkgDestino = Repo.Models.GetAt(0);
    if (pkgDestino == null) { Log("Selecciona un paquete destino."); return; }

    var model = pkgDestino.Packages.AddNew("Modelo de Datos FashionStore", "Package");
    model.Update();

    var elementos = new Object();
    var total = TABLAS.length;

    // 1) Crear clases + atributos
    for (var i = 0; i < total; i++) {
        var tabla = TABLAS[i][0];
        var campos = TABLAS[i][1];
        var cls = model.Elements.AddNew(tabla, "Class");
        cls.Stereotype = "table";
        cls.Update();

        for (var j = 0; j < campos.length; j++) {
            var campo = campos[j][0];
            var tipo  = campos[j][1];
            var est   = campos[j][2];
            var a = cls.Attributes.AddNew(campo, eaType(tipo));
            if (est != null) a.Stereotype = est;
            a.Update();
        }
        cls.Update();
        elementos[tabla] = cls;
    }
    // Nota: si EA añade atributos internos; limpiar estereotipo por defecto
    // no es necesario aquí.

    // 2) Crear asociaciones con verbo y cardinalidades
    for (var r = 0; r < RELACIONES.length; r++) {
        var origen  = RELACIONES[r][0];
        var destino = RELACIONES[r][1];
        var verbo   = RELACIONES[r][2];
        var cardOrigen  = RELACIONES[r][3];
        var cardDestino = RELACIONES[r][4];

        if (elementos[origen] == null || elementos[destino] == null) continue;

        var conn = elementos[origen].Connectors.AddNew(verbo, "Association");
        conn.ClientID    = elementos[origen].ElementID;
        conn.SupplierID  = elementos[destino].ElementID;
        conn.ClientEnd.Cardinality  = cardOrigen;
        conn.SupplierEnd.Cardinality = cardDestino;
        conn.Update();
    }

    // 3) Crear el diagrama de clases y posicionar los elementos en una grilla
    var diagram = model.Diagrams.AddNew("Diagrama de Clases — Modelo de Datos", "Logical");
    diagram.Update();

    var cols = 5, ancho = 220, alto = 170, gapX = 40, gapY = 60, x0 = 30, y0 = 30;
    for (var k = 0; k < total; k++) {
        var nombre = TABLAS[k][0];
        var obj = elementos[nombre];
        if (obj == null) continue;
        var fila = Math.floor(k / cols);
        var col = k % cols;
        var left   = x0 + col * (ancho + gapX);
        var top    = y0 + fila * (alto + gapY);
        var dObj = diagram.DiagramObjects.AddNew("l=" + left + ";r=" + (left + ancho) + ";t=" + top + ";b=" + (top + alto) + ";", "");
        dObj.ElementID = obj.ElementID;
        dObj.Update();
    }

    diagram.Update();
    Repo.RefreshModelView(diagram.DiagramID);
    Log("Modelo generado: " + total + " clases, " + RELACIONES.length + " asociaciones.");
}

Main();
// ============================================================================
// FIN DEL SCRIPT
// ============================================================================