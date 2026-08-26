const version = process.versions.node;
const [major, minor] = version.split('.').map((part) => Number(part));

const isSupported =
  (major === 20 && minor >= 19) ||
  (major === 22 && minor >= 13);

if (!isSupported) {
  console.error('');
  console.error('[frontend] Version de Node no compatible con esta app.');
  console.error(`[frontend] Detectada: v${version}`);
  console.error('[frontend] Requerida: v20.19.x o v22.13.x+');
  console.error('[frontend] Sugerencia: `nvm use 22.13.1` o `nvm use 20.19.0`.');
  process.exit(1);
}
