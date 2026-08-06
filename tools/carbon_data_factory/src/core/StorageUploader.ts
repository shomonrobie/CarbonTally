import { createClient } from '@supabase/supabase-js';
import fs from 'fs';
import path from 'path';

export interface UploadResult {
  fileName: string;
  fileUrl: string;
  bucket: string;
}

export class StorageUploader {
  private static supabase = createClient(
    process.env.SUPABASE_URL as string,
    process.env.SUPABASE_KEY as string
  );

  /**
   * Upload a local file to Supabase storage
   * @param localPath - Path to the file on disk
   * @param bucket - Supabase bucket name (e.g. "documents")
   * @param remotePath - Path inside bucket (e.g. "pdf/invoice_123.pdf")
   */
  static async uploadFile(localPath: string, bucket: string, remotePath: string): Promise<UploadResult> {
    const fileBuffer = fs.readFileSync(localPath);

    const { error } = await this.supabase.storage
      .from(bucket)
      .upload(remotePath, fileBuffer, {
        contentType: 'application/pdf',
        upsert: true
      });

    if (error) {
      throw new Error(`Supabase upload failed: ${error.message}`);
    }

    const { data: publicUrlData } = this.supabase.storage
      .from(bucket)
      .getPublicUrl(remotePath);

    return {
      fileName: path.basename(localPath),
      fileUrl: publicUrlData.publicUrl,
      bucket
    };
  }
}
