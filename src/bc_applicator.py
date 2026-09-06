# -*- coding: mbcs -*-
from abaqus import *
from abaqusConstants import *
import regionToolset
import job

# ==============================================================================
# 1. USER CONFIGURATION (EDIT THIS SECTION ONLY)
# ==============================================================================
config = {
    'MODEL_NAME':       '10mm_100res_30rd_40Kdecimated_fullopti',
    'LOADING_STEP':     'loading',       
    'JOB_NAME':         'XX_Tension_0_1_tit_30rd',
    'HO_PREFIX':        'HO_RP_'         
}

# Default displacement from instructions (0.1 mm for U1)
DEFAULT_U1 = '0.05'

# ==============================================================================
# 2. HELPER FUNCTIONS
# ==============================================================================

def get_model(model_name):
    if model_name not in mdb.models:
        print("[Error] Model '%s' not found." % model_name)
        return None
    return mdb.models[model_name]

def safe_create_symm_bc(model, bc_name, set_name, symm_type):
    """Creates Symmetry BCs (XSYMM, YSYMM, ZSYMM) in the Initial Step."""
    root_assembly = model.rootAssembly
    if set_name not in root_assembly.sets:
        print("  [Skip] Set '%s' missing for %s." % (set_name, bc_name))
        return
    region = root_assembly.sets[set_name]
    if bc_name in model.boundaryConditions:
        del model.boundaryConditions[bc_name]
    
    if symm_type == 'XSYMM':
        model.XsymmBC(name=bc_name, createStepName='Initial', region=region)
    elif symm_type == 'YSYMM':
        model.YsymmBC(name=bc_name, createStepName='Initial', region=region)
    elif symm_type == 'ZSYMM':
        model.ZsymmBC(name=bc_name, createStepName='Initial', region=region)
    print("  [OK] Created Symm BC: %s" % bc_name)

def safe_create_disp_bc(model, bc_name, step_name, set_name, u1=UNSET, u2=UNSET, u3=UNSET):
    root_assembly = model.rootAssembly
    if set_name not in root_assembly.sets:
        return
    region = root_assembly.sets[set_name]
    if bc_name in model.boundaryConditions:
        del model.boundaryConditions[bc_name]
    model.DisplacementBC(name=bc_name, createStepName=step_name, region=region, 
                         u1=u1, u2=u2, u3=u3, amplitude=UNSET, 
                         distributionType=UNIFORM, localCsys=None)
    print("  [OK] Created Disp BC: %s" % bc_name)

def safe_create_equation(model, eq_name, set_slave, set_master, dof):
    root_assembly = model.rootAssembly
    if set_slave not in root_assembly.sets or set_master not in root_assembly.sets:
        return
    if eq_name in model.constraints:
        del model.constraints[eq_name]
    model.Equation(name=eq_name, terms=((1.0, set_slave, dof), (-1.0, set_master, dof)))
    print("  [OK] Created Equation: %s" % eq_name)

# ==============================================================================
# 3. MAIN EXECUTION FLOW
# ==============================================================================

def run_xx_tension_pipeline():
    print("\n" + "="*60)
    print("STARTING UPDATED XX TENSION PIPELINE (IRANIAN PAPER BCs)")
    print("="*60)

    m = get_model(config['MODEL_NAME'])
    if m is None: return
    a = m.rootAssembly

    # Step A: User Input
    u1_input = getInput('Enter Displacement for RP_X (U1) in mm:', DEFAULT_U1)
    if u1_input is None: return 
    val_u1 = float(u1_input)

    # --------------------------------------------------------------------------
    # MODULE 1: APPLY BOUNDARY CONDITIONS (Symmetry & Loads)
    # --------------------------------------------------------------------------
    print("\n--- Module 1: Applying Symmetry & Loads ---")
    
    # 1. Symmetry BCs on Min/Max faces (Initial Step)
    safe_create_symm_bc(m, 'BC_XMIN_XSYMM', 'XMIN', 'XSYMM')
    safe_create_symm_bc(m, 'BC_YMIN_YSYMM', 'YMIN', 'YSYMM')
    safe_create_symm_bc(m, 'BC_ZMIN_ZSYMM', 'ZMIN', 'ZSYMM')
    safe_create_symm_bc(m, 'BC_YMAX_YSYMM', 'YMAX', 'YSYMM')
    safe_create_symm_bc(m, 'BC_ZMAX_ZSYMM', 'ZMAX', 'ZSYMM')

    # 2. Loading Step Displacement on Reference Points
    safe_create_disp_bc(m, 'LOAD_RP_X', config['LOADING_STEP'], 'RP_X', u1=val_u1)
    safe_create_disp_bc(m, 'LOAD_RP_Y', config['LOADING_STEP'], 'RP_Y', u2=0.0)
    safe_create_disp_bc(m, 'LOAD_RP_Z', config['LOADING_STEP'], 'RP_Z', u3=0.0)

    # --------------------------------------------------------------------------
    # MODULE 2: KINEMATIC COUPLING (Equations)
    # --------------------------------------------------------------------------
    print("\n--- Module 2: Applying Kinematic Equations ---")

    # XMAX face follows RP_X in U1, YMAX follows RP_Y in U2, ZMAX follows RP_Z in U3
    safe_create_equation(m, 'EQ_XMAX_RPX', 'XMAX', 'RP_X', 1)
    safe_create_equation(m, 'EQ_YMAX_RPY', 'YMAX', 'RP_Y', 2)
    safe_create_equation(m, 'EQ_ZMAX_RPZ', 'ZMAX', 'RP_Z', 3)

    # --------------------------------------------------------------------------
    # MODULE 3: HISTORY OUTPUT & JOB SETUP
    # --------------------------------------------------------------------------
    print("\n--- Module 3: History Output & Job Setup ---")

    # 1. History Output RP_X: RF1, U1
    if 'RP_X' in a.sets:
        m.HistoryOutputRequest(name='HO_RP_X', createStepName=config['LOADING_STEP'],
                               variables=('RF1', 'U1'), region=a.sets['RP_X'])
    
    # 2. History Output RP_Y: RF2
    if 'RP_Y' in a.sets:
        m.HistoryOutputRequest(name='HO_RP_Y', createStepName=config['LOADING_STEP'],
                               variables=('RF2', ), region=a.sets['RP_Y'])

    # 3. History Output RP_Z: RF3
    if 'RP_Z' in a.sets:
        m.HistoryOutputRequest(name='HO_RP_Z', createStepName=config['LOADING_STEP'],
                               variables=('RF3', ), region=a.sets['RP_Z'])

    # 4. Create Job
    job_name = config['JOB_NAME']
    if job_name in mdb.jobs: del mdb.jobs[job_name]
    mdb.Job(name=job_name, model=config['MODEL_NAME'], description='Validation Tension Pipeline')
    
    print("\nPIPELINE COMPLETE. SCRIPT READY.")

if __name__ == "__main__":
    run_xx_tension_pipeline()