/* =================================================================================
 * PROYECTO: FashionStore - E-Commerce
 * DIAGRAMA: Diagrama de Despliegue (Deployment Diagram - Flujo Vertical UML 2.5+)
 * DESCRIPCIÓN: Modelo de despliegue físico y lógico estructurado verticalmente:
 *              - Capa 1 (Superior): Dispositivos Cliente y Dispositivo Admin/Sucursal.
 *              - Capa 2: Red Internet (WAN / Telecomunicaciones).
 *              - Capa 3: Servidor Web Frontend (Vercel Cloud Platform).
 *              - Capa 4: Servidor Backend (Google Cloud Platform - Cloud Run).
 *              - Capa 5 (Inferior): Servidor Base de Datos (Cloud PostgreSQL - Neon.Tech).
 *              - Capa Lateral Derecha: Servicios Cloud/IA (Lucy VTON, Cloudinary, Gemini AI, Stripe).
 *              
 *              * Todos los artefactos y entornos de ejecución se generan como
 *                elementos UML independientes (Artifacts / Execution Environments)
 *                anidados visual y jerárquicamente dentro de sus Nodos.
 *
 * ENTORNO: Enterprise Architect 15.0+ / 16.0+
 * LENGUAJE: JScript (Motor nativo WSH en Enterprise Architect)
 * ================================================================================= */

var DEFAULT_PACKAGE_NAME = "CUdiagrams";
var DIAGRAM_NAME = "Diagrama de Despliegue - FashionStore";

function log(msg) {
    Session.Output("[Despliegue-FashionStore] " + msg);
}

/**
 * Obtiene el paquete de destino en el Project Browser o lo crea si no existe.
 */
function getTargetPackage() {
    var selectedPkg = Repository.GetTreeSelectedPackage();
    if (selectedPkg != null) {
        log("Usando paquete seleccionado en Project Browser: " + selectedPkg.Name);
        return selectedPkg;
    }

    var roots = Repository.Models;
    var root = (roots.Count > 0) ? roots.GetAt(0) : null;
    if (root == null) {
        Session.Prompt("No se encontró ningún modelo raíz en Enterprise Architect.", 0);
        return null;
    }

    for (var i = 0; i < root.Packages.Count; i++) {
        var p = root.Packages.GetAt(i);
        if (p.Name == DEFAULT_PACKAGE_NAME) {
            return p;
        }
    }

    var newPkg = root.Packages.AddNew(DEFAULT_PACKAGE_NAME, "Package");
    newPkg.Update();
    root.Packages.Refresh();
    log("Paquete creado: " + DEFAULT_PACKAGE_NAME);
    return newPkg;
}

/**
 * Recrea el diagrama de despliegue limpio.
 */
function recreateDiagram(pkg) {
    for (var i = pkg.Diagrams.Count - 1; i >= 0; i--) {
        var d = pkg.Diagrams.GetAt(i);
        if (d.Name == DIAGRAM_NAME) {
            try {
                pkg.Diagrams.Delete(i);
                pkg.Diagrams.Refresh();
                log("Diagrama previo eliminado para regeneración limpia.");
            } catch (e) {
                log("Aviso al eliminar: " + e.message);
            }
            break;
        }
    }

    var diagram = pkg.Diagrams.AddNew(DIAGRAM_NAME, "Deployment");
    diagram.Update();
    pkg.Diagrams.Refresh();
    return diagram;
}

/**
 * Crea un Nodo UML (Device o Node) y lo posiciona en el diagrama.
 */
function addNode(pkg, diagram, name, stereotype, notes, l, r, t, b) {
    var el = pkg.Elements.AddNew(name, "Node");
    if (stereotype && stereotype.length > 0) {
        el.Stereotype = stereotype;
    }
    if (notes && notes.length > 0) {
        el.Notes = notes;
    }
    el.Update();
    pkg.Elements.Refresh();

    var dObj = diagram.DiagramObjects.AddNew("l=" + l + ";r=" + r + ";t=" + t + ";b=" + b + ";", "");
    dObj.ElementID = el.ElementID;
    dObj.Update();

    return el;
}

/**
 * Crea un Artefacto UML como elemento hijo dentro de un Nodo y lo posiciona en el diagrama.
 */
function addArtifact(parentNode, diagram, name, stereotype, l, r, t, b) {
    var art = parentNode.Elements.AddNew(name, "Artifact");
    if (stereotype && stereotype.length > 0) {
        art.Stereotype = stereotype;
    }
    art.Update();
    parentNode.Elements.Refresh();

    var dObj = diagram.DiagramObjects.AddNew("l=" + l + ";r=" + r + ";t=" + t + ";b=" + b + ";", "");
    dObj.ElementID = art.ElementID;
    dObj.Update();

    return art;
}

