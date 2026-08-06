import { defineConfig } from "@snaplet/seed/config";
import { SeedPrisma } from "@snaplet/seed/adapter-prisma";
import { PrismaPg } from "@prisma/adapter-pg";
import { Client } from "pg";
import { PrismaClient } from "./node_modules/.prisma/client"; 

export default defineConfig({
  adapter: async () => {
    const client = new Client({
      connectionString: "postgresql://postgres:postgres@127.0.0.1:54326/postgres",
    });
    const adapter = new PrismaPg(client);
    const prisma = new PrismaClient({ adapter });
    return new SeedPrisma(prisma);
  },
  select: [
    "public.*",       // ✅ Automatically mock everything in your public tables
    "auth.users",     // ✅ Keep the main user table for relational constraints
    "!auth.*",        // ❌ Drop all other internal auth system logs that crash Snaplet
    "!storage.*",     // ❌ Drop internal storage buckets
    "!extensions.*"   // ❌ Drop internal database extension graphs
  ],
});
