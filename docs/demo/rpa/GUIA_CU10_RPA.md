# Guía de prueba – CU10: Registrar ingreso de mercadería con RPA e IA

## Qué demuestra este caso de uso

El proveedor entrega mercadería a la tienda junto con un documento (nota de remisión, factura,
guía de despacho o una foto escaneada). En lugar de cargar prenda por prenda a mano:

1. **El proveedor sube el documento** en *Ingesta RPA*.
2. **La IA (Gemini) lo lee** y arma una tabla: SKU, prenda, talla, color, cantidad y costo.
3. **El sistema cruza cada SKU con el catálogo** de la empresa:
   - *Reconocido* → la prenda existe y puede ingresar al stock.
   - *No reconocido* → la prenda no existe en el catálogo; se informa y **no se crea** sola.
4. **El proveedor revisa** la tabla y puede corregir lo que la IA leyó mal (*Guardar correcciones*).
5. **La tienda confirma** (administrador o encargado): elige la sucursal que recibe y pulsa
   *Ingresar al inventario*. Todo entra en una sola operación.

| Rol | Qué puede hacer |
|---|---|
| Proveedor | Subir documentos, ver **solo los suyos**, corregir. **No** puede ingresar al inventario. |
| Administrador | Ver todos los documentos de su empresa, corregir e ingresar a cualquier sucursal. |
| Encargado | Ver los documentos pendientes y los de su sucursal; ingresar **solo a su sucursal**. |

Contraseña de todos los usuarios de esta guía: **`Fashion2026!`**

## Antes de empezar

- Backend (`localhost:8000`) y frontend (`localhost:4200`) encendidos.
- Archivos de esta carpeta (`docs/demo/rpa/`): uno por empresa, en distintos formatos para
  mostrar que la IA lee PDF e imágenes.
- **Cuota de la IA:** la clave gratuita de Gemini permite pocas lecturas por día. Cada documento
  subido gasta una. Si aparece *"No se pudo procesar el documento con IA"*, espera un minuto y
  vuelve a subirlo; si persiste, se agotó la cuota del día.

---

## 1. Ayni Moda — Nota de remisión (PDF)

- **Archivo:** `01_ayni_moda_nota_remision.pdf`
- **Proveedor:** Textiles & Hilados Andinos S.R.L. → `carlos.aliaga@ayni-moda-proveedores.demo.bo`
- **Administradora:** `carolina.quiroga@ayni-moda.demo.bo`
- **Encargado:** `rodrigo.choque@ayni-moda.demo.bo`

| SKU | Prenda | Talla | Cant. | Resultado esperado |
|---|---|---|---|---|
| AYN-006-N-L | Vestido Mini Negro Estampado Floral | L | 10 | Reconocido |
| AYN-015-B-L | Top Asimétrico Lunares | L | 15 | Reconocido |
| AYN-021-CC-L | Chaqueta Bomber Cuero Marrón | L | 8 | Reconocido |
| AYN-003-C-L | Blusa Estructurada Botones Dorados | L | 20 | Reconocido |
| AYN-018-RP-L | Suéter Crop Cuello Barco Rosa | L | 12 | Reconocido |
| TA-NUEVO-2026 | Chaleco de alpaca (modelo nuevo) | M | 6 | **No reconocido** |

**Al ingresar:** entran **65 unidades** de 5 prendas; el chaleco se omite.

## 2. Kantuta Boutique — Factura (PDF)

- **Archivo:** `02_kantuta_boutique_factura.pdf`
- **Proveedor:** Modas del Oriente S.A. → `paola.lino@kantuta-boutique-proveedores.demo.bo`
- **Administradora:** `mariana.suarez@kantuta-boutique.demo.bo`
- **Encargada:** `gabriela.roca@kantuta-boutique.demo.bo`

| SKU | Prenda | Talla | Cant. | Resultado esperado |
|---|---|---|---|---|
| KAN-048-VO-L | Enterizo Romper Utilitario Verde Oliva | L | 10 | Reconocido |
| KAN-062-B-L | Vestido Midi Blanco Marfil | L | 15 | Reconocido |
| KAN-005-N-L | Top Peplum Negro Escote Cuadrado | L | 8 | Reconocido |
| KAN-023-GJ-L | Top Chaleco Sastre Gris | L | 20 | Reconocido |
| KAN-060-AM-L | Vestido Midi Azul Marino Drapeado | L | 12 | Reconocido |
| MO-VER-3301 | Vestido lino verano tropical | S | 5 | **No reconocido** |

**Al ingresar:** entran **65 unidades** de 5 prendas.

## 3. Urbana Denim — Remito escaneado (imagen PNG)

- **Archivo:** `03_urbana_denim_remito_escaneado.png` (simula una hoja escaneada, levemente torcida)
- **Proveedor:** Denim Andino Industrial → `ricardo.soto@urbana-denim-proveedores.demo.bo`
- **Administrador:** `sergio.claros@urbana-denim.demo.bo`
- **Encargada:** `claudia.ruiz@urbana-denim.demo.bo`

