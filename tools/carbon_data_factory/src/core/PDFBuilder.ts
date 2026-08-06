import fs from 'fs';
import path from 'path';
import crypto from 'crypto';
import puppeteer from 'puppeteer';
import { StorageUploader } from './StorageUploader';

export interface PDFMetadata {
  fileName: string;
  filePath: string;
  fileUrl: string;
  fileType: string;
  fileChecksum: string;
  createdAt: Date;
}

export class PDFBuilder {
  static async htmlToPdf(htmlContent: string, outputFileName: string): Promise<PDFMetadata> {
    const browser = await puppeteer.launch({ headless: 'new' });
    const page = await browser.newPage();
    await page.setContent(htmlContent, { waitUntil: 'networkidle0' });

    const outputDir = path.join(__dirname, '..', '..', 'storage', 'documents', 'pdf');
    if (!fs.existsSync(outputDir)) {
      fs.mkdirSync(outputDir, { recursive: true });
    }

    const outputPath = path.join(outputDir, outputFileName);
    await page.pdf({ path: outputPath, format: 'A4', printBackground: true });
    await browser.close();

    const fileBuffer = fs.readFileSync(outputPath);
    const checksum = crypto.createHash('sha256').update(fileBuffer).digest('hex');

    // Upload to Supabase
    const uploadResult = await StorageUploader.uploadFile(
      outputPath,
      'documents', // Supabase bucket name
      `pdf/${outputFileName}`
    );

    return {
      fileName: outputFileName,
      filePath: outputPath,
      fileUrl: uploadResult.fileUrl,
      fileType: 'application/pdf',
      fileChecksum: checksum,
      createdAt: new Date()
    };
  }
  


/**
   * Render a template with placeholders replaced by data
   * @param templateHtml - HTML template string with {{placeholders}}
   * @param data - Key/value pairs to replace in template
   * @param outputFileName - Desired output filename
   * @returns PDFMetadata object
   */
  static async fromTemplate(templateHtml: string, data: Record<string, string>, outputFileName: string): Promise<PDFMetadata> {
    let rendered = templateHtml;
    for (const [key, value] of Object.entries(data)) {
      const regex = new RegExp(`{{${key}}}`, 'g');
      rendered = rendered.replace(regex, value);
    }
    return await PDFBuilder.htmlToPdf(rendered, outputFileName);
  }
}
