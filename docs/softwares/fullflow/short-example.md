# Quick Start

The following is meant to be a quick example to get you familiar with FullFlow's interface. Before moving forward, make sure that you have successfully installed  `fullflow` into your Python environment. More installation instructions can be found [here](installation.md).

This short example will first go over static evaluation, then a steady-state solve, then a transient simulation. The following system will be simulated:

**Insert Image**

## Initialize a Network

Because all Components, Balances, Models, and Solvers requires a network object input, it is usually best to define the Network first. A Network is a simpply a container for all component

```python
from fullflow import Network

ExampleNetwork = Network("Example Network")
```

## Create Fluid Lookups

This system will use a `DarcyWeisbach` component, which requires knowing the pressures upstream and downstream, but also the fluid density, dynamic viscosity, etc. All of these properties are available in the *Lookup* components, which get their properties from **ThermoProp**. Upon each system solver evaluation, the lookups will generate the appropriate fluid or material properties since values like density are inherently dependent on fluid pressure and temperature, which the solver iterates on. For this particular example, since water is the fluid of interest, `FluidLookup` will be used.

```python
from fullflow import *

ExampleNetwork = Network("Example Network")

SourceFluid = FluidLookup(
    "Source Fluid",
    ExampleNetwork,
    "water",
    pressure=3e5,
    temperature=300
)
```

`SourceFluid`'s pressure and temperature are boundary conditions, so they will not be iterated on, and this component does not need to be connected to a `Boundary` component necessarily (unless you want to: it doesn't add anything to this particular simulation other than additional State tracking). 

Note the *SI Units*: Pascals for pressure and Kelvin for temperature.