| SKU | Prenda | Talla | Cant. | Resultado esperado |
|---|---|---|---|---|
| URB-018-RP-L | Suéter Crop Cuello Barco Rosa | L | 10 | Reconocido |
| URB-070-BN-36 | Pantalón Sastre Wide Leg Beige | 36 | 15 | Reconocido |
| URB-045-B-36 | Pantalón Sastre Tiro Alto Blanco | 36 | 8 | Reconocido |
| URB-016-B-L | Twin-set Cárdigan Cropped | L | 20 | Reconocido |
| URB-025-AM-L | Camiseta Básica Slim Fit Azul Marino | L | 12 | Reconocido |
| DA-MOM-900 | Jean mom fit lavado claro | 28 | 10 | **No reconocido** |

**Al ingresar:** entran **65 unidades** de 5 prendas. Este caso muestra la lectura de una **imagen**,
no solo de PDF (lo mismo serviría una foto del remito tomada con el celular).

## 4. Luna Satén — Guía de despacho (PDF)

- **Archivo:** `04_luna_saten_guia_despacho.pdf`
- **Proveedora:** Satinados La Paz → `monica.rivas@luna-saten-proveedores.demo.bo`
- **Administradora:** `veronica.pinto@luna-saten.demo.bo`
- **Encargada:** `ana.vera@luna-saten.demo.bo`

| SKU | Prenda | Talla | Cant. | Resultado esperado |
|---|---|---|---|---|
| LUN-054-B-L | Pijama Top Encaje y Short Vichy | L | 10 | Reconocido |
| LUN-030-B-L | Camiseta Béisbol Raglán | L | 15 | Reconocido |
| LUN-052-N-L | Pijama Corto Satinado Rosa Palo | L | 8 | Reconocido |
| LUN-027-CC-L | Camiseta Fruncida Marrón Espresso | L | 20 | Reconocido |
| LUN-025-AM-L | Camiseta Básica Slim Fit Azul Marino | L | 12 | Reconocido |
| SLP-KIM-07 | Kimono de satén bordado | M | 4 | **No reconocido** |

**Al ingresar:** entran **65 unidades** de 5 prendas.

---

## Pasos (iguales para cada empresa)

### Parte A — Proveedor
1. Iniciar sesión con el **proveedor** de la empresa.
2. Menú **Ingesta RPA** → arrastrar el archivo de la empresa (o clic para elegirlo).
3. En **Documentos** aparece *"Procesando"*; en unos segundos pasa a **"Listo para revisar"**.
4. Abrir el documento: se ve la tabla con las 6 líneas, 5 **Reconocido** (verde) y 1 **No reconocido** (ámbar),
   con el aviso de que esa línea se omitirá.
5. *(Opcional, para mostrar la corrección humana)* cambiar una cantidad, p. ej. de 10 a 9, y pulsar
   **Guardar correcciones**.
6. Comprobar que **no aparece** el botón *Ingresar al inventario*: el proveedor no puede ingresar stock.

### Parte B — Tienda (administrador o encargado)
1. Cerrar sesión e ingresar con el **administrador** (o el encargado) de la misma empresa.
2. Antes de ingresar, abrir **Inventario** y anotar el stock actual de una de las prendas reconocidas
   en la sucursal que va a recibir.
3. Menú **Ingesta RPA** → abrir el documento que subió el proveedor.
4. Elegir la **sucursal que recibe** y pulsar **Ingresar al inventario**.
5. El documento pasa a **"Ingresado"** y la tabla queda bloqueada.
6. Volver a **Inventario**: el stock de esa prenda subió exactamente en la cantidad del documento.

---

## Pruebas de control (lo que el sistema debe rechazar)

| Prueba | Cómo | Resultado esperado |
|---|---|---|
| Documento de otra empresa | Con la proveedora de Kantuta, subir `01_ayni_moda_nota_remision.pdf` | Estado **"No se pudo leer"**; al abrirlo: *"Ninguna prenda del documento coincide con un SKU activo del catálogo de esta empresa"*. Una empresa no puede ingresar prendas de otra. |
| Documento que no es un envío | Subir una ficha de devolución (RMA) o un ticket de venta | Estado **"No se pudo leer"**: la IA no encuentra mercadería de proveedor. |
| Archivo no permitido | Subir un Excel, Word o `.txt` | Rechazado al subir: *solo PDF o imagen*. |
| Ingresar dos veces | Volver a abrir un documento ya ingresado | No tiene botón de ingreso: no se duplica el stock. |
| Aislamiento entre proveedores | Entrar con otro proveedor de la misma empresa (p. ej. `rosa.mamani@ayni-moda-proveedores.demo.bo`) | No ve los documentos de Carlos. |

## Relación con *Solicitudes* (reposición a proveedores)

*Solicitudes* es otro flujo: la tienda **pide** mercadería y el proveedor la **acepta**
(Aceptar → Marcar preparando → Marcar entregada a sucursal) y la tienda pulsa **Confirmar recepción**,
que también suma stock. Para la demostración conviene mostrarlos por separado: si se confirma una
solicitud **y** se ingresa por RPA la misma mercadería, el stock se suma dos veces.
