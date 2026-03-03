import requests
import time
import json
import os
import csv
import re
from datetime import datetime

class NPIRegistryService:
    def __init__(self):
        self.base_url = 'https://npiregistry.cms.hhs.gov/api/'
        self.max_retries = 5
        self.retry_delay = 1.0
        self.pecos_file = 'pecos_data.json'
        self.pecos_data = self.load_pecos_data()

    def load_pecos_data(self):
        """Load PECOS dataset from local JSON file."""
        if not os.path.exists(self.pecos_file):
            print(f"⚠️ PECOS dataset file not found: {self.pecos_file}")
            return []
        try:
            with open(self.pecos_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            print(f"📂 Loaded {len(data)} providers from PECOS dataset")
            return data
        except Exception as e:
            print(f"❌ Error loading PECOS dataset: {e}")
            return []

    def search_providers(self, provider_name, state=None, max_results=10):
        # Create debug info dictionary to track the search process
        debug_info = {
            'original_name': provider_name,
            'original_state': state,
            'parsed_first_name': '',
            'parsed_last_name': '',
            'api_first_name_param': '',
            'api_last_name_param': '',
            'api_state_param': '',
            'api_response_count': 0,
            'api_error': None,
            'used_pecos_fallback': False,
            'pecos_matches': 0
        }
        
        # Parse name: Assume "LAST, FIRST" or "LAST FIRST"
        name_parts = provider_name.strip().split(',')
        if len(name_parts) == 2:
            last_name = name_parts[0].strip()
            first_name = name_parts[1].strip()
        else:
            name_parts = provider_name.strip().split()
            if len(name_parts) >= 2:
                first_name = name_parts[0]
                last_name = ' '.join(name_parts[1:])
            else:
                first_name = ''
                last_name = provider_name.strip()

        # Remove middle initials/names (single letters or short words)
        first_name = self.remove_middle_initial(first_name)

        # Store parsed names
        debug_info['parsed_first_name'] = first_name
        debug_info['parsed_last_name'] = last_name

        # Add wildcards for fuzzy matching
        first_name_search = f"{first_name}*" if first_name else ''
        last_name_search = f"{last_name}*" if last_name else ''
        
        # Store API parameters
        debug_info['api_first_name_param'] = first_name_search
        debug_info['api_last_name_param'] = last_name_search
        debug_info['api_state_param'] = state.upper() if state else ''

        print(f"🔍 Searching CMS NPI Registry for: First='{first_name_search}', Last='{last_name_search}' {f'in {state}' if state else ''}")

        # Try CMS NPI API
        try:
            params = {
                'version': '2.1',
                'first_name': first_name_search,
                'last_name': last_name_search,
                'enumeration_type': 'NPI-1',
                'limit': max_results
            }
            if state:
                params['state'] = state.upper()
            
            response = self.make_request(params)
            data = response.json()
            result_count = data.get('result_count', 0)
            debug_info['api_response_count'] = result_count
            
            print(f"📊 CMS API Response: Found {result_count} total matches, returning {min(result_count, max_results)} results")
            providers = self.parse_api_response(data, state)
            if providers:
                # Add debug info to each provider
                for provider in providers:
                    provider['_debug_info'] = debug_info
                return providers
            print("⚠️ No matches in CMS API, falling back to PECOS dataset")
        except Exception as e:
            print(f"❌ Error searching CMS NPI Registry: {e}")
            debug_info['api_error'] = str(e)
            print("⚠️ Falling back to PECOS dataset")

        # Fallback to PECOS dataset
        debug_info['used_pecos_fallback'] = True
        providers = self.search_pecos_dataset(first_name, last_name, state, max_results)
        debug_info['pecos_matches'] = len(providers)
        
        # Add debug info to each provider
        for provider in providers:
            provider['_debug_info'] = debug_info
            
        return providers

    def remove_middle_initial(self, name):
        """Remove middle initials and middle names from first name"""
        if not name:
            return name
        
        parts = name.split()
        if len(parts) <= 1:
            return name
        
        # Keep only the first part, remove middle initials/names
        return parts[0]

    def extract_state_from_address(self, address):
        """Extract state abbreviation from address string"""
        if not address or address.lower() == "not available":
            return None
        
        # Look for state pattern (2 uppercase letters followed by zip)
        state_pattern = r'\b([A-Z]{2})\s+\d{5}'
        match = re.search(state_pattern, address.upper())
        if match:
            return match.group(1)
        
        # Alternative pattern: look for state at end of address
        parts = address.upper().split(',')
        if len(parts) >= 2:
            last_part = parts[-1].strip()
            state_match = re.match(r'([A-Z]{2})\s+\d{5}', last_part)
            if state_match:
                return state_match.group(1)
        
        return None

    def search_pecos_dataset(self, first_name, last_name, state, max_results):
        """Search local PECOS dataset for matching providers."""
        providers = []
        first_name = first_name.lower().strip()
        last_name = last_name.lower().strip()
        state = state.upper().strip() if state else None

        for record in self.pecos_data:
            record_first = record.get('FIRST_NAME', '').lower().strip()
            record_last = record.get('LAST_NAME', '').lower().strip()
            record_state = record.get('STATE_CD', '').upper().strip()

            # Match names (partial) and state (if provided)
            if ((not first_name or first_name in record_first or record_first in first_name) and
                (not last_name or last_name in record_last or record_last in last_name) and
                (not state or state == record_state)):
                provider_data = {
                    'npi': record.get('NPI', ''),
                    'fullName': f"{record.get('FIRST_NAME', '')} {record.get('LAST_NAME', '')}".strip(),
                    'firstName': record.get('FIRST_NAME', ''),
                    'lastName': record.get('LAST_NAME', ''),
                    'credential': '',
                    'gender': '',
                    'providerType': record.get('PROVIDER_TYPE_DESC', ''),
                    'practiceAddress': '',
                    'practiceCity': '',
                    'practiceState': record_state,
                    'practiceZip': '',
                    'practicePhone': '',
                    'practiceFax': '',
                    'licenses': [{
                        'taxonomy': {
                            'code': record.get('PROVIDER_TYPE_CD', ''),
                            'classification': record.get('PROVIDER_TYPE_DESC', ''),
                            'specialization': '',
                            'primary': 'Y'
                        },
                        'license_number': '',
                        'state': record_state
                    }],
                    'primaryTaxonomyCode': record.get('PROVIDER_TYPE_CD', ''),
                    'primaryTaxonomyName': record.get('PROVIDER_TYPE_DESC', ''),
                    'licenseNumber': '',
                    'licenseState': record_state
                }
                providers.append(provider_data)
                print(f"✅ Parsed PECOS provider: {provider_data['fullName']} ({provider_data['npi']}) - {provider_data['practiceState']}")
                if len(providers) >= max_results:
                    break

        print(f"📊 PECOS Dataset: Found {len(providers)} matches")
        return providers

    def get_provider_by_npi(self, npi_number):
        print(f"🔍 Looking up NPI: {npi_number}")
        params = {
            'version': '2.1',
            'number': npi_number,
            'enumeration_type': 'NPI-1'
        }
        try:
            response = self.make_request(params)
            data = response.json()
            providers = self.parse_api_response(data)
            if providers:
                return providers[0]
            print("⚠️ No CMS API match for NPI, checking PECOS dataset")
        except Exception as e:
            print(f"❌ Error looking up NPI {npi_number} in CMS API: {e}")
            print("⚠️ Falling back to PECOS dataset")

        for record in self.pecos_data:
            if record.get('NPI') == npi_number:
                provider_data = {
                    'npi': record.get('NPI', ''),
                    'fullName': f"{record.get('FIRST_NAME', '')} {record.get('LAST_NAME', '')}".strip(),
                    'firstName': record.get('FIRST_NAME', ''),
                    'lastName': record.get('LAST_NAME', ''),
                    'credential': '',
                    'gender': '',
                    'providerType': record.get('PROVIDER_TYPE_DESC', ''),
                    'practiceAddress': '',
                    'practiceCity': '',
                    'practiceState': record.get('STATE_CD', ''),
                    'practiceZip': '',
                    'practicePhone': '',
                    'practiceFax': '',
                    'licenses': [{
                        'taxonomy': {
                            'code': record.get('PROVIDER_TYPE_CD', ''),
                            'classification': record.get('PROVIDER_TYPE_DESC', ''),
                            'specialization': '',
                            'primary': 'Y'
                        },
                        'license_number': '',
                        'state': record.get('STATE_CD', '')
                    }],
                    'primaryTaxonomyCode': record.get('PROVIDER_TYPE_CD', ''),
                    'primaryTaxonomyName': record.get('PROVIDER_TYPE_DESC', ''),
                    'licenseNumber': '',
                    'licenseState': record.get('STATE_CD', '')
                }
                print(f"✅ Parsed PECOS provider: {provider_data['fullName']} ({provider_data['npi']}) - {provider_data['practiceState']}")
                return provider_data
        print(f"❌ No match found for NPI {npi_number} in PECOS dataset")
        return None

    def parse_api_response(self, api_data, target_state=None):
        try:
            results = api_data.get('results', [])
            if not results:
                return []
            
            providers = []
            for result in results:
                provider_data = {
                    'npi': result.get('number', ''),
                    'fullName': result.get('basic', {}).get('name', '') or f"{result.get('basic', {}).get('first_name', '')} {result.get('basic', {}).get('last_name', '')}".strip(),
                    'firstName': result.get('basic', {}).get('first_name', ''),
                    'lastName': result.get('basic', {}).get('last_name', ''),
                    'credential': result.get('basic', {}).get('credential', ''),
                    'gender': result.get('basic', {}).get('gender', ''),
                    'providerType': '',
                    'practiceAddress': '',
                    'practiceCity': '',
                    'practiceState': '',
                    'practiceZip': '',
                    'practicePhone': '',
                    'practiceFax': '',
                    'licenses': []
                }

                addresses = result.get('addresses', [])
                practice_addr = next((addr for addr in addresses if addr.get('address_type') == 'LOCATION'), addresses[0] if addresses else None)
                if practice_addr:
                    provider_data['practiceAddress'] = f"{practice_addr.get('address_1', '')} {practice_addr.get('address_2', '')}".strip()
                    provider_data['practiceCity'] = practice_addr.get('city', '')
                    provider_data['practiceState'] = practice_addr.get('state', '')
                    provider_data['practiceZip'] = practice_addr.get('postal_code', '')[:5]
                    provider_data['practicePhone'] = practice_addr.get('telephone_number', '')
                    provider_data['practiceFax'] = practice_addr.get('fax_number', '')

                if target_state and provider_data['practiceState'] != target_state:
                    print(f"⏭️ Skipping provider {provider_data['fullName']} - wrong state ({provider_data['practiceState']}, need {target_state})")
                    continue

                taxonomies = result.get('taxonomies', [])
                provider_data['licenses'] = [
                    {
                        'taxonomy': {
                            'code': tax.get('code', ''),
                            'classification': tax.get('desc', ''),
                            'specialization': tax.get('specialization', ''),
                            'primary': 'Y' if tax.get('primary') else 'N'
                        },
                        'license_number': tax.get('license', ''),
                        'state': tax.get('state', '')
                    } for tax in taxonomies
                ]

                if provider_data['licenses']:
                    primary_tax = next((lic for lic in provider_data['licenses'] if lic['taxonomy']['primary'] == 'Y'), provider_data['licenses'][0])
                    provider_data['providerType'] = primary_tax['taxonomy']['classification']
                    provider_data['primaryTaxonomyCode'] = primary_tax['taxonomy']['code']
                    provider_data['primaryTaxonomyName'] = primary_tax['taxonomy']['classification'] or primary_tax['taxonomy']['specialization']
                    provider_data['licenseNumber'] = primary_tax['license_number']
                    provider_data['licenseState'] = primary_tax['state']

                providers.append(provider_data)
                print(f"✅ Parsed CMS provider: {provider_data['fullName']} ({provider_data['npi']}) - {provider_data['practiceState']}")

            return providers
        except Exception as e:
            print(f"❌ Error parsing CMS API response: {e}")
            return []

    def make_request(self, params):
        current_delay = self.retry_delay
        last_error = None
        for attempt in range(1, self.max_retries + 1):
            print(f"📡 API Request attempt {attempt}/{self.max_retries}")
            try:
                response = requests.get(self.base_url, params=params, headers={
                    'User-Agent': 'Medicare-Doctor-Automation/1.0.0'
                }, timeout=30)
                response.raise_for_status()
                return response
            except Exception as e:
                last_error = e
                print(f"⚠️ Attempt {attempt} failed: {e}")
                if attempt < self.max_retries:
                    print(f"⏳ Waiting {current_delay}s before retry...")
                    time.sleep(current_delay)
                    current_delay *= 2
        raise last_error

    def validate_provider_basic_criteria(self, provider):
        validation_result = {'isValid': True, 'reasons': [], 'warnings': []}
        
        if not provider.get('npi'):
            validation_result['isValid'] = False
            validation_result['reasons'].append('Missing NPI number')
        
        if not (provider.get('fullName') or provider.get('firstName') or provider.get('lastName')):
            validation_result['isValid'] = False
            validation_result['reasons'].append('Missing provider name')
        
        if not provider.get('practiceState'):
            validation_result['isValid'] = False
            validation_result['reasons'].append('Missing practice state')
        
        if provider.get('providerType') and 'organization' in provider.get('providerType', '').lower():
            validation_result['isValid'] = False
            validation_result['reasons'].append('Provider is an organization, not individual')
        
        if not provider.get('practicePhone'):
            validation_result['warnings'].append('Missing practice phone number')
        
        if not provider.get('primaryTaxonomyCode'):
            validation_result['warnings'].append('Missing taxonomy/specialty information')
        
        return validation_result

class PECOSEnrollmentService:
    def __init__(self):
        self.base_url = 'https://data.cms.gov/data-api/v1/dataset'
        self.dataset_id = '2457ea29-fc82-48b0-86ec-3b0755de7515'
        self.rate_limit_delay = 0.5

    def check_provider_enrollment(self, npi):
        print(f"🔍 Checking PECOS enrollment for NPI: {npi}")
        
        pecos_debug_info = {
            'npi_checked': npi,
            'api_endpoint': f"{self.base_url}/{self.dataset_id}/data",
            'filter_used': f"NPI eq '{npi}'",
            'api_response': None,
            'api_error': None,
            'records_found': 0
        }
        
        if not npi or len(npi) != 10 or not npi.isdigit():
            print(f"❌ Invalid NPI format: {npi}")
            pecos_debug_info['api_error'] = 'Invalid NPI format'
            return {
                'isEnrolled': False, 
                'status': 'Invalid NPI', 
                'error': 'NPI must be 10 digits',
                '_pecos_debug_info': pecos_debug_info
            }
        
        time.sleep(self.rate_limit_delay)
        
        try:
            response = requests.get(f"{self.base_url}/{self.dataset_id}/data", params={
                '$filter': f"NPI eq '{npi}'",
                '$top': 1
            }, timeout=30, headers={
                'User-Agent': 'Medicare-Automation/1.0',
                'Accept': 'application/json'
            })
            response.raise_for_status()
            data = response.json()
            
            pecos_debug_info['api_response'] = f"HTTP {response.status_code}"
            pecos_debug_info['records_found'] = len(data) if data else 0
            
            if data and len(data) > 0:
                provider_data = data[0]
                enrollment_status = self.parse_enrollment_status(provider_data)
                print(f"✅ PECOS data found for NPI {npi}:")
                print(f"   📋 Status: {enrollment_status['status']}")
                print(f"   📅 Enrollment Date: {enrollment_status['enrollmentDate'] or 'Not available'}")
                print(f"   🏥 Provider Type: {enrollment_status['providerType'] or 'Not specified'}")
                return {
                    'isEnrolled': enrollment_status['isActive'],
                    'status': enrollment_status['status'],
                    'enrollmentDate': enrollment_status['enrollmentDate'],
                    'providerType': enrollment_status['providerType'],
                    'deactivationDate': enrollment_status['deactivationDate'],
                    'rawData': provider_data,
                    'dataSource': 'CMS API',
                    '_pecos_debug_info': pecos_debug_info
                }
            else:
                print(f"❌ Provider NPI {npi} not found in PECOS database - NOT ENROLLED")
                return {
                    'isEnrolled': False,
                    'status': 'Not Found in PECOS',
                    'error': 'Provider not found in Medicare PECOS enrollment database',
                    'dataSource': 'CMS API',
                    'enrollmentDate': None,
                    'providerType': 'Unknown',
                    '_pecos_debug_info': pecos_debug_info
                }
        except Exception as e:
            pecos_debug_info['api_error'] = str(e)
            print(f"❌ Error checking PECOS enrollment for NPI {npi}: {e}")
            return self.alternative_enrollment_check(npi, pecos_debug_info)

    def alternative_enrollment_check(self, npi, debug_info=None):
        print(f"🔄 Using alternative enrollment verification for NPI: {npi}")
        
        if debug_info is None:
            debug_info = {'fallback_used': True}
        else:
            debug_info['fallback_used'] = True
            
        is_valid_npi = self.validate_npi_checksum(npi)
        debug_info['npi_checksum_valid'] = is_valid_npi
        
        if is_valid_npi:
            print(f"✅ NPI {npi} passes validation - UNKNOWN enrollment status (API unavailable)")
            return {
                'isEnrolled': None,
                'status': 'Unknown - API Unavailable',
                'error': 'CMS PECOS API unavailable - cannot verify enrollment',
                'dataSource': 'NPI Validation Fallback',
                'enrollmentDate': None,
                'providerType': 'Unknown',
                '_pecos_debug_info': debug_info
            }
        else:
            print(f"❌ NPI {npi} fails validation - Invalid NPI")
            return {
                'isEnrolled': False,
                'status': 'Invalid NPI',
                'error': 'NPI failed checksum validation',
                'dataSource': 'NPI Validation',
                '_pecos_debug_info': debug_info
            }

    def validate_npi_checksum(self, npi):
        if not npi.isdigit() or len(npi) != 10:
            return False
        full_number = '80840' + npi
        sum_val = 0
        alternate = False
        for i in range(len(full_number) - 1, -1, -1):
            digit = int(full_number[i])
            if alternate:
                digit *= 2
                if digit > 9:
                    digit = (digit % 10) + 1
            sum_val += digit
            alternate = not alternate
        return sum_val % 10 == 0

    def parse_enrollment_status(self, provider_data):
        status = 'Enrolled'
        enrollment_date = None
        deactivation_date = None
        provider_type = provider_data.get('PROVIDER_TYPE_DESC', 'Unknown')
        is_active = True
        return {
            'status': status,
            'isActive': is_active,
            'enrollmentDate': enrollment_date,
            'deactivationDate': deactivation_date,
            'providerType': provider_type
        }

class TaxonomyBasedSpecialtyValidator:
    """Updated specialty validator using taxonomy codes from CSV file"""
    
    def __init__(self, taxonomy_file='taxonomy.csv', bad_specs_file='bad specs.csv'):
        self.taxonomy_file = taxonomy_file
        self.bad_specs_file = bad_specs_file
        
        # Taxonomy-based data
        self.taxonomy_lookup = {}  # taxonomy_code -> category (GOOD/BAD)
        self.taxonomy_descriptions = {}  # taxonomy_code -> description
        
        # CN specialties (keyword-based search)
        self.cn_keywords = set()  # Keywords to search in description
        
        self.load_taxonomy_data()
        self.load_cn_specialties()
        
    def load_taxonomy_data(self):
        """Load taxonomy data from CSV file"""
        if not os.path.exists(self.taxonomy_file):
            print(f"⚠️ Taxonomy file not found: {self.taxonomy_file}")
            self.create_example_taxonomy_file()
            return
            
        encodings = ['utf-8', 'utf-8-sig', 'windows-1252', 'latin1', 'cp1252']
        
        for enc in encodings:
            try:
                with open(self.taxonomy_file, 'r', encoding=enc) as f:
                    reader = csv.DictReader(f)
                    
                    if not reader.fieldnames:
                        print(f"⚠️ Taxonomy CSV file appears to be empty with encoding {enc}")
                        continue
                    
                    # Find required columns
                    desc_col = None
                    code_col = None
                    cat_col = None
                    
                    for col in reader.fieldnames:
                        col_clean = col.strip().upper()
                        if 'MEDICARE PROVIDER' in col_clean or 'SUPPLIER TYPE DESCRIPTION' in col_clean:
                            desc_col = col
                        elif 'PROVIDER TAXONOMY CODE' in col_clean or 'TAXONOMY CODE' in col_clean:
                            code_col = col
                        elif col_clean in ['CAT', 'CAT.', 'CATEGORY']:
                            cat_col = col
                    
                    if not code_col or not cat_col:
                        print(f"⚠️ Missing required columns in taxonomy file with encoding {enc}")
                        print(f"   Found columns: {reader.fieldnames}")
                        continue
                    
                    temp_taxonomy = {}
                    temp_descriptions = {}
                    row_count = 0
                    
                    for row in reader:
                        row_count += 1
                        
                        taxonomy_code = row.get(code_col, '').strip()
                        category = row.get(cat_col, '').strip().upper()
                        description = row.get(desc_col, '').strip() if desc_col else ''
                        
                        if taxonomy_code and category in ['GOOD', 'BAD']:
                            temp_taxonomy[taxonomy_code] = category
                            if description:
                                temp_descriptions[taxonomy_code] = description
                    
                    if not temp_taxonomy:
                        print(f"⚠️ No valid taxonomy data found with encoding {enc}")
                        continue
                    
                    self.taxonomy_lookup = temp_taxonomy
                    self.taxonomy_descriptions = temp_descriptions
                    
                    print(f"📋 Loaded {len(self.taxonomy_lookup)} taxonomy codes")
                    print(f"📋 GOOD taxonomies: {sum(1 for v in self.taxonomy_lookup.values() if v == 'GOOD')}")
                    print(f"📋 BAD taxonomies: {sum(1 for v in self.taxonomy_lookup.values() if v == 'BAD')}")
                    print(f"📋 Used encoding: {enc}")
                    return
                    
            except Exception as e:
                print(f"❌ Error loading taxonomy file with encoding {enc}: {e}")
                continue
        
        print(f"❌ Could not load taxonomy data from {self.taxonomy_file}")
    
    def load_cn_specialties(self):
        """Load CN specialties from bad specs file for keyword-based search"""
        if not os.path.exists(self.bad_specs_file):
            print(f"⚠️ Bad specs file not found: {self.bad_specs_file}")
            return
            
        encodings = ['utf-8', 'utf-8-sig', 'windows-1252', 'latin1', 'cp1252']
        
        for enc in encodings:
            try:
                with open(self.bad_specs_file, 'r', encoding=enc) as f:
                    reader = csv.DictReader(f)
                    
                    if not reader.fieldnames:
                        continue
                    
                    # Find good for CN column
                    good_cn_col = None
                    for col in reader.fieldnames:
                        col_clean = col.strip().upper()
                        if 'GOOD FOR CN' in col_clean or 'GOODFORCN' in col_clean:
                            good_cn_col = col
                            break
                    
                    if not good_cn_col:
                        print(f"⚠️ No 'good for CN' column found in bad specs file")
                        continue
                    
                    temp_keywords = set()
                    
                    for row in reader:
                        good_specialties = row.get(good_cn_col, '').strip()
                        if good_specialties:
                            # Split by comma and extract keywords
                            for specialty in good_specialties.split(','):
                                specialty = specialty.strip()
                                if specialty:
                                    # Extract meaningful keywords from specialty name
                                    keywords = self.extract_keywords_from_specialty(specialty)
                                    temp_keywords.update(keywords)
                    
                    if temp_keywords:
                        self.cn_keywords = temp_keywords
                        print(f"📋 Loaded CN keywords: {list(self.cn_keywords)}")
                        return
                        
            except Exception as e:
                print(f"❌ Error loading CN specialties with encoding {enc}: {e}")
                continue
        
        print(f"❌ Could not load CN specialties from {self.bad_specs_file}")
    
    def extract_keywords_from_specialty(self, specialty_name):
        """Extract meaningful keywords from specialty name for CN search"""
        keywords = set()
        
        # Clean the specialty name
        specialty_clean = specialty_name.strip().lower()
        
        # Define keyword mapping for common specialties
        keyword_mappings = {
            'chiropractor': ['chiropractic',"chiropractor"],
            'physical therapist': ['physical therapy', 'physiotherap'],
            'sports physician': ['sports medicine', 'sports'],
        }
        
        # Check for direct mappings
        for specialty, mapped_keywords in keyword_mappings.items():
            if specialty in specialty_clean:
                keywords.update(mapped_keywords)
                # Also add the original term
                keywords.add(specialty.replace(' ', ''))
        
        # Add the main words from the specialty name
        words = re.findall(r'\b[a-zA-Z]{3,}\b', specialty_clean)
        keywords.update(words)
        
        return keywords
    
    def create_example_taxonomy_file(self):
        """Create an example taxonomy file"""
        example_data = [
            {
                'MEDICARE PROVIDER/SUPPLIER TYPE DESCRIPTION': 'Physician/Undefined Physician type',
                'PROVIDER TAXONOMY CODE': '208D00000X',
                'SPECIALTY UNI': 'Allopathic & Osteopathic Physicians/General Practice',
                'Cat.': 'GOOD'
            },
            {
                'MEDICARE PROVIDER/SUPPLIER TYPE DESCRIPTION': 'Physician Assistant',
                'PROVIDER TAXONOMY CODE': '363A00000X',
                'SPECIALTY UNI': 'Physician Assistants & Advanced Practice Nursing Providers/Physician Assistant',
                'Cat.': 'GOOD'
            },
            {
                'MEDICARE PROVIDER/SUPPLIER TYPE DESCRIPTION': 'Optometrist',
                'PROVIDER TAXONOMY CODE': '152W00000X',
                'SPECIALTY UNI': 'Eye and Vision Services Providers/Optometrist',
                'Cat.': 'BAD'
            }
        ]
        
        try:
            with open(self.taxonomy_file, 'w', newline='', encoding='utf-8') as f:
                writer = csv.DictWriter(f, fieldnames=example_data[0].keys())
                writer.writeheader()
                writer.writerows(example_data)
            print(f"Created example taxonomy file: {self.taxonomy_file}")
        except Exception as e:
            print(f"Error creating example taxonomy file: {e}")
    
    def evaluate_provider_by_taxonomy(self, provider):
        """
        Evaluate provider using taxonomy-based system
        Returns: (category, reason, is_cn_eligible)
        """
        taxonomy_code = provider.get('primaryTaxonomyCode', '').strip()
        specialty_description = provider.get('primaryTaxonomyName', '').strip()
        medicare_description = provider.get('providerType', '').strip()
        
        evaluation_result = {
            'category': 'UNKNOWN',
            'reason': '',
            'is_cn_eligible': False,
            'taxonomy_code': taxonomy_code,
            'specialty_description': specialty_description,
            'evaluation_method': ''
        }
        
        # Step 1: Check taxonomy code first (most accurate)
        if taxonomy_code and taxonomy_code in self.taxonomy_lookup:
            category = self.taxonomy_lookup[taxonomy_code]
            evaluation_result['category'] = category
            evaluation_result['reason'] = f"Taxonomy code {taxonomy_code} classified as {category}"
            evaluation_result['evaluation_method'] = 'TAXONOMY_CODE'
            
            if category == 'GOOD':
                return evaluation_result
            elif category == 'BAD':
                # Check if it's good for CN despite being bad taxonomy
                is_cn = self.is_good_for_cn_by_description(medicare_description)
                evaluation_result['is_cn_eligible'] = is_cn
                if is_cn:
                    evaluation_result['reason'] += " but eligible for CN"
                return evaluation_result
        
        # Step 2: Check CN eligibility by description keyword search
        is_cn = self.is_good_for_cn_by_description(medicare_description)
        if is_cn:
            evaluation_result['category'] = 'CN_ELIGIBLE'
            evaluation_result['is_cn_eligible'] = True
            evaluation_result['reason'] = f"Good for CN based on description: {medicare_description}"
            evaluation_result['evaluation_method'] = 'CN_KEYWORD_SEARCH'
            return evaluation_result
        
        # Step 3: Default - unknown taxonomy
        evaluation_result['category'] = 'UNKNOWN'
        evaluation_result['reason'] = f"Taxonomy code {taxonomy_code} not found in reference file"
        evaluation_result['evaluation_method'] = 'UNKNOWN_TAXONOMY'
        
        return evaluation_result
    
    def is_good_for_cn_by_description(self, description):
        """Check if provider is good for CN using keyword search in description"""
        if not description or not self.cn_keywords:
            return False
        
        description_lower = description.lower()
        
        # Check if any CN keyword is found in the description
        for keyword in self.cn_keywords:
            if keyword.lower() in description_lower:
                print(f"CN keyword '{keyword}' found in description: {description}")
                return True
        
        return False
    
    def is_bad_specialty(self, specialty):
        """Legacy method - now handled by evaluate_provider_by_taxonomy"""
        # This method is kept for backward compatibility
        # But the main evaluation should use evaluate_provider_by_taxonomy
        return False
    
    def is_good_for_cn(self, specialty):
        """Legacy method - now handled by evaluate_provider_by_taxonomy"""
        # This method is kept for backward compatibility
        return self.is_good_for_cn_by_description(specialty)

class DoctorProcessor:
    def __init__(self, doctors_csv_file='test_amir.csv'):
        self.doctors_csv_file = doctors_csv_file
        self.npi_service = NPIRegistryService()
        self.pecos_service = PECOSEnrollmentService()
        self.specialty_validator = TaxonomyBasedSpecialtyValidator()
        self.report_data = []
        self.test_mode = False
        
    def process_doctors(self):
        """Process all doctors from CSV file using taxonomy-based filtering"""
        print("Starting doctor processing with taxonomy-based evaluation...")
        
        encodings = ['utf-8', 'utf-8-sig', 'windows-1252', 'latin1', 'cp1252']
        
        for encoding in encodings:
            try:
                with open(self.doctors_csv_file, 'r', encoding=encoding) as f:
                    reader = csv.DictReader(f)
                    rows = list(reader)
                    
                print(f"Found {len(rows)} rows to process")
                print(f"Used encoding: {encoding}")
                
                if rows:
                    print(f"CSV columns: {list(rows[0].keys())[:10]}...")
                
                processed_rows = []
                rows_to_process = rows[:3] if self.test_mode else rows
                
                for i, row in enumerate(rows_to_process, 1):
                    print(f"\n{'='*50}")
                    print(f"Processing row {i}/{len(rows_to_process)}")
                    print(f"{'='*50}")
                    
                    processed_row = self.process_single_row(row)
                    if processed_row:
                        processed_rows.append(processed_row)
                        
                self.write_processed_data(processed_rows)
                self.generate_report()
                
                print(f"\nProcessing complete! {len(processed_rows)} rows remaining after filtering")
                return
                
            except UnicodeDecodeError:
                print(f"Encoding {encoding} failed, trying next...")
                continue
            except Exception as e:
                print(f"Error with encoding {encoding}: {e}")
                continue
                
        print(f"Could not read doctors file with any encoding")
    
    def process_single_row(self, row):
        """Process a single row with taxonomy-based evaluation"""
        patient_state = row.get('PT State', '').strip()
        
        # Categories for doctors
        good_doctors = []
        good_cn_doctors = []
        bad_specialty_doctors = []
        not_found_doctors = []
        not_enrolled_doctors = []
        other_failed_doctors = []
        
        # Process all doctor columns (DR1 to DR20)
        for dr_num in range(1, 21):
            dr_name = row.get(f'DR{dr_num}', '').strip()
            dr_address = row.get(f'DR{dr_num}_ADDRESS', '').strip()
            dr_date = row.get(f'DR{dr_num}_DATE', '').strip()
            
            if not dr_name:
                continue
                
            print(f"\nProcessing DR{dr_num}: {dr_name}")
            
            # Process this doctor with taxonomy evaluation
            result = self.process_doctor_with_taxonomy(dr_name, dr_address, dr_date, patient_state)
            
            if result['category'] == 'GOOD':
                good_doctors.append(result['formatted_doctor'])
            elif result['category'] == 'CN_ELIGIBLE':
                good_cn_doctors.append(result['formatted_doctor'])
            elif result['category'] == 'BAD_SPECIALTY':
                bad_specialty_doctors.append(result['suggestion'])
            elif result['category'] == 'NOT_FOUND':
                not_found_doctors.append(result['suggestion'])
            elif result['category'] == 'NOT_ENROLLED':
                not_enrolled_doctors.append(result['suggestion'])
            else:
                other_failed_doctors.append(result['suggestion'])
        
        # Update row with categorized doctors
        if good_doctors or good_cn_doctors:
            updated_row = row.copy()
            
            # Clear all doctor fields first
            for dr_num in range(1, 21):
                for field in ['', '_ADDRESS', '_DATE', '_NPI', '_ENROLLMENT', '_SPECIALTY', '_SOURCE', '_PHONE', '_FAX']:
                    updated_row[f'DR{dr_num}{field}'] = ''
            
            # Add good doctors first (up to 20)
            all_good_doctors = good_doctors + good_cn_doctors
            for i, doctor_data in enumerate(all_good_doctors[:20], 1):
                updated_row[f'DR{i}'] = doctor_data['full_string']
                updated_row[f'DR{i}_ADDRESS'] = doctor_data['address']
                updated_row[f'DR{i}_DATE'] = doctor_data['date']
                updated_row[f'DR{i}_NPI'] = doctor_data['npi']
                updated_row[f'DR{i}_ENROLLMENT'] = doctor_data['enrollment']
                updated_row[f'DR{i}_SPECIALTY'] = doctor_data['specialty']
                updated_row[f'DR{i}_SOURCE'] = doctor_data['source']
                updated_row[f'DR{i}_PHONE'] = doctor_data['phone']
                updated_row[f'DR{i}_FAX'] = doctor_data['fax']
            
            # Add categorized suggestions
            if bad_specialty_doctors:
                updated_row['DR_SUGGESTION_BAD_SPECIALTY'] = ' | '.join(bad_specialty_doctors)
            if not_found_doctors:
                updated_row['DR_SUGGESTION_NOT_FOUND'] = ' | '.join(not_found_doctors)
            if not_enrolled_doctors:
                updated_row['DR_SUGGESTION_NOT_ENROLLED'] = ' | '.join(not_enrolled_doctors)
            if other_failed_doctors:
                updated_row['DR_SUGGESTION_OTHER'] = ' | '.join(other_failed_doctors)
            
            # Update counts
            updated_row['DR_COUNT'] = len(all_good_doctors)
            updated_row['DR_SUGGESTIONS_COUNT'] = len(bad_specialty_doctors + not_found_doctors + not_enrolled_doctors + other_failed_doctors)
            
            return updated_row
        else:
            # No doctors left after filtering
            self.add_to_report(row, 0, "All doctors", "", "All doctors removed due to filtering", {})
            return None
    
    def process_doctor_with_taxonomy(self, dr_name, dr_address, dr_date, patient_state):
        """Process individual doctor using taxonomy-based evaluation"""
        
        result = {
            'category': 'OTHER_FAILED',
            'formatted_doctor': None,
            'suggestion': '',
            'debug_info': {}
        }
        
        # Extract state from doctor address
        dr_state = self.npi_service.extract_state_from_address(dr_address)
        if not dr_state:
            dr_state = patient_state
        
        try:
            # Search for provider
            providers = self.npi_service.search_providers(dr_name, dr_state, max_results=1)
            
            if not providers:
                result['category'] = 'NOT_FOUND'
                result['suggestion'] = f"{dr_name} // {dr_address} // {dr_date} // Doctor not found in NPI registry"
                return result
                
            provider = providers[0]
            
            # Validate basic criteria
            validation_result = self.npi_service.validate_provider_basic_criteria(provider)
            if not validation_result['isValid']:
                result['category'] = 'OTHER_FAILED'
                result['suggestion'] = f"{dr_name} // {dr_address} // {dr_date} // Provider validation failed: {', '.join(validation_result['reasons'])}"
                return result
            
            # NEW: Taxonomy-based evaluation
            taxonomy_evaluation = self.specialty_validator.evaluate_provider_by_taxonomy(provider)
            
            print(f"Taxonomy evaluation: {taxonomy_evaluation}")
            
            # Check PECOS enrollment
            npi = provider.get('npi', '')
            enrollment_status = "Not Enrolled"
            
            if npi:
                enrollment_result = self.pecos_service.check_provider_enrollment(npi)
                if enrollment_result.get('isEnrolled'):
                    enrollment_status = "Enrolled"
                elif enrollment_result.get('isEnrolled') is None:
                    enrollment_status = "Unknown"
            
            # Decision logic based on taxonomy evaluation
            if taxonomy_evaluation['category'] == 'GOOD':
                # Good taxonomy - accept if enrolled or enrollment unknown
                if enrollment_status in ["Enrolled", "Unknown"]:
                    result['category'] = 'GOOD'
                    result['formatted_doctor'] = self.format_doctor_data(provider, dr_address, dr_date, enrollment_status, 'TAXONOMY_GOOD')
                else:
                    result['category'] = 'NOT_ENROLLED'
                    result['suggestion'] = f"{dr_name} // {dr_address} // {dr_date} // Good taxonomy but not enrolled in PECOS"
                    
            elif taxonomy_evaluation['category'] == 'BAD':
                if taxonomy_evaluation['is_cn_eligible']:
                    # Bad taxonomy but good for CN
                    result['category'] = 'CN_ELIGIBLE'
                    result['formatted_doctor'] = self.format_doctor_data(provider, dr_address, dr_date, enrollment_status, 'CN_ELIGIBLE')
                else:
                    # Bad taxonomy and not good for CN
                    result['category'] = 'BAD_SPECIALTY'
                    result['suggestion'] = f"{dr_name} // {dr_address} // {dr_date} // Bad specialty: {taxonomy_evaluation['specialty_description']}"
                    
            elif taxonomy_evaluation['category'] == 'CN_ELIGIBLE':
                # Good for CN regardless of enrollment
                result['category'] = 'CN_ELIGIBLE'
                result['formatted_doctor'] = self.format_doctor_data(provider, dr_address, dr_date, enrollment_status, 'CN_ELIGIBLE')
                
            else:
                # Unknown taxonomy
                if enrollment_status == "Enrolled":
                    # Unknown taxonomy but enrolled - accept as good
                    result['category'] = 'GOOD'
                    result['formatted_doctor'] = self.format_doctor_data(provider, dr_address, dr_date, enrollment_status, 'ENROLLED_UNKNOWN_TAXONOMY')
                else:
                    # Unknown taxonomy and not enrolled - reject
                    result['category'] = 'OTHER_FAILED'
                    result['suggestion'] = f"{dr_name} // {dr_address} // {dr_date} // Unknown taxonomy and not enrolled"
            
            print(f"Final decision: {result['category']}")
            return result
            
        except Exception as e:
            print(f"Error processing doctor {dr_name}: {e}")
            result['category'] = 'OTHER_FAILED'
            result['suggestion'] = f"{dr_name} // {dr_address} // {dr_date} // Error processing: {str(e)}"
            return result
    
    def format_doctor_data(self, provider, dr_address, dr_date, enrollment_status, source):
        """Format doctor data for output"""
        phone = provider.get('practicePhone', '')
        fax = provider.get('practiceFax', '')
        return {
            'full_string': f"{provider.get('fullName', '')} // {dr_address} // {provider.get('npi', '')} // {enrollment_status} // {provider.get('primaryTaxonomyName', '')} // {dr_date}",
            'address': dr_address,
            'date': dr_date,
            'npi': provider.get('npi', ''),
            'enrollment': enrollment_status,
            'specialty': provider.get('primaryTaxonomyName', ''),
            'source': source,
            'phone': phone,
            'fax': fax
        }
    
    def add_to_report(self, row, dr_num, dr_name, dr_address, reason, debug_info=None):
        """Add removed doctor to report"""
        report_entry = {
            'patient_info': f"Name: {row.get('PT First Name', '')} {row.get('PT Last Name', '')}, State: {row.get('PT State', '')}",
            'doctor_number': f"DR{dr_num}" if dr_num > 0 else "All",
            'doctor_name': dr_name,
            'doctor_address': dr_address,
            'removal_reason': reason,
            'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'debug_info': debug_info or {}
        }
        self.report_data.append(report_entry)
        print(f"REMOVED: DR{dr_num} - {dr_name} - Reason: {reason}")
    
    def write_processed_data(self, processed_rows):
        """Write processed data back to CSV file"""
        if not processed_rows:
            print("No data to write - all rows were filtered out")
            return
            
        output_filename = 'doctors_filtered_taxonomy.csv'
        try:
            fieldnames = processed_rows[0].keys()
            
            with open(output_filename, 'w', newline='', encoding='utf-8') as f:
                writer = csv.DictWriter(f, fieldnames=fieldnames)
                writer.writeheader()
                writer.writerows(processed_rows)
                
            print(f"Filtered data written to {output_filename}")
            
        except Exception as e:
            print(f"Error writing processed data: {e}")
    
    def generate_report(self):
        """Generate detailed removal report"""
        report_filename = f'taxonomy_doctor_removal_report_{datetime.now().strftime("%Y%m%d_%H%M%S")}.txt'
        
        try:
            with open(report_filename, 'w', encoding='utf-8') as f:
                f.write("TAXONOMY-BASED DOCTOR REMOVAL REPORT\n")
                f.write("=" * 60 + "\n\n")
                f.write(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
                f.write(f"Total Removals: {len(self.report_data)}\n\n")
                
                # Group by removal reason
                reason_groups = {}
                for entry in self.report_data:
                    reason = entry['removal_reason']
                    if reason not in reason_groups:
                        reason_groups[reason] = []
                    reason_groups[reason].append(entry)
                
                f.write("SUMMARY BY REMOVAL REASON:\n")
                f.write("-" * 30 + "\n")
                for reason, entries in reason_groups.items():
                    f.write(f"{reason}: {len(entries)} doctors\n")
                
                f.write("\nDETAILED REMOVAL LOG:\n")
                f.write("-" * 40 + "\n\n")
                
                for i, entry in enumerate(self.report_data, 1):
                    f.write(f"{i}. {entry['timestamp']}\n")
                    f.write(f"   Patient: {entry['patient_info']}\n")
                    f.write(f"   Doctor: {entry['doctor_number']} - {entry['doctor_name']}\n")
                    f.write(f"   Address: {entry['doctor_address']}\n")
                    f.write(f"   Reason: {entry['removal_reason']}\n")
                    f.write("\n" + "="*80 + "\n\n")
                
            print(f"Detailed removal report generated: {report_filename}")
            
        except Exception as e:
            print(f"Error generating report: {e}")

def main():
    """Main function to run the taxonomy-based doctor processing"""
    print("Medicare Doctor Validation System - Taxonomy Based")
    print("=" * 50)
    
    # Check if required files exist
    required_files = ['test_amir.csv', 'taxonomy.csv']
    missing_files = []
    
    for file in required_files:
        if not os.path.exists(file):
            missing_files.append(file)
    
    if missing_files:
        print(f"Missing required files: {', '.join(missing_files)}")
        print("Please ensure the following files are in the current directory:")
        print("- test_amir.csv: CSV file with doctor data")
        print("- taxonomy.csv: CSV file with taxonomy codes and categories")
        print("- bad specs.csv: CSV file with CN specialties (optional)")
        return
    
    # Test mode option
    test_mode = input("\nRun in test mode? (process only first 3 rows) [y/N]: ").lower().startswith('y')
    
    # Initialize and run processor
    processor = DoctorProcessor()
    
    if test_mode:
        processor.test_mode = True
        print("Running in TEST MODE - processing only first 3 rows")
    
    processor.process_doctors()
    
    print("\nTaxonomy-based doctor processing completed!")
    print("Files generated:")
    print("- doctors_filtered_taxonomy.csv: Filtered doctor data")
    print("- taxonomy_doctor_removal_report_[timestamp].txt: Detailed removal report")

if __name__ == "__main__":
    main()