# Quick Start

The following is meant to be a quick example to get you familiar with FullFlow's interface. Before moving forward, make sure that you have successfully installed  `fullflow` into your Python environment. More installation instructions can be found [here](installation.md).

This short example will first go over static evaluation, then a steady-state solve, then a transient simulation. The following system will be simulated:

!!! warning "Documentation TODO"
    Add system schematic for the example network.

## Initialize a Network

Because all components, balances, models, and solvers require a network object input, it is usually best to define the Network first. A `Network` is simply a container for all components, states, residuals, and tracked outputs.

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

NodeFluid = FluidLookup(
    "Node Fluid",
    ExampleNetwork,
    SourceFluid.composition,
    pressure=2e5,
    temperature=300
)
```

This `NodeFluid` object simply represents the fluid properties of the fluid node that sits between the Source and Drain. The node is not necessarily any particular volume; it could simply be a section of the same pipe whose pressure and temperature we are interested in.

Note that because we do not actually know this node's pressure and temperature beforehand, the values provided to the lookup are guess values that will be used as starting points for iteration.

## Assign Components

There is no need to define a boundary node, so we will jump directly to the first branch in the system.

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

NodeFluid = FluidLookup(
    "Node Fluid",
    ExampleNetwork,
    SourceFluid.composition,
    pressure=2e5,
    temperature=300
)

line1_mass_flow = State(5)

Line1 = DarcyWeisbach(
    "Line 1",
    ExampleNetwork,
    mass_flow=line1_mass_flow,
    upstream_pressure=SourceFluid.pressure,
    downstream_pressure=NodeFluid.pressure,
    density=SourceFluid.density,
    length=1,
    cross_sectional_area=(3.14/4) * (0.0127**2),
    hydraulic_diameter=0.0127,
    friction_factor=2e-5
)
```

For the `DarcyWeisbach` component, a guess mass_flow is necessary. Notice how an external State `line1_mass_flow` was passed into the `mass_flow` attribute. We could have just as easily done `mass_flow=5` instead, but this shows how States of interest can easily be passed into components. Now, if we want to add bounds to the mass flow as it is iterated on, we can do:

```python
line1_mass_flow = State(5, bounds=(0, 10), keep_feasible=True)
```

Bounds can slow down the solver or increase the residual sizes, so we will not use them here for this simple application. We can also track this external State in the solver output by doing:

```python
ExampleNetwork.track(
    "Line 1 Mass Flow",
    line1_mass_flow
)
```

As mentioned, the line is one meter long and 0.5 inches in diameter. Notice that the friction factor is hardcoded. To get the true friction factor, it is necessary to recompute the value every iteration, which can be done by one of the friction factor components. For this example, we will use `Colebrook`:

```python
Line1 = DarcyWeisbach(
    "Line 1",
    ExampleNetwork,
    mass_flow=line1_mass_flow,
    upstream_pressure=SourceFluid.pressure,
    downstream_pressure=NodeFluid.pressure,
    density=SourceFluid.density,
    length=1,
    cross_sectional_area=(3.14/4) * (0.0127**2),
    hydraulic_diameter=0.0127,
    friction_factor=2e-5
)

Line1Friction = Colebrook(
    "Line 1 Friction",
    ExampleNetwork,
    mass_flow=Line1.mass_flow,
    friction_factor=Line1.friction_factor,
    hydraulic_diameter=Line1.hydraulic_diameter,
    dynamic_viscosity=SourceFluid.dynamic_viscosity,
    cross_sectional_area=Line1.cross_sectional_area,
    roughness=5e-6
)
```

In order to determine the node's temperature and pressure, we need a `Volume` Component:

```python
Node1 = Volume(
    "Node 1",
    ExampleNetwork,
    pressure=NodeFluid.pressure,
    enthalpy=NodeFluid.enthalpy,
    volume=1,
    total_enthalpy_in=SourceFluid.enthalpy,
    mass_flow_in=Line1.mass_flow
)
```

For a static evaluation or steady-state simulation, the volume value does not affect the algebraic residuals. Instead of temperature, the node will iterate on enthalpy as a way to account for saturated fluid states (temperature is constant during a phase change). However, the node lookup was initialized with pressure and temperature, which makes those the default flash parameters for the lookup (the lookup gets all properties from pressure and temperature, so enthalpy would be derived from those two values, and it would not be an independent iterable). To solve this, a `flash_values` input can be provided to the lookup:

