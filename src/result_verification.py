from abaqus import *
from abaqusConstants import *
import visualization

# --- CONFIGURATION ---
try:
    # Gets the ODB from the active viewport
    vpName = session.currentViewportName
    odbName = session.viewports[vpName].odbDisplay.name
    odb = session.odbs[odbName]
except:
    print("Error: ODB must be open in the active viewport.")

el_set_name = 'ALL_ELEMENTS'  
step_name = 'loading'         

# PHYSICAL PARAMETERS 
L_initial = 10.0              # Initial length in the direction of loading (mm)
U_applied = 0.1               # Applied displacement (mm)
V_box = 10.0 * 10.0 * 10.0    # Total Volume of the Unit Cell (Bounding Box)

# Access the last frame
last_frame = odb.steps[step_name].frames[-1]
target_set = odb.rootAssembly.elementSets[el_set_name]

# Get Field Outputs
stress_field = last_frame.fieldOutputs['S'].getSubset(region=target_set, position=INTEGRATION_POINT)
ivol_field = last_frame.fieldOutputs['IVOL'].getSubset(region=target_set, position=INTEGRATION_POINT)

# Initialize sums for Volume Averaging
sum_s11_ivol = 0.0
sum_s22_ivol = 0.0
total_solid_vol = 0.0

# Loop through integration points
for i in range(len(stress_field.values)):
    # Handle different data types if necessary (Double vs Float)
    if hasattr(stress_field.values[i], 'dataDouble') and stress_field.values[i].dataDouble is not None:
        s_val = stress_field.values[i].dataDouble
        ivol = ivol_field.values[i].dataDouble
    else:
        s_val = stress_field.values[i].data
        ivol = ivol_field.values[i].data
    
    # S[0] is S11, S[1] is S22
    sum_s11_ivol += (s_val[0] * ivol) 
    sum_s22_ivol += (s_val[1] * ivol) 
    total_solid_vol += ivol

# --- HOMOGENIZATION CALCULATIONS ---

# 1. Macroscopic Applied Strain
epsilon_macro = U_applied / L_initial

# 2. Volume Averaged (Macroscopic) Stresses
# Note: We divide by V_box (Total UC Volume), not just total_solid_vol
sig_11_macro = sum_s11_ivol / V_box
sig_22_macro = sum_s22_ivol / V_box

# 3. Extract Stiffness Components (Assuming strain applied in direction 1 or 2)
# If strain was applied in direction 1: C11 = sig11/eps11, C12 = sig22/eps11
# If strain was applied in direction 2: C22 = sig22/eps22, C21 = sig11/eps22
C11_comp = abs(sig_11_macro / epsilon_macro)
C12_comp = abs(sig_22_macro / epsilon_macro)

print("--- UNIT CELL HOMOGENIZATION: STIFFNESS COMPONENTS ---")
print("Total Solid Volume:  %.4f mm^3" % total_solid_vol)
print("Relative Density:    %.2f %%" % ((total_solid_vol/V_box)*100))
print("-------------------------------------------------------")
print("Macro Strain applied: %.6f" % epsilon_macro)
print("Avg Macro Sigma_11:   %.4f MPa" % sig_11_macro)
print("Avg Macro Sigma_22:   %.4f MPa" % sig_22_macro)
print("-------------------------------------------------------")
print("C11 (or C22):         %.4f MPa" % C11_comp)
print("C12 (or C21):         %.4f MPa" % C12_comp)
print("-------------------------------------------------------")