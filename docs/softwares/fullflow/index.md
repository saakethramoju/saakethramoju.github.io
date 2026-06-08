# FullFlow

FullFlow is a Python framework for fluid, thermal, and propulsion network simulation.

It provides a component-based architecture for constructing and solving engineering systems composed of interconnected fluid, thermal, combustion, turbomachinery, and heat-transfer elements.

FullFlow is inspired by tools such as:

* ROCETS
* GFSSP
* NPSS
* EcosimPro

while remaining fully open-source and Python-native.

## Why FullFlow?

Engineering systems are often modeled as networks:

* Fluid networks
* Thermal networks
* Feed systems
* Propulsion systems
* Turbomachinery systems
* Heat exchanger systems
* Regenerative cooling systems
* Coupled fluid-thermal systems

Traditional network solvers are frequently proprietary, difficult to extend, or difficult to integrate into modern Python workflows.

FullFlow allows engineers to construct simulation networks directly in Python using reusable components and shared states.

For example:

```python
from fullflow import *

FeedSystem = Network("Feed System")

SourcePressure = State(5e5)
TankPressure = State(3e5)

FeedLine = DarcyWeisbach(
    "Feed Line",
    FeedSystem,
    upstream_pressure=SourcePressure,
    downstream_pressure=TankPressure,
)

solution = SteadyState(FeedSystem).solve()
```

## Features

* Component-based network architecture
* Steady-state and transient network solver
* Fluid, thermal, and propulsion modeling
* Real fluids, ideal gases, and propellants
* Temperature-dependent material properties
* Compressible and incompressible flow
* Conduction, convection, and radiation
* Turbomachinery maps
* Model switching and correlation comparison
* Excel and DataFrame result export
* Pure Python implementation

## Example Applications

FullFlow can be used to model:

* Pump-fed liquid rocket engines
* Pressure-fed propulsion systems
* Turbomachinery and pump maps
* Counterflow heat exchangers
* Regenerative cooling systems
* Fluid mixture separation and mixing
* Compressible flow systems
* Coupled fluid-thermal networks
* Material thermal response
* Engineering correlation studies

## Fluid Systems

FullFlow supports modeling of:

* Compressible flow
* Incompressible flow
* Real fluids
* Ideal gases
* Fluid mixtures
* Liquid rocket propellants
* Flow splitting
* Flow mixing

through integration with ThermoProp.

## Thermal Systems

FullFlow supports:

* Lumped thermal networks
* Conduction
* Convection
* Radiation
* Temperature-dependent material properties
* Coupled fluid-thermal simulation

## Propulsion Systems

FullFlow is designed to support rocket propulsion applications including:

* Feed systems
* Turbopumps
* Turbines
* Combustion chambers
* Nozzles
* Regenerative cooling systems
* Integrated propulsion cycles

## Dependencies

FullFlow builds upon several scientific and aerospace libraries:

* NumPy
* SciPy
* Pandas
* OpenPyXL
* ThermoProp
* RocketCEA
* Rich

## Project Status

FullFlow is currently under active development.

Current development focuses on:

* Transient modeling
* Unit conversions
* Advanced combustors
* Improved transient simulation
* Two-phase flow support
* Control system modeling
* Advanced turbomachinery models
* Heat exchanger libraries
* Cycle analysis tools
* Expanded reporting and visualization

The API may evolve as capabilities continue to expand.

## Contributing

Bug reports, feature requests, discussions, and pull requests are welcome.

Please open an issue in the GitHub repo if you encounter a problem or would like to propose an enhancement.

## Source Code

GitHub:

[https://github.com/saakethramoju/FullFlow](https://github.com/saakethramoju/FullFlow)

FullFlow is released under the GNU General Public License v3.0.

See `LICENSE` in the GitHub repo for details.