```python
NodeFluid = FluidLookup(
    "Node Fluid",
    ExampleNetwork,
    SourceFluid.composition,
    pressure=2e5,
    temperature=300,
    flash_values=('pressure', 'enthalpy')
)
```

Even though `mass_flow_out` is needed to create a finite residual, it is not inputted here in this Component. Instead, to avoid creating an external State, `Node1.mass_flow_out` will simply be passed in as an input to the downstream branch's mass flow attribute.

The downstream branch will be a `DischargeCoefficient` branch, where the effective area, $C_dA$, is known from experimental data.

```python
Line2 = DischargeCoefficient(
    "Line 2",
    ExampleNetwork,
    upstream_pressure=Node1.pressure,
    downstream_pressure=101325,
    density=NodeFluid.density,
    discharge_coefficient=0.75,
    cross_sectional_area=(3.14/4) * (0.0127**2),
    mass_flow=Node1.mass_flow_out
)
```

## Run a Static Evaluation

A static evaluation simply evaluates all of the components in the Network with the current State values (so the guess values). Static evaluation is useful for debugging because it shows whether each component can evaluate successfully before the nonlinear solver is run. There are multiple ways to do this:

```python
SteadyState(ExampleNetwork).static_evaluate(verbose=True, print_solution=True)
```

or

```python
SteadyState(ExampleNetwork).solve(static=True, verbose=True, print_solution=True)
```

The `verbose` and `print_solution` attributes are optional and are useful for viewing the result in the terminal window.
Either way, the evaluation yields the same result. So the full code is:

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

NodeFluid = FluidLookup(
    "Node Fluid",
    ExampleNetwork,
    SourceFluid.composition,
    pressure=2e5,
    temperature=300,
    flash_values=('pressure', 'enthalpy')
)

line1_mass_flow = State(5)
ExampleNetwork.track(
    "Line 1 Mass Flow",
    line1_mass_flow
)

Line1 = DarcyWeisbach(
    "Line 1",
    ExampleNetwork,
    mass_flow=line1_mass_flow,
    upstream_pressure=SourceFluid.pressure,
    downstream_pressure=NodeFluid.pressure,
    density=SourceFluid.density,
    length=1,
    cross_sectional_area=(3.14/4) * (0.0127**2),
    hydraulic_diameter=0.0127,
    friction_factor=2e-5
)

Line1Friction = Colebrook(
    "Line 1 Friction",
    ExampleNetwork,
    mass_flow=Line1.mass_flow,
    friction_factor=Line1.friction_factor,
    hydraulic_diameter=Line1.hydraulic_diameter,
    dynamic_viscosity=SourceFluid.dynamic_viscosity,
    cross_sectional_area=Line1.cross_sectional_area,
    roughness=5e-6
)

Node1 = Volume(
    "Node 1",
    ExampleNetwork,
    pressure=NodeFluid.pressure,
    enthalpy=NodeFluid.enthalpy,
    volume=1,
    total_enthalpy_in=SourceFluid.enthalpy,
    mass_flow_in=Line1.mass_flow
)

Line2 = DischargeCoefficient(
    "Line 2",
    ExampleNetwork,
    upstream_pressure=Node1.pressure,
    downstream_pressure=101325,
    density=NodeFluid.density,
    discharge_coefficient=0.75,
    cross_sectional_area=(3.14/4) * (0.0127**2),
    mass_flow=Node1.mass_flow_out
)

