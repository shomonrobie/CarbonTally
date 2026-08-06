import { BaseSeeder } from '../core/BaseSeeder';
import { DatabaseWriter } from '../core/DatabaseWriter';
import { v4 as uuidv4 } from 'uuid';
import { faker } from '@faker-js/faker';

export class FacilitiesSeeder extends BaseSeeder {
  async run() {
    const orgs = await DatabaseWriter.selectAll('organizations');

    for (const org of orgs) {
      // Seed 2 facilities per organization
      for (let i = 0; i < 2; i++) {
        await DatabaseWriter.insert('facilities', {
          id: uuidv4(),
          organization_id: org.id,
          name: `${org.name} Facility ${i + 1}`,
          postcode: faker.location.zipCode(),
          city: faker.location.city(),
          country: faker.location.country(),
          created_at: new Date(),
          updated_at: new Date(),
          is_active: true,
          type: faker.helpers.arrayElement(['office', 'factory', 'hotel', 'warehouse'])
        });
      }
    }

    this.logger.info('Seeded facilities for all organizations');
  }
}
