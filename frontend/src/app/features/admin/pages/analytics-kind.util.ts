import type { AnalyticsQuery, AnalyticsTotals, ReportKind } from '../../shared/models/report.model';

// Non-sales kinds ignore these fields: send defaults so the backend never gets misleading noise.
export function specForKind(spec: AnalyticsQuery, kind: ReportKind): AnalyticsQuery {
  if (kind === 'sales') return { ...spec, kind };
  const period = kind === 'movements' ? spec.period : { preset: 'last_n_days' as const, n: 30, from_date: null, to_date: null };
  return {
    ...spec, kind, period, metric: 'units', group_by: ['product'], top_n: null, order: 'desc',
    channel: 'all', payment_methods: [], compare_previous: false, chart: null,
  };
}

// One summary line for non-sales kinds: only the totals that exist, labelled in Spanish.
export function kindSummary(kind: ReportKind, totals: AnalyticsTotals): Array<{ label: string; value: number }> {
  const unitsLabel = kind === 'movements' ? 'Unidades movidas' : 'Unidades en existencia';
  return ([['items', 'Registros'], ['units', unitsLabel]] as const)
    .filter(([key]) => totals[key] !== null && totals[key] !== undefined)
    .map(([key, label]) => ({ label, value: Number(totals[key]) }));
}

// Single catalogue of example phrases (panel, quick row and 422 suggestions); all verified against the backend interpreter.
export const REPORT_EXAMPLES: Array<{ title: string; items: string[] }> = [
  { title: 'Ventas', items: ['cuánto vendimos hoy', 'cuánto vendí ayer', 'ventas de la semana pasada', 'ventas de octubre', 'ticket promedio de este mes', 'cuánta plata entró ayer'] },
  { title: 'Rankings', items: ['los 5 productos más vendidos del mes', 'cuál es el producto más vendido', 'cuál es la sucursal que más vende', 'la peor sucursal', 'los productos que menos se venden', 'el mejor producto de cada sucursal en el último trimestre'] },
  { title: 'Períodos', items: ['ventas del 1 al 15 de octubre', 'ventas del último trimestre', 'ventas del trimestre pasado', 'ventas del año pasado', 'ventas de los últimos quince días', 'ventas de septiembre'] },
  { title: 'Canal y pago', items: ['ventas por internet este mes', 'ventas con tarjeta de ayer', 'online vs tienda', 'ventas de la tienda física', 'ventas en efectivo de hoy', 'ventas por QR'] },
  { title: 'Inventario', items: ['mostrame el inventario', 'muéstrame el inventario', 'qué productos tienen poco stock', 'stock crítico', 'movimientos de inventario de esta semana'] },
  { title: 'Clientes', items: ['mis mejores clientes', 'cuántos clientes compraron este mes'] },
  { title: 'Comparaciones', items: ['ventas de este mes comparado con el mes pasado', 'compara las ventas de este mes con las del mes pasado', 'compárame las sucursales', 'ventas por día de esta semana'] },
];
export const QUICK_EXAMPLES = ['cuánto vendimos hoy', 'los 5 productos más vendidos del mes', 'mostrame el inventario', 'mis mejores clientes'];
