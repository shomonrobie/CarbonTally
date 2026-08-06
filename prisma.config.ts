import "dotenv/config";
import { defineConfig } from "prisma/config";

export default defineConfig({
  schema: "prisma/schema.prisma",
  migrations: {
    path: "prisma/migrations",
  },
  datasource: {
    // Explicitly connect to your active local Supabase container port (54326)
    url: "postgresql://postgres:postgres@127.0.0.1:54326/postgres",
  },
});