SteadyState(ExampleNetwork).solve(static=True, verbose=True, print_solution=True)
```

The result is:

??? success "Static Evaluation Solution"

    ```text
             Static Network Evaluation

      Quantity                          Value
     ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
      Mode                  Static evaluation
      Nonlinear solve           Not performed
      Evaluation time                 0.001 s
      Components                            6
      Iteration variables                  48
      Residuals                             3


                                        Example Network Solution

      Component         Type                   Attribute                                      Value
     ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
      Source Fluid      FluidLookup            fluid.Water                                        1
      Source Fluid      FluidLookup            pressure                                      300000
      Source Fluid      FluidLookup            temperature                                      300
      Source Fluid      FluidLookup            flash_values                         <uninitialized>
      Node Fluid        FluidLookup            fluid.Water                                        1
      Node Fluid        FluidLookup            pressure                                      200000
      Node Fluid        FluidLookup            temperature                                      300
      Node Fluid        FluidLookup            enthalpy                                      112746
      Node Fluid        FluidLookup            flash_values                ('pressure', 'enthalpy')
      Line 1            DarcyWeisbach          mass_flow                                          5
      Line 1            DarcyWeisbach          upstream_pressure                             300000
      Line 1            DarcyWeisbach          downstream_pressure                           200000
      Line 1            DarcyWeisbach          length                                             1
      Line 1            DarcyWeisbach          cross_sectional_area                     0.000126613
      Line 1            DarcyWeisbach          hydraulic_diameter                            0.0127
      Line 1            DarcyWeisbach          density                                      996.646
      Line 1            DarcyWeisbach          friction_factor                            0.0168149
      Line 1            DarcyWeisbach          effective_area                           0.000354148
      Line 1 Friction   Colebrook              mass_flow                                          5
      Line 1 Friction   Colebrook              friction_factor                            0.0168149
      Line 1 Friction   Colebrook              hydraulic_diameter                            0.0127
      Line 1 Friction   Colebrook              dynamic_viscosity                        0.000853725
      Line 1 Friction   Colebrook              cross_sectional_area                     0.000126613
      Line 1 Friction   Colebrook              poiseuille_number                                 16
      Line 1 Friction   Colebrook              roughness                                      5e-06
      Line 1 Friction   Colebrook              reynolds_number                               587461
      Line 1 Friction   Colebrook              reynolds_number_threshold                       2300
      Line 1 Friction   Colebrook              Deff                                          0.0127
      Node 1            Volume                 pressure                                      200000
      Node 1            Volume                 enthalpy                                      112746
      Node 1            Volume                 volume                                             1
      Node 1            Volume                 total_enthalpy_in                             112838
      Node 1            Volume                 total_enthalpy_out                   <uninitialized>
      Node 1            Volume                 heat_rate                            <uninitialized>
      Node 1            Volume                 temperature                          <uninitialized>
      Node 1            Volume                 density                              <uninitialized>
      Node 1            Volume                 internal_energy                      <uninitialized>
      Node 1            Volume                 mass_flow_in                                       5
      Node 1            Volume                 mass_flow_out                                1.33173
      Line 2            DischargeCoefficient   upstream_pressure                             200000
      Line 2            DischargeCoefficient   downstream_pressure                           101325
      Line 2            DischargeCoefficient   density                                      996.601
      Line 2            DischargeCoefficient   discharge_coefficient                           0.75
      Line 2            DischargeCoefficient   cross_sectional_area                     0.000126613
      Line 2            DischargeCoefficient   mass_flow                                    1.33173
      Example Network   TrackedState           Line 1 Mass Flow                                   5
    ```

## Run a Steady-State Simulation

With the Network set up, running a steady-state simulation is just a matter of altering the `.solve()` call.

```python
SteadyState(ExampleNetwork).solve(verbose=True, print_solution=True)
```

The full code is:

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

NodeFluid = FluidLookup(
    "Node Fluid",
    ExampleNetwork,
    SourceFluid.composition,
    pressure=2e5,
    temperature=300,
    flash_values=('pressure', 'enthalpy')
)

line1_mass_flow = State(5)
ExampleNetwork.track(
    "Line 1 Mass Flow",
    line1_mass_flow
)

Line1 = DarcyWeisbach(
    "Line 1",
    ExampleNetwork,
    mass_flow=line1_mass_flow,
    upstream_pressure=SourceFluid.pressure,
    downstream_pressure=NodeFluid.pressure,
    density=SourceFluid.density,
    length=1,
    cross_sectional_area=(3.14/4) * (0.0127**2),
    hydraulic_diameter=0.0127,
    friction_factor=2e-5
)

Line1Friction = Colebrook(
    "Line 1 Friction",
    ExampleNetwork,
    mass_flow=Line1.mass_flow,
    friction_factor=Line1.friction_factor,
    hydraulic_diameter=Line1.hydraulic_diameter,
    dynamic_viscosity=SourceFluid.dynamic_viscosity,
    cross_sectional_area=Line1.cross_sectional_area,
    roughness=5e-6
)

Node1 = Volume(
    "Node 1",
    ExampleNetwork,
    pressure=NodeFluid.pressure,
    enthalpy=NodeFluid.enthalpy,
    volume=1,
    total_enthalpy_in=SourceFluid.enthalpy,
    mass_flow_in=Line1.mass_flow
)

Line2 = DischargeCoefficient(
    "Line 2",
    ExampleNetwork,
    upstream_pressure=Node1.pressure,
    downstream_pressure=101325,
    density=NodeFluid.density,
    discharge_coefficient=0.75,
    cross_sectional_area=(3.14/4) * (0.0127**2),
    mass_flow=Node1.mass_flow_out
)

SteadyState(ExampleNetwork).solve(verbose=True, print_solution=True)
```

