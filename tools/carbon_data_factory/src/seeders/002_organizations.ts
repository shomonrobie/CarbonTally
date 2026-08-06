import { BaseSeeder } from '../core/BaseSeeder';
import { DatabaseWriter } from '../core/DatabaseWriter';
import { v4 as uuidv4 } from 'uuid';
import { faker } from '@faker-js/faker';

export class OrganizationsSeeder extends BaseSeeder {
  async run() {
    for (let i = 0; i < 5; i++) {
      await DatabaseWriter.insert('organizations', {
        id: uuidv4(),
        name: faker.company.name(),
        industry: faker.commerce.department(),
        country: faker.location.country(),
        created_at: new Date(),
        updated_at: new Date(),
        is_active: true
      });
    }
    this.logger.info('Seeded 5 organizations');
  }
}