/**
 * Crea un Entorno de Ejecución (Execution Environment) dentro de un Nodo y lo posiciona en el diagrama.
 */
function addExecutionEnv(parentNode, diagram, name, stereotype, l, r, t, b) {
    var env = parentNode.Elements.AddNew(name, "ExecutionEnvironment");
    if (stereotype && stereotype.length > 0) {
        env.Stereotype = stereotype;
    }
    env.Update();
    parentNode.Elements.Refresh();

    var dObj = diagram.DiagramObjects.AddNew("l=" + l + ";r=" + r + ";t=" + t + ";b=" + b + ";", "");
    dObj.ElementID = env.ElementID;
    dObj.Update();

    return env;
}

/**
 * Crea una vía de comunicación (CommunicationPath) con etiqueta de protocolo y estereotipo.
 */
function addCommunication(src, dst, protocolLabel, stereotype) {
    var con = src.Connectors.AddNew(protocolLabel, "CommunicationPath");
    con.SupplierID = dst.ElementID;
    if (stereotype && stereotype.length > 0) {
        con.Stereotype = stereotype;
    }
    con.Update();
    return con;
}

function main() {
    log("Iniciando generación del Diagrama de Despliegue (Flujo Vertical)...");

    var pkg = getTargetPackage();
    if (pkg == null) return;

    var diagram = recreateDiagram(pkg);

    /* =========================================================================
     * 1. NIVEL 1: CAPA DE DISPOSITIVOS CLIENTES (Superior: Y = -40 .. -250)
     * ========================================================================= */
    // Dispositivo Cliente
    var nodoCliente = addNode(
        pkg, diagram,
        "Dispositivo Cliente\n(PC / Laptop / Smartphone)",
        "device",
        "Dispositivo del cliente final para acceso a catálogo, compras y probador virtual.",
        60, 420, -40, -250
    );
    addArtifact(nodoCliente, diagram, "Web Client App\n(Angular SPA)", "artifact", 90, 390, -100, -160);
    addArtifact(nodoCliente, diagram, "Mobile Client App\n(Flutter / Dart)", "artifact", 90, 390, -175, -235);

    // Dispositivo Admin / Sucursal
    var nodoAdmin = addNode(
        pkg, diagram,
        "Dispositivo Sucursal / Admin\n(PC Escritorio / Terminal POS)",
        "device",
        "Terminal de trabajo de administradores, encargados y cajeros.",
        480, 820, -40, -250
    );
    addArtifact(nodoAdmin, diagram, "Admin Dashboard SPA\n(Angular Web App)", "artifact", 510, 790, -125, -210);

    /* =========================================================================
     * 2. NIVEL 2: RED INTERNET (WAN / Tránsito: Y = -300 .. -420)
     * ========================================================================= */
    var nodoInternet = addNode(
        pkg, diagram,
        "Red Internet\n(WAN / Red Pública)",
        "device",
        "Infraestructura de telecomunicaciones pública segura (TCP/IP - TLS 1.3).",
        270, 610, -300, -420
    );

    /* =========================================================================
     * 3. NIVEL 3: SERVIDOR WEB FRONTEND - VERCEL (Y = -480 .. -690)
     * ========================================================================= */
    var nodoFrontend = addNode(
        pkg, diagram,
        "Servidor Web Frontend\n(Vercel Cloud Platform)",
        "device",
        "Plataforma PaaS Serverless y CDN global para alojamiento del frontend.",
        250, 630, -480, -690
    );
    var envVercel = addExecutionEnv(nodoFrontend, diagram, "Vercel Edge Runtime\n(Node.js Engine)", "executionEnvironment", 280, 600, -540, -670);
    addArtifact(nodoFrontend, diagram, "FashionStore Web Bundle\n(Next.js / Angular)", "artifact", 300, 580, -590, -655);

    /* =========================================================================
     * 4. NIVEL 4: SERVIDOR BACKEND - GOOGLE CLOUD (Y = -750 .. -980)
     * ========================================================================= */
    var nodoBackend = addNode(
        pkg, diagram,
        "Servidor Backend\n(Google Cloud Platform - Cloud Run)",
        "device",
        "Servidor de aplicaciones en la nube para procesamiento de APIs y lógica de negocio.",
        250, 630, -750, -980
    );
    var envDocker = addExecutionEnv(nodoBackend, diagram, "Docker Container\n(Python 3.11 + FastAPI)", "executionEnvironment", 280, 600, -810, -960);
    addArtifact(nodoBackend, diagram, "FashionStore REST API\n(FastAPI / Uvicorn)", "artifact", 300, 580, -870, -945);

    /* =========================================================================
     * 5. NIVEL 5: SERVIDOR BASE DE DATOS (Inferior: Y = -1040 .. -1250)
     * ========================================================================= */
    var nodoDatabase = addNode(
        pkg, diagram,
        "Servidor Base de Datos\n(Cloud PostgreSQL - Neon.Tech / Cloud SQL)",
        "device",
        "Servidor relacional de base de datos transaccional con persistencia y copias de seguridad.",
        250, 630, -1040, -1250
    );
    var envPostgres = addExecutionEnv(nodoDatabase, diagram, "PostgreSQL 16 DBMS Engine", "executionEnvironment", 280, 600, -1100, -1230);
    addArtifact(nodoDatabase, diagram, "Esquema BD Relacional\n(FashionStore_DB)", "artifact", 300, 580, -1155, -1215);

    /* =========================================================================
     * 6. COLUMNA DERECHA: SERVICIOS CLOUD E IA EXTERNOS (X = 930 .. 1280)
     * ========================================================================= */
    // Servicio 1: Lucy VTON (Probador Virtual / RA)
    var nodoLucy = addNode(
        pkg, diagram,
        "Lucy VTON Service\n(Probador Virtual / RA)",
        "node",
        "Servicio de Inteligencia Artificial para probador virtual de prendas.",
        930, 1280, -40, -220
    );
    addArtifact(nodoLucy, diagram, "Lucy VTON Inference API", "artifact", 960, 1250, -110, -190);

    // Servicio 2: Cloudinary
    var nodoCloudinary = addNode(
        pkg, diagram,
        "Cloudinary Media Cloud\n(Gestión y CDN de Multimedia)",
        "node",
        "Almacenamiento en la nube y optimización de imágenes de productos y catálogos.",
        930, 1280, -280, -460
    );
    addArtifact(nodoCloudinary, diagram, "Cloudinary REST & CDN API", "artifact", 960, 1250, -350, -430);

    // Servicio 3: Google Gemini AI
    var nodoGemini = addNode(
        pkg, diagram,
        "Google Cloud - Gemini AI\n(Asistente Inteligente & IA)",
        "node",
        "Modelos de lenguaje multimodal para chatbot y recomendaciones personalizadas.",
        930, 1280, -520, -700
    );
    addArtifact(nodoGemini, diagram, "Gemini 1.5/2.0 Flash API", "artifact", 960, 1250, -590, -670);

    // Servicio 4: Stripe
    var nodoStripe = addNode(
        pkg, diagram,
        "Pasarela de Pago\n(Stripe Payments)",
        "node",
        "Infraestructura de pagos digitales certificada PCI-DSS.",
        930, 1280, -760, -940
    );
    addArtifact(nodoStripe, diagram, "Stripe Payments REST API", "artifact", 960, 1250, -830, -910);

    /* =========================================================================
     * 7. VÍAS DE COMUNICACIÓN (Communication Paths con Protocolos)
     * ========================================================================= */
    // Flujo Vertical Principal
    addCommunication(nodoCliente, nodoInternet, "HTTPS :443\n(WSS/TLS 1.3)", "communication");
    addCommunication(nodoAdmin, nodoInternet, "HTTPS :443\n(TLS 1.3)", "communication");
    addCommunication(nodoInternet, nodoFrontend, "HTTPS :443\n(CDN / HTTP/2)", "communication");
    addCommunication(nodoFrontend, nodoBackend, "HTTPS / REST JSON\n(API Calls)", "communication");
    addCommunication(nodoBackend, nodoDatabase, "psycopg2 / TCP :5432\n(SSL Encrypted)", "communication");

    // Conexiones a Servicios Externos
    addCommunication(nodoCliente, nodoLucy, "HTTPS :443\n(AR Video Stream)", "communication");
    addCommunication(nodoBackend, nodoLucy, "HTTPS :443\n(Inference API)", "communication");
    addCommunication(nodoCliente, nodoCloudinary, "HTTPS :443\n(CDN Image Fetch)", "communication");
    addCommunication(nodoBackend, nodoCloudinary, "HTTPS :443\n(Media Upload API)", "communication");
    addCommunication(nodoBackend, nodoGemini, "HTTPS :443\n(REST API)", "communication");
    addCommunication(nodoBackend, nodoStripe, "HTTPS :443\n(Payment Intents)", "communication");

    /* =========================================================================
     * 8. GUARDAR, REFRESCAR Y ABRIR DIAGRAMA
     * ========================================================================= */
    diagram.Update();
    Repository.SaveDiagram(diagram.DiagramID);
    Repository.ReloadDiagram(diagram.DiagramID);
    Repository.OpenDiagram(diagram.DiagramID);

    log("Diagrama vertical '" + DIAGRAM_NAME + "' generado exitosamente con artefactos independientes.");
    Session.Prompt("¡Diagrama de Despliegue (Flujo Vertical) generado con éxito en Enterprise Architect!", 0);
}

main();
