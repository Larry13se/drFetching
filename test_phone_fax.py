# -*- coding: utf-8 -*-
import sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

from DR_eval import NPIRegistryService, DoctorProcessor

npi_svc = NPIRegistryService()

# ---- change name/state here to test your own doctors ----
providers = npi_svc.search_providers('John Smith', 'TX', max_results=3)

print()
print('=== PROVIDER RESULTS ===')
for p in providers:
    print('  Name      :', p.get('fullName'))
    print('  NPI       :', p.get('npi'))
    print('  Address   :', p.get('practiceAddress'), '|', p.get('practiceCity'), p.get('practiceState'), p.get('practiceZip'))
    print('  Phone     :', p.get('practicePhone') or '(none)')
    print('  Fax       :', p.get('practiceFax') or '(none)')
    print('  Specialty :', p.get('primaryTaxonomyName'))
    print()

# ---- also test format_doctor_data output ----
print('=== FORMAT_DOCTOR_DATA OUTPUT (what goes into CSV) ===')
if providers:
    processor = DoctorProcessor.__new__(DoctorProcessor)
    formatted = processor.format_doctor_data(providers[0], '123 Main St TX', '2024-01-01', 'Enrolled', 'TAXONOMY_GOOD')
    for k, v in formatted.items():
        print(f'  {k:12}: {v}')
