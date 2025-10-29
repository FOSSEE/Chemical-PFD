import os
import csv
import sys

def resource_path(relative_path):
    """Get absolute path to resource, works for dev and for PyInstaller."""
    if hasattr(sys, '_MEIPASS'):
        return os.path.join(sys._MEIPASS, relative_path)
    return os.path.join(os.path.abspath("."), relative_path)

def get_component_data(component_type):
    csv_path = resource_path('Component_Details.csv')

    if not os.path.exists(csv_path):
        print(f"[Error] CSV not found at: {csv_path}")
        return None

    try:
        with open(csv_path, mode='r', encoding='utf-8-sig') as file:
            reader = csv.DictReader(file)
            for row in reader:
                # Normalize all keys and values
                normalized_row = {
                    k.strip().lower(): v.strip() for k, v in row.items()
                }

                object_name = normalized_row.get('object', '').lower()
                if object_name == component_type.strip().lower():
                    print(f"[Matched] Found: {component_type}")
                    return {
                        'legend': normalized_row.get('legend', ''),
                        'suffix': normalized_row.get('suffix', ''),
                        'name': normalized_row.get('name', '')  # Optional
                    }

        print(f"[Warning] Component '{component_type}' not found in CSV.")
        return None

    except Exception as e:
        print(f"[Exception] Error while reading CSV: {e}")
        return None
