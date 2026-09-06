# -*- coding: mbcs -*-
# ------------------------------------------------------------------------------
# FULL UNIFIED PRE-PROCESSOR
# Material -> Instance -> Section -> Face Sets -> Step -> Reference Points
# ------------------------------------------------------------------------------

from abaqus import *
from abaqusConstants import *
from regionToolset import Region

# ==============================================================================
# 0. GLOBAL USER CONFIGURATION
# ==============================================================================
MODEL_NAME    = '10mm_100res_30rd_40Kdecimated_fullopti'
PART_NAME     = 'uni'
INSTANCE_NAME = PART_NAME + '_INST'
STEP_NAME     = 'loading'

# Material Properties (Titanium)
MATERIAL_NAME  = 'PLA'
YOUNGS_MODULUS = 3500.0    # MPa
POISSON_RATIO  = 0.35
SECTION_NAME   = 'PLA_SOLID_SECTION'

# RP Set Names
RP_X_NAME = 'RP_X'
RP_Y_NAME = 'RP_Y'
RP_Z_NAME = 'RP_Z'

# Face Set Tolerance
TOLERANCE = 0.01

# ==============================================================================
# 1. MATERIAL & SECTION ASSIGNMENT
# ==============================================================================
model = mdb.models[MODEL_NAME]

# Material
if MATERIAL_NAME not in model.materials.keys():
    print('Creating material: %s' % MATERIAL_NAME)
    mat = model.Material(name=MATERIAL_NAME)
    mat.Elastic(table=((YOUNGS_MODULUS, POISSON_RATIO), ), type=ISOTROPIC)

# Section
if SECTION_NAME not in model.sections.keys():
    print('Creating section: %s' % SECTION_NAME)
    model.HomogeneousSolidSection(name=SECTION_NAME, material=MATERIAL_NAME, thickness=None)

# Assignment to Part
part = model.parts[PART_NAME]
region = Region(cells=part.cells) if part.cells else Region(faces=part.faces)
part.SectionAssignment(region=region, sectionName=SECTION_NAME)

# ==============================================================================
# 2. INSTANCE CREATION
# ==============================================================================
assembly = model.rootAssembly
if INSTANCE_NAME in assembly.instances.keys():
    print('Instance "%s" already exists.' % INSTANCE_NAME)
else:
    print('Creating instance: %s' % INSTANCE_NAME)
    assembly.Instance(name=INSTANCE_NAME, part=part, dependent=ON)

# ==============================================================================
# 3. AUTO-FACE SET CREATION
# ==============================================================================
print("\nDetecting Bounding Box and Creating Face Sets...")
inst = assembly.instances[INSTANCE_NAME]

try:
    bbox = inst.getBoundingBox()
    xmin, ymin, zmin = bbox['low']
    xmax, ymax, zmax = bbox['high']
except:
    coords = [v.pointOn[0] for v in inst.vertices] if inst.vertices else [n.coordinates for n in inst.nodes]
    xmin, xmax = min(c[0] for c in coords), max(c[0] for c in coords)
    ymin, ymax = min(c[1] for c in coords), max(c[1] for c in coords)
    zmin, zmax = min(c[2] for c in coords), max(c[2] for c in coords)

def create_side_set(set_name, axis_char, limit_value):
    idx = {'X': 0, 'Y': 1, 'Z': 2}[axis_char]
    args = {'xMin': xmin-0.1, 'xMax': xmax+0.1, 'yMin': ymin-0.1, 'yMax': ymax+0.1, 'zMin': zmin-0.1, 'zMax': zmax+0.1}
    args[axis_char.lower() + 'Min'] = limit_value - TOLERANCE
    args[axis_char.lower() + 'Max'] = limit_value + TOLERANCE

    found_faces = inst.faces.getByBoundingBox(**args)
    if not found_faces: # Deep scan fallback
        face_indices = [i for i, f in enumerate(inst.faces) if abs(f.pointOn[0][idx] - limit_value) < TOLERANCE]
        if face_indices:
            found_faces = inst.faces[face_indices[0]:face_indices[0]+1]
            for val in face_indices[1:]: found_faces += inst.faces[val:val+1]

    if found_faces:
        if set_name in assembly.sets.keys(): del assembly.sets[set_name]
        assembly.Set(faces=found_faces, name=set_name)

create_side_set('XMIN', 'X', xmin); create_side_set('XMAX', 'X', xmax)
create_side_set('YMIN', 'Y', ymin); create_side_set('YMAX', 'Y', ymax)
create_side_set('ZMIN', 'Z', zmin); create_side_set('ZMAX', 'Z', zmax)

# ==============================================================================
# 4. STEP CREATION
# ==============================================================================
if STEP_NAME in model.steps.keys():
    print('Step "%s" already exists.' % STEP_NAME)
else:
    print('Creating step: %s' % STEP_NAME)
    model.StaticStep(name=STEP_NAME, previous='Initial', nlgeom=OFF,
                     initialInc=0.1, timePeriod=1.0)

# ==============================================================================
# 5. REFERENCE POINT CREATION (Dynamic Positioning)
# ==============================================================================
print("Creating Reference Points...")
# Offset RPs by 5 units from the bounding box to ensure no overlap
offset = 5.0
rp_coords = [
    (xmax + offset, 0.0, 0.0), # RP_X
    (0.0, ymax + offset, 0.0), # RP_Y
    (0.0, 0.0, zmax + offset)  # RP_Z
]

rp_features = [assembly.ReferencePoint(point=pt) for pt in rp_coords]
rp_objects = assembly.referencePoints

# Create Named Sets for Equation Mapping
names = [RP_X_NAME, RP_Y_NAME, RP_Z_NAME]
for i, feat in enumerate(rp_features):
    if names[i] in assembly.sets.keys(): del assembly.sets[names[i]]
    assembly.Set(name=names[i], referencePoints=(rp_objects[feat.id],))

print('\n' + '-'*45)
print(' ALL-IN-ONE PIPELINE COMPLETE')
print(' Bounding Box: X(%.1f), Y(%.1f), Z(%.1f)' % (xmax, ymax, zmax))
print('-'*45)