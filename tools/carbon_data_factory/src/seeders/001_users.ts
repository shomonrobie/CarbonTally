import { BaseSeeder } from '../core/BaseSeeder';
import { DatabaseWriter } from '../core/DatabaseWriter';
import { v4 as uuidv4 } from 'uuid';
import { faker } from '@faker-js/faker';

export class UsersSeeder extends BaseSeeder {
  async run() {
    for (let i = 0; i < 10; i++) {
      await DatabaseWriter.insert('users', {
        id: uuidv4(),
        email: faker.internet.email(),
        password_hash: faker.string.alphanumeric(32),
        first_name: faker.person.firstName(),
        last_name: faker.person.lastName(),
        user_type: 'member',
        is_active: true,
        email_verified: true,
        created_at: new Date(),
        updated_at: new Date()
      });
    }
    this.logger.info('Seeded 10 users');
  }
}
