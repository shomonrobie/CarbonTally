import { faker } from '@faker-js/faker';

export class Random {
  static int(min: number, max: number): number {
    return faker.number.int({ min, max });
  }

  static float(min: number, max: number): number {
    return faker.number.float({ min, max });
  }

  static pick<T>(arr: T[]): T {
    return faker.helpers.arrayElement(arr);
  }

  static uuid(): string {
    return faker.string.uuid();
  }

  static datePast(): Date {
    return faker.date.past();
  }

  static dateRecent(): Date {
    return faker.date.recent();
  }
}
