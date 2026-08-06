import { Logger } from './Logger';

export abstract class BaseSeeder {
  protected logger: Logger;

  constructor() {
    this.logger = new Logger();
  }

  abstract run(): Promise<void>;
}
