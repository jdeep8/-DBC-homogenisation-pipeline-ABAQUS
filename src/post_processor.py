# -*- coding: mbcs -*-
from abaqus import *
from abaqusConstants import *
from odbAccess import *
import os

# ==============================================================================
# 1. AUTOMATIC ODB DETECTION
# ==============================================================================
def get_active_odb():
    try:
        vp_name = session.currentViewportName
        odb_display_name = session.viewports[vp_name].odbDisplay.name
        odb = session.odbs[odb_display_name]
        return odb, os.path.dirname(odb.path), os.path.basename(odb.path)
    except:
        print("ERROR: ODB must be open in the active viewport.")
        return None, None, None

# ==============================================================================
# 2. HISTORY DATA EXTRACTION
# ==============================================================================
def extract_history_data(odb):
    try:
        if not odb.steps.values():
            return None, None, None
            
        last_step = odb.steps.values()[-1]
        rf1, u1, rf2 = None, None, None

        print("Scanning History Regions in Step: %s" % last_step.name)
        
        for region_name in last_step.historyRegions.keys():
            region = last_step.historyRegions[region_name]
            outputs = region.historyOutputs
            
            # Extract RF1 and U1
            if 'RF1' in outputs and 'U1' in outputs:
                rf1 = outputs['RF1'].data[-1][1]
                u1 = outputs['U1'].data[-1][1]
                print("  Found RF1 and U1 in region: %s" % region_name)
                
            # Extract RF2
            if 'RF2' in outputs:
                rf2 = outputs['RF2'].data[-1][1]
                print("  Found RF2 in region: %s" % region_name)

        return rf1, u1, rf2

    except Exception as e:
        print("Extraction Error: " + str(e))
        return None, None, None

# ==============================================================================
# 3. CALCULATION PIPELINE
# ==============================================================================
def run_post_processor():
    odb, work_dir, odb_name = get_active_odb()
    if not odb: return

    # 1. Get Geometry Info
    L_in = getInput("Enter RVE Length (mm):", "10.0")
    if not L_in: return
    try:
        L = float(L_in)
    except ValueError:
        print("Invalid input for length.")
        return

    # 2. Extract from History
    rf1, u1, rf2 = extract_history_data(odb)

    if rf1 is None or u1 is None or rf2 is None:
        print("-" * 50)
        print("CRITICAL ERROR: Could not find RF1, U1, or RF2 in History Output.")
        print("Ensure you requested History Output for the Reference Points.")
        print("-" * 50)
        return

    # 3. Math Logic
    epsilon_11 = u1 / L
    area = L * L
    
    if abs(epsilon_11) < 1e-18:
        print("Error: Displacement is zero. Check your loading.")
        return

    c11 = (rf1 / area) / epsilon_11
    c12 = (rf2 / area) / epsilon_11

    # 4. Effective Properties
    # E* = (C11^2 + C11*C12 - 2*C12^2) / (C11 + C12)
    E_eff = ((c11**2) + (c11 * c12) - (2 * (c12**2))) / (c11 + c12)
    # v* = C12 / (C11 + C12)
    v_eff = c12 / (c11 + c12)
    # K* = (C11 + 2*C12) / 3
    K_eff = (c11 + (2.0 * c12)) / 3.0

    # 5. Output Results
    header = "\n" + "="*50 + "\n HOMOGENIZED EFFECTIVE PROPERTIES (HISTORY DATA) \n" + "="*50
    print(header)
    print("Source ODB: %s" % odb_name)
    print("-" * 50)
    print("C11 (Normal):           {:.4e}".format(c11))
    print("C12 (Transverse):       {:.4e}".format(c12))
    print("-" * 50)
    print("YOUNG'S MODULUS (E*):   {:.4e}".format(E_eff))
    print("POISSON'S RATIO (v*):   {:.4f}".format(v_eff))
    print("BULK MODULUS (K*):      {:.4e}".format(K_eff))
    print("=" * 50)

if __name__ == "__main__":
    run_post_processor()