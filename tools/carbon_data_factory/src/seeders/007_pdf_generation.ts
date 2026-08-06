import { BaseSeeder } from '../core/BaseSeeder';
import { TemplateSelector } from '../core/TemplateSelector';
import { PDFBuilder } from '../core/PDFBuilder';
import { DatabaseWriter } from '../core/DatabaseWriter';
import { v4 as uuidv4 } from 'uuid';

export class PdfGenerationSeeder extends BaseSeeder {
  async run() {
    // Example: generate 10 hotel invoices
    for (let i = 0; i < 10; i++) {
      const selector = new TemplateSelector();
      const templatePath = selector.selectRandom('hotel'); // category: hotel
      const templateHtml = selector.loadTemplate(templatePath);

      // Fake data for placeholders
      const data = {
        hotel_name: `Hotel ${i}`,
        guest_name: `Guest ${i}`,
        check_in: '2026-08-01',
        check_out: '2026-08-05',
        total: `${100 + i * 20}`,
        reservation_id: uuidv4()
      };

      // Generate PDF + upload
      const pdfMeta = await PDFBuilder.fromTemplate(
        templateHtml,
        data,
        `hotel_invoice_${data.reservation_id}.pdf`
      );

      // Insert into customer_documents
      await DatabaseWriter.insert('customer_documents', {
        id: uuidv4(),
        organization_id: 'some-org-id', // replace with seeded org
        organization_member_id: 'some-member-id', // replace with seeded member
        file_name: pdfMeta.fileName,
        file_url: pdfMeta.fileUrl,
        file_type: pdfMeta.fileType,
        file_checksum: pdfMeta.fileChecksum,
        document_type_code: 'hotel_invoice',
        billing_period_start: data.check_in,
        billing_period_end: data.check_out,
        created_at: pdfMeta.createdAt
      });

      this.logger.info(`Generated and uploaded PDF: ${pdfMeta.fileName}`);
    }
  }
}
