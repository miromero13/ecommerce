# Frontend

Frontend del proyecto Roadside Assistance construido con Angular 21 y componentes Spartan/Helm.

## Requisitos

- Node.js 20 o superior
- npm 10 o superior

## Clonar el proyecto

```bash
git clone <URL_DEL_REPOSITORIO>
cd roadside-assistance/frontend
```

Si ya tienes el repositorio local, entra directamente a la carpeta `frontend`.

## Instalar dependencias

```bash
npm install
```

## Ejecutar en desarrollo

```bash
npm run start
```

Luego abre `http://localhost:4200/`.

También puedes usar el comando de Angular directamente:

```bash
ng serve
```

## Comandos útiles

```bash
npm run build
npm run watch
npm run test
```

- `npm run build`: genera la versión de producción.
- `npm run watch`: recompila en modo desarrollo cuando cambias archivos.
- `npm run test`: ejecuta las pruebas del proyecto.

## Estructura general

```text
frontend/
├── public/
└── src/
    ├── main.ts
    ├── styles.css
    └── app/
        ├── app.config.ts
        ├── app.routes.ts
        ├── app.ts
        └── components/
```

## Uso de Spartan

El proyecto usa Spartan/Helm para construir la interfaz. En `src/app/app.ts` ya están importados componentes como:

- `HlmAvatarImports`
- `HlmBadgeImports`
- `HlmButtonImports`
- `HlmCardImports`
- `HlmSeparatorImports`
- `HlmSidebarImports`

### Cómo usarlo en un componente

1. Importa los módulos Spartan que necesites.
2. Agrégalos al arreglo `imports` del componente.
3. Usa sus directivas o etiquetas en el template.

Ejemplo:

```ts
import { Component } from '@angular/core';
import { HlmButtonImports } from '@spartan-ng/helm/button';

@Component({
  selector: 'app-example',
  standalone: true,
  imports: [
    ...HlmButtonImports,
  ],
  template: `
    <button hlmBtn>Continuar</button>
  `,
})
export class ExampleComponent {}
```

### Componentes disponibles en el proyecto

El repositorio ya incluye varios componentes de Spartan en `src/app/components/`, como:

- avatar
- badge
- button
- card
- separator
- sheet
- sidebar
- skeleton
- tooltip
- input

Si quieres crear uno nuevo, usa la misma estructura de `src/app/components/<componente>/src/lib` y exporta el módulo desde `src/index.ts`.

## Configuración de la app

- `src/app/app.config.ts` configura el router.
- `src/app/app.ts` es el componente raíz.
- `src/app/app.routes.ts` define las rutas.

## Notas

- El proyecto usa el gestor `npm` definido en `package.json`.
- El comando recomendado para desarrollo es `npm run start`.
- Si agregas más componentes Spartan, recuerda importarlos en el componente donde los uses.
