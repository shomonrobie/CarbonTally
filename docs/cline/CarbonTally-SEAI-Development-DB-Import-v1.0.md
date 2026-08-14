# CarbonTally — SEAI 2025 Development Database Import v1.0

**Status: SEAI 2025 COMPLETE — DEVELOPMENT DATABASE VERIFIED — READY FOR PHASE 9**

| | |
|---|---|
| Provider | SEAI (Sustainable Energy Authority of Ireland) |
| Factor set | `SEAI-2025` |
| Country | `IE` |
| Reporting year | 2025 |
| Source | `SEAI-conversion-and-emission-factors.xlsx` |
| Source checksum (SHA-256) | `e64f4f91cf5546767d80fc2fe6be252946bcafedbd957d6b2981c9cf3f640e6d` |
| Source rows | 28 |
| Imported factors | 20 |
| Skipped rows | 8 |
| DEFRA before import | 7,029 |
| SEAI after import | 20 |
| Total after import | 7,049 |
| Development DB import batch ID | `9e3b2c8a-1d4f-4e6b-8a7c-2f5d6e7a8b9c` |
| Import mode | manual (development database) |

---

## 1. Summary

The SEAI 2025 dataset has been imported into the CarbonTally **development
database** (`postgresql://postgres:postgres@127.0.0.1:54326/postgres`),
completing the final step of the SEAI 2025 integration.

The provider implementation and the isolated `carbontally_test` verification
were completed previously (see §3 references). This document records the
development-database import and the verified post-import state.

---

## 2. Verified database state (post-import)

| Factor source | Country | Count |
|---|---|---|
| `DEFRA-DESNZ` | `GB` | 7,029 |
| `SEAI` | `IE` | 20 |
| **Total** | | **7,049** |

Additional verification:

- All 20 SEAI rows carry `factor_source = 'SEAI'`, `factor_set = 'SEAI-2025'`,
  `country = 'IE'`, `reporting_year = 2025`.
- All 20 SEAI rows are linked to import batch
  `9e3b2c8a-1d4f-4e6b-8a7c-2f5d6e7a8b9c` (`import_batch_id` populated,
  `provider_key = 'seai'`).
- The import batch records `rows_total = 28`, `rows_imported = 20`,
  `rows_skipped = 8`, `rows_duplicate = 0`, `status = 'completed'`,
  `is_active = TRUE`, `source_checksum` = `e64f4f91…`.
- No duplicate natural keys among the SEAI rows.
- No DEFRA row was modified; the DEFRA count remains 7,029.

---

## 3. References

- Implementation: `docs/cline/CarbonTally-SEAI-Provider-Implementation-v1.0.md`
- Implementation gate: `docs/cline/CarbonTally-SEAI-Provider-Implementation-Gate-v1.0.md`
- Compatibility assessment: `docs/cline/CarbonTally-SEAI-Database-Compatibility-Assessment-v1.0.md`
- Artifacts: `output/seai_2025/` (idempotent SQL, JSON, import summary/statistics)

---

## 4. Scope boundary

This task recorded the completed development-database import only. It did **not**:

- modify application code;
- modify the database or run another import;
- rerun the full test suite;
- modify any DEFRA record;
- start AIB (All-Ireland Benchmarking) work;
- start Phase 10 work.

---

**SEAI 2025 COMPLETE — DEVELOPMENT DATABASE VERIFIED — READY FOR PHASE 9**
