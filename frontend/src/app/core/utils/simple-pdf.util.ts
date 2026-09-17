import { jsPDF } from 'jspdf';
import autoTable from 'jspdf-autotable';

type SimplePdfReport = {
  filename: string;
  title: string;
  generatedAt: string;
  filters: string[][];
  columns: string[];
  rows: string[][];
};

export function downloadSimplePdf(report: SimplePdfReport): void {
  const doc = new jsPDF({ unit: 'mm', format: 'a4', orientation: 'landscape' });
  const pageWidth = doc.internal.pageSize.getWidth();

  doc.setFontSize(16);
  doc.setFont('helvetica', 'bold');
  doc.text(report.title, 14, 16);

  doc.setFontSize(9);
  doc.setFont('helvetica', 'normal');
  doc.text(`Generado: ${report.generatedAt}`, 14, 23);

  const filterLines = report.filters.map(([label, value]) => `${label}: ${value}`);
  const filterText = doc.splitTextToSize(filterLines.join('   •   '), pageWidth - 28);
  if (filterLines.length) {
    doc.text(filterText, 14, 30);
  }

  const body = report.rows.length
    ? report.rows
    : [report.columns.map((_, index) => index === 0 ? 'No hay datos para los filtros seleccionados.' : '')];

  autoTable(doc, {
    head: [report.columns],
    body,
    startY: filterLines.length ? 30 + filterText.length * 4 + 4 : 36,
    margin: { left: 14, right: 14 },
    theme: 'grid',
    styles: {
      font: 'helvetica',
      fontSize: 8,
      cellPadding: 2,
      overflow: 'linebreak',
      lineColor: [180, 180, 180],
      lineWidth: 0.2,
    },
    headStyles: {
      fillColor: [31, 78, 121],
      textColor: [255, 255, 255],
      fontStyle: 'bold',
      halign: 'center',
    },
    bodyStyles: {
      textColor: [35, 35, 35],
      valign: 'top',
    },
    alternateRowStyles: { fillColor: [245, 248, 251] },
    showHead: 'everyPage',
  });

  const pageCount = doc.getNumberOfPages();
  doc.setFontSize(8);
  doc.setTextColor(100, 100, 100);
  for (let page = 1; page <= pageCount; page += 1) {
    doc.setPage(page);
    doc.text(`Página ${page} de ${pageCount}`, pageWidth - 14, doc.internal.pageSize.getHeight() - 8, { align: 'right' });
  }

  doc.save(report.filename);
}
