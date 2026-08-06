import { BaseSeeder } from '../core/BaseSeeder';
import { DatabaseWriter } from '../core/DatabaseWriter';
import { v4 as uuidv4 } from 'uuid';
import { faker } from '@faker-js/faker';

export class EmissionsSeeder extends BaseSeeder {
  async run() {
    const orgs = await DatabaseWriter.selectAll('organizations');
    const facilities = await DatabaseWriter.selectAll('facilities');
    const assets = await DatabaseWriter.selectAll('assets');
    const factors = await DatabaseWriter.selectAll('emission_factors');
    const documents = await DatabaseWriter.selectAll('customer_documents');

    for (const doc of documents) {
      // Pick a random emission factor
      const factor = faker.helpers.arrayElement(factors);

      // Generate a random raw quantity (e.g. kWh, liters, etc.)
      const rawQuantity = faker.number.int({ min: 10, max: 1000 });

      // Calculate emissions
      const calculatedKgCo2e = rawQuantity * Number(factor.co2e_multiplier);

      await DatabaseWriter.insert('emissions_logs', {
        id: uuidv4(),
        organization_id: doc.organization_id,
        asset_id: faker.helpers.arrayElement(assets).id,
        customer_document_id: doc.id,
        organization_member_id: doc.organization_member_id,
        supplier_id: doc.supplier_id,
        product_category_id: doc.product_category_id,
        start_date: doc.billing_period_start || faker.date.past(),
        end_date: doc.billing_period_end || faker.date.recent(),
        raw_quantity: rawQuantity,
        calculated_kg_co2e: calculatedKgCo2e,
        created_by_user_id: faker.helpers.arrayElement(orgs).id, // replace with seeded user
        created_at: new Date(),
        updated_at: new Date(),
        emission_factor_id: factor.id,
        unit: factor.unit,
        scope: factor.scope,
        data_source: 'seed_generator',
        confidence_score: faker.number.float({ min: 80, max: 100 })
      });

      this.logger.info(
        `Inserted emissions log for document ${doc.file_name} → ${calculatedKgCo2e} kgCO2e`
      );
    }
  }
}