The result is:

??? success "Steady-State Solver Solution"

    ```text
                            Steady-State Solver Summary

      Quantity                                                                  Value
     ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
      Success                                                                    True
      Status                                                                        3
      Message                              `xtol` termination condition is satisfied.
      Solver method                                                               trf
      Jacobian method                                                         3-point
      Solve time                                                              0.011 s
      Function evaluations                                                          5
      Jacobian evaluations                                                          5
      Cost                                                               4.320292e-18
      Optimality                                                            3.317e-04
      Max |residual|                                                        2.939e-09
      RMS residual                                                          1.697e-09
      Max normalized variable adjustment                                    2.575e+00
      Residual tolerance                                                    1.000e-02
      ftol                                                                  1.000e-08
      xtol                                                                  1.000e-08
      gtol                                                                  1.000e-08

                                               Solution Variables

                                                                                        Normalized Variable
      Index   Variable                            Value   Variable Adjustment                    Adjustment
     ───────────────────────────────────────────────────────────────────────────────────────────────────────
       x[0]   Line 1.mass_flow             1.398701e+00         -3.601299e+00                     2.575e+00
              Line 1 Friction.mass_flow
              Node 1.mass_flow_in
       x[1]   Node Fluid.pressure          2.101733e+05         +1.017331e+04                     4.840e-02
              Line 1.downstream_pressure
              Node 1.pressure
              Line 2.upstream_pressure
       x[2]   Node Fluid.enthalpy          1.128378e+05         +9.206225e+01                     8.159e-04
              Node 1.enthalpy

                      Residuals

      Index   Residual                     Value
     ────────────────────────────────────────────
       r[0]   Line 1.residual[0]   -2.220446e-16
       r[1]   Node 1.residual[0]   -2.597922e-14
       r[2]   Node 1.residual[1]   -2.939487e-09


                                        Example Network Solution

      Component         Type                   Attribute                                      Value
     ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
      Source Fluid      FluidLookup            fluid.Water                                        1
      Source Fluid      FluidLookup            pressure                                      300000
      Source Fluid      FluidLookup            temperature                                      300
      Source Fluid      FluidLookup            flash_values                         <uninitialized>
      Node Fluid        FluidLookup            fluid.Water                                        1
      Node Fluid        FluidLookup            pressure                                      210173
      Node Fluid        FluidLookup            temperature                                   300.02
      Node Fluid        FluidLookup            enthalpy                                      112838
      Node Fluid        FluidLookup            flash_values                ('pressure', 'enthalpy')
      Line 1            DarcyWeisbach          mass_flow                                     1.3987
      Line 1            DarcyWeisbach          upstream_pressure                             300000
      Line 1            DarcyWeisbach          downstream_pressure                           210173
      Line 1            DarcyWeisbach          length                                             1
      Line 1            DarcyWeisbach          cross_sectional_area                     0.000126613
      Line 1            DarcyWeisbach          hydraulic_diameter                            0.0127
      Line 1            DarcyWeisbach          density                                      996.646
      Line 1            DarcyWeisbach          friction_factor                             0.018652
      Line 1            DarcyWeisbach          effective_area                           0.000104529
      Line 1 Friction   Colebrook              mass_flow                                     1.3987
      Line 1 Friction   Colebrook              friction_factor                             0.018652
      Line 1 Friction   Colebrook              hydraulic_diameter                            0.0127
      Line 1 Friction   Colebrook              dynamic_viscosity                        0.000853725
      Line 1 Friction   Colebrook              cross_sectional_area                     0.000126613
      Line 1 Friction   Colebrook              poiseuille_number                                 16
      Line 1 Friction   Colebrook              roughness                                      5e-06
      Line 1 Friction   Colebrook              reynolds_number                               164336
      Line 1 Friction   Colebrook              reynolds_number_threshold                       2300
      Line 1 Friction   Colebrook              Deff                                          0.0127
      Node 1            Volume                 pressure                                      210173
      Node 1            Volume                 enthalpy                                      112838
      Node 1            Volume                 volume                                             1
      Node 1            Volume                 total_enthalpy_in                             112838
      Node 1            Volume                 total_enthalpy_out                   <uninitialized>
      Node 1            Volume                 heat_rate                            <uninitialized>
      Node 1            Volume                 temperature                          <uninitialized>
      Node 1            Volume                 density                              <uninitialized>
      Node 1            Volume                 internal_energy                      <uninitialized>
      Node 1            Volume                 mass_flow_in                                  1.3987
      Node 1            Volume                 mass_flow_out                                 1.3987
      Line 2            DischargeCoefficient   upstream_pressure                             210173
      Line 2            DischargeCoefficient   downstream_pressure                           101325
      Line 2            DischargeCoefficient   density                                        996.6
      Line 2            DischargeCoefficient   discharge_coefficient                           0.75
      Line 2            DischargeCoefficient   cross_sectional_area                     0.000126613
      Line 2            DischargeCoefficient   mass_flow                                     1.3987
      Example Network   TrackedState           Line 1 Mass Flow                              1.3987
    ```

