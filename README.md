# Abaqus-Python Automated Displacement boundary conditions supported Homogenization Pipeline



## Getting started

An automated Python toolset for Abaqus to compute the effective (homogenized) mechanical properties of Representative Volume Elements (RVEs) of porous or architectured lattices.



## Module 1: Pre-Processor (`pre_processor.py`)

The Pre-Processor automates the foundational setup of your Representative Volume Element (RVE) inside Abaqus/CAE. It eliminates manual clicking by configuring material behaviors, assembly instances, analysis steps and set creation.

### What it does:
* **Material & Section Setup:** Automatically checks for and creates an isotropic elastic material profile (default: PLA) and assigns a homogeneous solid section to your geometry.
* **Assembly Instance:** Brings your base part into the root assembly context automatically.
* **Bounding Box & Auto-Face Sets:** Scans the outer spatial limits of your geometry to accurately locate and isolate the six boundary faces (`XMIN`, `XMAX`, `YMIN`, `YMAX`, `ZMIN`, `ZMAX`).
* **Analysis Step Management:** Configures a dedicated static general loading step required for the subsequent homogenization constraints.
* **Reference Points (RPs):** Calculates and spawns three independent reference points (`RP_X`, `RP_Y`, `RP_Z`) outside the RVE boundaries enerates named geometry sets for them. These points serve as the master control handles for applying macro-strains and extracting homogenized reaction data.

---

### Prerequisites

Before executing this script, ensure your Abaqus session matches this expectation:
1. **Existing Model & Part:** You must already have an active Abaqus Model (`.cae` database) containing your imported RVE geometry as a single **Part**.

---

### How to Customize and Run

#### 1. Configure the Script Variables
Open `src/pre_processor.py` and modify the variables in **Section 0 (GLOBAL USER CONFIGURATION)** to match your specific model requirements:

| Variable | Description | Example Value |
| :--- | :--- | :--- |
| `MODEL_NAME` | Exact name of your current Abaqus model container. | `'10mm_100res_30rd_40Kdecimated_fullopti'` |
| `PART_NAME` | Exact name of the base geometry part inside your model. | `'uni'` |
| `MATERIAL_NAME` | The label for the material you want to generate. | `'PLA'` |
| `YOUNGS_MODULUS`| Elastic modulus value (in **MPa**). | `3500.0` |
| `POISSON_RATIO` | Poisson's ratio for lateral strain calculations. | `0.35` |
| `TOLERANCE` | Geometric allowance for capturing outer faces (increase if your mesh boundary is imperfect). | `0.01` |

#### 2. Run the Script
You can execute this script inside Abaqus through two primary methods:

* **Via Abaqus/CAE Interface:** Go to the top menu and select **File... Run Script...**, navigate to your directory, and choose `pre_processor.py`.

## Module 2: Boundary Conditions Applicator (`bc_applicator.py`)

The Boundary Conditions Applicator maps kinematic equations, symmetric constraints, and displacements across the faces of the RVE.

### What it does:
* **Symmetry Constraints:** Automatically applies `XSYMM`, `YSYMM`, and `ZSYMM` boundary conditions to the minimum and maximum faces during the initialization step.
* **Kinematic Coupling:** Hooks up the maximum faces (`XMAX`, `YMAX`, `ZMAX`) directly to their respective Reference point.
* **Job Assembly:** Requests targeted History Outputs (`RF`, `U`) directly from the Reference Points and sets up the ready-to-run Abaqus simulation analysis Job.

### Configuration & Execution

#### 1. Configure the Script Variables
Open `src/bc_applicator.py` and tweak the execution configurations inside **Section 1**

## Module 3: Post-Processor (`post_processor.py`)

The Post-Processor automates data extraction and analytical homogenization once the simulation is complete. It queries the active Output Database (`.odb`) to calculate the macro-scale effective mechanical properties of the RVE.

### What it does:
* **Active ODB Detection:** Automatically detects and connects to the active `.odb` file currently open in your Abaqus viewport.
* **History Data:** Scans the output history regions to extract the final-frame reaction forces (`RF1`, `RF2`) and macro-displacements (`U1`) directly from the reference points.
* **Stiffness & Engineering Constants Conversion:** Combines the extracted boundary variables with user-defined geometry settings to map the core components of the stiffness tensor ($C_{11}$, $C_{12}$). It then calculates the effective macro-properties: **Young's Modulus ($E^*$)**, **Poisson's Ratio ($\nu^*$)**, and **Bulk Modulus ($K^*$)**.

---

### How to Run

1. Run and complete your homogenization job in Abaqus.
2. Open the resulting `.odb` database file in your active Abaqus viewport (`File...  Open... ODB...`).
3. Run this script via the Abaqus GUI menu: **File... Run Script...** and select `post_processor.py`.
4. A dialogue box will prompt you to enter your **RVE side length** (in mm, defaults to `10.0`).
5. Check your Abaqus Command/Log window at the bottom of the screen to view your printed homogenization report.

## Verification Module: Result Verification (`result_verification.py`)

This validation tool provides a dual-check mechanism for your homogenization output. Rather than utilizing reaction forces, it loops through every element integration point inside the RVE to compute a localized **Volume Average** of the inner stress fields. 

Users can compare these calculated stiffness constants against the results from the Reaction Force Post-Processor to verify mathematical convergence.

### What it does:
* **Field Output data:** Queries the internal element field data fields for individual Integration Points.
* **Volume Averaging Integration:** Multiplies the localized micro-stresses by their local elemental integration volume (`IVOL`), aggregates them over the whole domain, and normalizes the sum over the entire bounding box volume ($V_{box}$).
* **Stiffness Verification:** Extracts the matrix constants ($C_{11}$, $C_{12}$).

---

### Critical Prerequisite (Abaqus Setup)

Because the base Pre-Processor module is optimized for reaction force data collection, **you must manually adjust your Abaqus Step parameters** before executing your simulation job for this verification script to function:

1. In Abaqus/CAE, make sure to make an element set containing all the elements and name them `ALL_ELEMENTS` and then 
navigate to the **Step Module**.
2. Select **Output...Field Output Requests...Manager**.
3. Edit the active request for your loading step and ensure the following output toggles are **explicitly checked**:
   * **`S`** (Stress components)
   * **`E`** (Strain components)
   * **`IVOL`** (Integration point volume - located under the *Volume/Thickness/Coordinates* sub-menu)
4. Ensure the element set named `ALL_ELEMENTS` is selected accordingly for the Field Output Request.

---

### How to Run

1. Open the analyzed `.odb` file (containing `S`, `E`, and `IVOL` variables) in your active viewport (it needs to be in the active viewport).
2. Open `src/result_verification.py` to update your physical geometric assumptions if your bounding box isn't a $10 \times 10 \times 10\text{ mm}$ cube:
   ```python
   L_initial = 10.0              # Directional loading length
   U_applied = 0.1               # Imposed load displacement
   V_box = 1000.0                # Total bounding-box volume (L^3)






