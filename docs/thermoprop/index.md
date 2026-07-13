# ThermoProp

ThermoProp is a Python package that provides thermophysical fluid and material properties and performs chemical equilibrium. ThermoProp's goal is to allow users to easily access properties for real fluids, ideal gases, rocket propellants, combustion gases, and engineering materials all in one place with a simple, user-friendly API.

Oftentimes, when running custom computer simulations, engineers need access to a large database of fluid and material parameters, especially for lumped-parameter tools like FullFlow or ROCETS. While industrial tools like GFSSP, EcosimPro, or GT Suite provide these properties as part of their installations, the tools themselves are either difficult to access, hard to setup, or simply too expensive for amateur engineers, hobbyists, or students. Therefore, it's essential that open-source packages be available, and what's more open-source than Python. 

Several packages and computer programs have been widely by engineers to solve these issues:

- [CoolProp](https://coolprop.org/contents.html#): REFPROP's free (and cooler) twin. It's a widely-used Python package that allows for users to easily access real pure-fluid and mixture properties across many different phases. 
- [PYroMat](http://pyromat.org/): an ideal-gas property pacckage that's targetted towards scientific computation.
- [RocketProps](https://rocketprops.readthedocs.io/en/latest/#): made by the same amazing creator who made RocketCEA, RockeProps provides thermophysical properties for liquid rocket propellants, which can be difficult to find properties for, especially for fluids like RP-1.
- [NASA CEA](https://cearun.grc.nasa.gov/): Chemical Equilibrium with Applications. This is NASA's ultimate chemical equilibrium solver, and it's most commonly used for rocket nozzle performance calculations. CEA (and its MATLAB equivalent CEAM) has a dedicated species database (based on NASA [ThermoBuild](https://cearun.grc.nasa.gov/ThermoBuild/)) which stores ideal gas and condensed phase properties for complex equilibrium calculations.

These packages are great, but they all share different APIs:

```python
CP.PropsSI(...) # CoolProp
pm.get(...) # PYroMat
get_prop(...) # RocketProps
```

Additionally, CEA is usually used as a web application, *CEARUN*, and any development versions are limited to Windows or require fortran compilers.

With ThermoProp, you get a single, intuitive API for real fluids, ideal gases, propellants, combustion gases, equilibrium products, and materials: 

```python
from thermoprop import Fluid

water = Fluid(
    "water",
    pressure=101325,
    temperature=300,
)

print(water.density)
print(water.enthalpy)
print(water.entropy)
```

## Installation

ThermoProp requires at least version 3.11 of Python. Therefore, the easiest way to install ThermoProp is:

```bash
pip3 install thermoprop
```

(ThermoProp is on PyPi: [pypi.org/project/thermoprop/](https://pypi.org/project/thermoprop/))

## GitHub Repository

The source code is stored here: [github.com/saakethramoju/ThermoProp](https://github.com/saakethramoju/ThermoProp).

The repo's README contains a thorough startup guide, and the examples folder provides several example scripts that describe the utilities of ThermoProp in detail.

## Main Features

ThermoProp offers several wrapper classes for convenience:

```python3
from thermoprop import Fluid # CoolProp wrapper
from thermoprop import IdealGas # PYroMat wrapper
from thermoprop import Propellant # CEA condensed species/RocketProps wrapper
from thermoprop import CombustionGas # CEA gas species wrapper
from thermoprop import Reactants # Reactant property initializer for Equilibrium
from thermoprop import Equilibrium # CEA-based TP, HP, and SP eq
from thermoprop import Material # Material properties from matprotlib

from thermoprop import CEA # Raw CEA species data
from thermoprop import SpeciesDatabase # Alias interface for fluid species
from thermoprop import MaterialDatabase # Alias interface for material species
```

It also has a bunch of convenient functions:

```python
from thermoprop import list_species
from thermoprop import supported_species
from thermoprop import species_aliases
from thermoprop import add_species_alias

from thermoprop import list_materials
from thermoprop import supported_materials
from thermoprop import material_aliases
from thermoprop import add_material_alias
```

For the most part, ThermoProp does not provide access to any data that isn't already on the internet or existing Python packages. ThermoProp exists for user convenience:

* Fluid, material, and combustion properties in a single place with a simple API
* Works on all major operating systems
* Repackages legacy softwares like CEA and makes them more general and easier to use

Therefore, ThermoProp aims to be the one-stop shop for fluid and material data users may need.

### What wrapper do I use?

| Need                                  | Use                |
| ------------------------------------- | ------------------ |
| Real-fluid thermodynamics             | `Fluid`            |
| CoolProp fluid mixtures               | `Fluid`            |
| Ideal-gas thermodynamics              | `IdealGas`         |
| Ideal-gas mixtures                    | `IdealGas`         |
| Rocket propellant properties          | `Propellant`       |
| CEA gas species properties            | `CombustionGas`    |
| Combustion-product gas mixtures       | `CombustionGas`    |
| Reactant mixture setup                | `Reactants`        |
| Chemical equilibrium                  | `Equilibrium`      |
| Frozen combustion-gas properties      | `CombustionGas`    |
| Equilibrium combustion-gas properties | `Equilibrium`      |
| Engineering material properties       | `Material`         |
| Direct NASA CEA data access           | `CEA`              |
| Species discovery and backend mapping | `SpeciesDatabase`  |
| Material discovery and aliases        | `MaterialDatabase` |


## Thermodynamic Reference States

Values like

* Enthalpy
* Internal energy
* Entropy
* Gibbs energy
* Helmholtz energy

don't have true absolute values. As in, without defining a reference state, saying "the enthalpy of my substance is 10000 J/kg" doesn't mean anything. Because energy changes are measurable, every thermophysical property system must set a reference point in order for absolute property values to mean anything. 

The issue is usually that different packages use different reference points. For example, a CoolProp `Fluid`, a PYroMat `IdealGas`, a NASA CEA `CombustionGas`, and a RocketProps / CEA `Propellant` may report different absolute enthalpy values even for physically similar states. Within a single backend, property differences are generally meaningful:

* Delta enthalpy
* Delta internal energy
* Delta entropy
* Heat capacity
* Density
* Speed of sound
* Transport properties

When combining results from multiple wrappers, establish a consistent thermodynamic reference basis if absolute values are required.

## Units

ThermoProp's public API uses SI units.


| Quantity             | Unit                                |
| -------------------- | ----------------------------------- |
| Pressure             | Pa                                  |
| Temperature          | K                                   |
| Density              | kg/m³                               |
| Specific volume      | m³/kg                               |
| Enthalpy             | J/kg                                |
| Internal energy      | J/kg                                |
| Entropy              | J/kg-K                              |
| Specific heat        | J/kg-K                              |
| Dynamic viscosity    | Pa-s                                |
| Kinematic viscosity  | m²/s                                |
| Thermal conductivity | W/m-K                               |
| Surface tension      | N/m                                 |
| Molar mass           | kg/mol                              |
| Molecular weight     | kg/kmol, numerically equal to g/mol |
| Material strength    | Pa                                  |


## Limitations

ThermoProp wraps and combines several independent property sources.

Property availability depends on:

* The selected wrapper
* The selected species or material
* Backend support
* Temperature range
* Pressure range
* Phase
* Availability of NASA CEA transport data

Use runtime introspection methods such as `supported_properties()`, `supported_flash_inputs()`, and `data_sources` where available.

## Acknowledgements

ThermoProp incorporates, depends on, or adapts data from:

* CoolProp
* PYroMat
* RocketProps
* NASA CEA / CEAM
* MatProtLib
* NumPy
* SciPy

ThermoProp's engineering material database was adapted from material property data compiled and distributed through the MatProtLib project.

Special thanks to Tyson Tran and the MatProtLib project for making engineering material datasets publicly available.

The author also gratefully acknowledges the NASA Glenn Research Center and the NASA CEA development team for making thermochemical and transport datasets publicly available.


## Sources

!!! info
    This section is under construction