So we have determined, with this very simple setup, that the pressure at the node is 210173 Pascals and the temperature is basically exactly what it was at the Source.

When looking at the output, it is important to gauge the size of the residuals. Here, they are very small, indicating a good result.

Deviations from reality in the solution could have happened because of:

* Using the `SourceFluid` enthalpy as the total enthalpy into the node instead of the enthalpy exiting `Line1`
* Using only the upstream viscosities and densities for the branches.

To improve the density estimate, we can use State math to define a derived State that passes the average density of `SourceFluid` and `NodeFluid` to `Line1`:

```python
line1_density = 0.5*(SourceFluid.density + NodeFluid.density)
```

This makes the full code:

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

NodeFluid = FluidLookup(
    "Node Fluid",
    ExampleNetwork,
    SourceFluid.composition,
    pressure=2e5,
    temperature=300,
    flash_values=('pressure', 'enthalpy')
)

line1_mass_flow = State(5)
ExampleNetwork.track(
    "Line 1 Mass Flow",
    line1_mass_flow
)

line1_density = 0.5*(SourceFluid.density + NodeFluid.density)

Line1 = DarcyWeisbach(
    "Line 1",
    ExampleNetwork,
    mass_flow=line1_mass_flow,
    upstream_pressure=SourceFluid.pressure,
    downstream_pressure=NodeFluid.pressure,
    density=line1_density,
    length=1,
    cross_sectional_area=(3.14/4) * (0.0127**2),
    hydraulic_diameter=0.0127,
    friction_factor=2e-5
)

Line1Friction = Colebrook(
    "Line 1 Friction",
    ExampleNetwork,
    mass_flow=Line1.mass_flow,
    friction_factor=Line1.friction_factor,
    hydraulic_diameter=Line1.hydraulic_diameter,
    dynamic_viscosity=SourceFluid.dynamic_viscosity,
    cross_sectional_area=Line1.cross_sectional_area,
    roughness=5e-6
)

Node1 = Volume(
    "Node 1",
    ExampleNetwork,
    pressure=NodeFluid.pressure,
    enthalpy=NodeFluid.enthalpy,
    volume=1,
    total_enthalpy_in=SourceFluid.enthalpy,
    mass_flow_in=Line1.mass_flow
)

Line2 = DischargeCoefficient(
    "Line 2",
    ExampleNetwork,
    upstream_pressure=Node1.pressure,
    downstream_pressure=101325,
    density=NodeFluid.density,
    discharge_coefficient=0.75,
    cross_sectional_area=(3.14/4) * (0.0127**2),
    mass_flow=Node1.mass_flow_out
)

