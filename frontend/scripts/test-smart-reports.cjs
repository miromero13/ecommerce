const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const vm = require('node:vm');
const { test } = require('node:test');
const ts = require('typescript');
const { of, throwError, firstValueFrom } = require('rxjs');

// Execute the real component without a DOM; Angular owns signals/computed/injection.
// Only presentation imports, HTTP boundaries and toast delivery are replaced.
async function main() {
  await import('@angular/compiler');
  const core = await import('@angular/core');
  const http = await import('@angular/common/http');
  class ReportsApiService {}
  class AdminBranchService {}
  const messages = [];
  const modules = {
    '@angular/common': { CommonModule: class {} },
    '@angular/common/http': http,
    '@angular/core': { ...core, Component: () => (component) => component },
    '@angular/forms': { FormsModule: class {} },
    rxjs: { firstValueFrom },
    '@spartan-ng/brain/sonner': { toast: { success: (message) => messages.push(message), error() {} } },
    '@spartan-ng/helm/utils': { OnBrowserDirective: class {} },
    'angular-chrts': { BarChartComponent: class {} },
    '../../../components/button/src': { HlmButton: class {} },
    '../../../components/card/src': { HlmCardImports: [] },
    '../../../components/input/src': { HlmInputImports: [] },
    '../../../components/table/src': { HlmTable: class {} },
    '../../shared/services/reports-api.service': { ReportsApiService },
    '../services/admin-branch.service': { AdminBranchService },
  };
  function load(relativePath) {
    const filename = path.join(__dirname, '..', relativePath);
    const { outputText } = ts.transpileModule(fs.readFileSync(filename, 'utf8'), {
      compilerOptions: { module: ts.ModuleKind.CommonJS, target: ts.ScriptTarget.ES2022, experimentalDecorators: true },
      fileName: filename,
    });
    const exports = {};
    const requireStub = (name) => {
      assert.ok(Object.hasOwn(modules, name), `Unexpected dependency: ${name}`);
      return modules[name];
    };
    vm.runInThisContext(`(function(require, exports) {${outputText}\n})`, { filename })(requireStub, exports);
    return exports;
  }
  modules['../../../core/utils/http-error.util'] = load('src/app/core/utils/http-error.util.ts');
  const { AdminReportsPageComponent } = load('src/app/features/admin/pages/admin-reports-page.component.ts');
  const rows = [{ branch_id: 'private-id', branch_name: 'Centro', product_name: 'Blusa', quantity_sold: 2, gross_sales: '50.00' }];
  const payload = { summary: {}, rows };
  function setup(columns) {
    messages.length = 0;
    const api = {
      queryNaturalLanguage: () => of({ message: 'Consulta interpretada', data: { report_type: 'sales', columns, filters: {}, interpretation: 'Ventas', report: payload } }),
      getSmartReport: () => of({ message: 'Reporte generado', data: payload }),
      predictDemand: () => of({ message: 'Pronóstico generado', data: { forecast: [] } }),
      customerClusters: () => of({ message: 'Segmentación generada', data: { segments: [] } }),
    };
    const injector = core.Injector.create({ providers: [
      { provide: ReportsApiService, useValue: api },
      { provide: AdminBranchService, useValue: { listBranches: () => of({ data: [] }) } },
    ] });
    const page = core.runInInjectionContext(injector, () => new AdminReportsPageComponent());
    page.naturalQuery = 'Ventas, solo columna sucursal';
    return { page, api };
  }
  const keys = (page) => page.columns().map((column) => column.key);

  test('NLP projects only requested presentation columns in the requested order', async () => {
    const { page } = setup(['branch_name']);
    await page.generateReport(true);
    assert.deepEqual(keys(page), ['branch_name']);
    assert.equal(page.error(), '');
    assert.deepEqual(messages, ['Consulta interpretada']);
  });
  test('NLP ordering is preserved while IDs and unknown columns stay hidden', async () => {
    const { page } = setup(['gross_sales', 'branch_id', 'branch_name', 'unknown']);
    await page.generateReport(true);
    assert.deepEqual(keys(page), ['gross_sales', 'branch_name']);
  });
  test('manual reports reset NLP selection and retain all known safe columns', async () => {
    const { page } = setup(['branch_name']);
    await page.generateReport(true);
    await page.generateReport();
    assert.deepEqual(keys(page), ['branch_name', 'product_name', 'quantity_sold', 'gross_sales']);
    assert.deepEqual(messages, ['Consulta interpretada', 'Reporte generado']);
  });
  test('NLP without a column selection preserves default presentation columns', async () => {
    for (const columns of [undefined, []]) {
      const { page } = setup(columns);
      await page.generateReport(true);
      assert.deepEqual(keys(page), ['branch_name', 'product_name', 'quantity_sold', 'gross_sales']);
    }
  });
  test('ML actions use real company data by default and synthetic data only in demo mode', async () => {
    const { page, api } = setup();
    const requests = [];
    api.predictDemand = (payload) => {
      requests.push(['demand', payload]);
      return of({ message: 'Demanda', data: { forecast: [] } });
    };
    api.customerClusters = (synthetic) => {
      requests.push(['clusters', synthetic]);
      return of({ message: 'Segmentos', data: { segments: [] } });
    };
    page.branchId = 'descriptive-branch';
    page.weeks = 2;
    await page.predictDemand();
    await page.segmentCustomers();
    page.demoMode.set(true);
    await page.predictDemand();
    await page.segmentCustomers();
    assert.deepEqual(requests, [
      ['demand', { target_period_weeks: 2, use_synthetic_data: false }],
      ['clusters', false],
      ['demand', { target_period_weeks: 2, use_synthetic_data: true }],
      ['clusters', true],
    ]);
    assert.deepEqual(page.forecast(), { forecast: [] });
    assert.deepEqual(page.clusters(), { segments: [] });
    assert.deepEqual(messages, ['Demanda', 'Segmentos', 'Demanda', 'Segmentos']);
    assert.equal(page.error(), '');
    assert.equal(page.loading(), false);
  });
  test('both ML actions project actual API success messages', async () => {
    const { page } = setup();
    await page.predictDemand();
    await page.segmentCustomers();
    assert.deepEqual(messages, ['Pronóstico generado', 'Segmentación generada']);
    assert.equal(page.error(), '');
  });
  test('failed JSON calls preserve API errors and never announce success', async () => {
    for (const [method, action] of [
      ['queryNaturalLanguage', (page) => page.generateReport(true)],
      ['getSmartReport', (page) => page.generateReport()],
      ['predictDemand', (page) => page.predictDemand()],
      ['customerClusters', (page) => page.segmentCustomers()],
    ]) {
      const { page, api } = setup();
      api[method] = () => throwError(() => new http.HttpErrorResponse({ status: 403, error: { message: 'Tu plan no incluye esta función' } }));
      await action(page);
      assert.equal(page.error(), 'Tu plan no incluye esta función');
      assert.deepEqual(messages, []);
      assert.equal(page.loading(), false);
    }
  });
}
main().catch((error) => { console.error(error); process.exitCode = 1; });
