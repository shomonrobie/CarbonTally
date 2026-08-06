import { Pool } from 'pg';

export class DatabaseWriter {
  private static pool = new Pool({
    connectionString: process.env.DATABASE_URL
  });

  static async insert(table: string, data: Record<string, any>) {
    const keys = Object.keys(data);
    const values = Object.values(data);
    const placeholders = keys.map((_, i) => `$${i + 1}`).join(', ');

    const query = `INSERT INTO ${table} (${keys.join(', ')}) VALUES (${placeholders})`;
    await this.pool.query(query, values);
  }

  static async selectAll(table: string) {
    const result = await this.pool.query(`SELECT * FROM ${table}`);
    return result.rows;
  }
}