SteadyState(ExampleNetwork).solve(verbose=True, print_solution=True)
```

Now the result is:

??? success "Steady-State Solver Solution"

    ```text
                            Steady-State Solver Summary

      Quantity                                                                  Value
     ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
      Success                                                                    True
      Status                                                                        3
      Message                              `xtol` termination condition is satisfied.
      Solver method                                                               trf
      Jacobian method                                                         3-point
      Solve time                                                              0.011 s
      Function evaluations                                                          5
      Jacobian evaluations                                                          5
      Cost                                                               1.145189e-18
      Optimality                                                            1.708e-04
      Max |residual|                                                        1.513e-09
      RMS residual                                                          8.738e-10
      Max normalized variable adjustment                                    2.575e+00
      Residual tolerance                                                    1.000e-02
      ftol                                                                  1.000e-08
      xtol                                                                  1.000e-08
      gtol                                                                  1.000e-08

                                               Solution Variables

                                                                                        Normalized Variable
      Index   Variable                            Value   Variable Adjustment                    Adjustment
     ───────────────────────────────────────────────────────────────────────────────────────────────────────
       x[0]   Line 1.mass_flow             1.398693e+00         -3.601307e+00                     2.575e+00
              Line 1 Friction.mass_flow
              Node 1.mass_flow_in
       x[1]   Node Fluid.pressure          2.101722e+05         +1.017216e+04                     4.840e-02
              Line 1.downstream_pressure
              Node 1.pressure
              Line 2.upstream_pressure
       x[2]   Node Fluid.enthalpy          1.128378e+05         +9.206225e+01                     8.159e-04
              Node 1.enthalpy

                      Residuals

      Index   Residual                     Value
     ────────────────────────────────────────────
       r[0]   Line 1.residual[0]   -6.883383e-15
       r[1]   Node 1.residual[0]   -1.332268e-14
       r[2]   Node 1.residual[1]   -1.513399e-09


                                        Example Network Solution

      Component         Type                   Attribute                                      Value
     ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
      Source Fluid      FluidLookup            fluid.Water                                        1
      Source Fluid      FluidLookup            pressure                                      300000
      Source Fluid      FluidLookup            temperature                                      300
      Source Fluid      FluidLookup            flash_values                         <uninitialized>
      Node Fluid        FluidLookup            fluid.Water                                        1
      Node Fluid        FluidLookup            pressure                                      210172
      Node Fluid        FluidLookup            temperature                                   300.02
      Node Fluid        FluidLookup            enthalpy                                      112838
      Node Fluid        FluidLookup            flash_values                ('pressure', 'enthalpy')
      Line 1            DarcyWeisbach          mass_flow                                    1.39869
      Line 1            DarcyWeisbach          upstream_pressure                             300000
      Line 1            DarcyWeisbach          downstream_pressure                           210172
      Line 1            DarcyWeisbach          length                                             1
      Line 1            DarcyWeisbach          cross_sectional_area                     0.000126613
      Line 1            DarcyWeisbach          hydraulic_diameter                            0.0127
      Line 1            DarcyWeisbach          density                                      996.623
      Line 1            DarcyWeisbach          friction_factor                             0.018652
      Line 1            DarcyWeisbach          effective_area                           0.000104529
      Line 1 Friction   Colebrook              mass_flow                                    1.39869
      Line 1 Friction   Colebrook              friction_factor                             0.018652
      Line 1 Friction   Colebrook              hydraulic_diameter                            0.0127
      Line 1 Friction   Colebrook              dynamic_viscosity                        0.000853725
      Line 1 Friction   Colebrook              cross_sectional_area                     0.000126613
      Line 1 Friction   Colebrook              poiseuille_number                                 16
      Line 1 Friction   Colebrook              roughness                                      5e-06
      Line 1 Friction   Colebrook              reynolds_number                               164335
      Line 1 Friction   Colebrook              reynolds_number_threshold                       2300
      Line 1 Friction   Colebrook              Deff                                          0.0127
      Node 1            Volume                 pressure                                      210172
      Node 1            Volume                 enthalpy                                      112838
      Node 1            Volume                 volume                                             1
      Node 1            Volume                 total_enthalpy_in                             112838
      Node 1            Volume                 total_enthalpy_out                   <uninitialized>
      Node 1            Volume                 heat_rate                            <uninitialized>
      Node 1            Volume                 temperature                          <uninitialized>
      Node 1            Volume                 density                              <uninitialized>
      Node 1            Volume                 internal_energy                      <uninitialized>
      Node 1            Volume                 mass_flow_in                                 1.39869
      Node 1            Volume                 mass_flow_out                                1.39869
      Line 2            DischargeCoefficient   upstream_pressure                             210172
      Line 2            DischargeCoefficient   downstream_pressure                           101325
      Line 2            DischargeCoefficient   density                                        996.6
      Line 2            DischargeCoefficient   discharge_coefficient                           0.75
      Line 2            DischargeCoefficient   cross_sectional_area                     0.000126613
      Line 2            DischargeCoefficient   mass_flow                                    1.39869
      Example Network   TrackedState           Line 1 Mass Flow                             1.39869
    ```

## Run a Transient Simulation

!!! warning "Documentation TODO"
    Add transient stuff