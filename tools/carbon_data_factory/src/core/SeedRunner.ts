import { Logger } from './Logger';

// Import all seeders
import { UsersSeeder } from '../seeders/001_users';
import { OrganizationsSeeder } from '../seeders/002_organizations';
import { FacilitiesSeeder } from '../seeders/003_facilities';
import { AssetsSeeder } from '../seeders/004_assets';
import { DocumentTypesSeeder } from '../seeders/005_document_types';
import { PdfGenerationSeeder } from '../seeders/007_pdf_generation';
import { EmissionsSeeder } from '../seeders/010_emissions';
import { ReportsSeeder } from '../seeders/011_reports';

export class SeedRunner {
  private logger = new Logger();

  private seeders = [
    { name: 'Users', seeder: new UsersSeeder() },
    { name: 'Organizations', seeder: new OrganizationsSeeder() },
    { name: 'Facilities', seeder: new FacilitiesSeeder() },
    { name: 'Assets', seeder: new AssetsSeeder() },
    { name: 'Document Types', seeder: new DocumentTypesSeeder() },
    { name: 'PDF Generation', seeder: new PdfGenerationSeeder() },
    { name: 'Emissions', seeder: new EmissionsSeeder() },
    { name: 'Reports', seeder: new ReportsSeeder() }
  ];

  async runAll() {
    for (const { name, seeder } of this.seeders) {
      try {
        this.logger.info(`➡️ Running ${name} seeder...`);
        await seeder.run();
        this.logger.info(`✅ Completed ${name} seeder`);
      } catch (err) {
        this.logger.error(`❌ Failed ${name} seeder: ${err}`);
      }
    }
    this.logger.info('🎉 All seeders completed');
  }
}

// Entry point
(async () => {
  const runner = new SeedRunner();
  await runner.runAll();
})();
