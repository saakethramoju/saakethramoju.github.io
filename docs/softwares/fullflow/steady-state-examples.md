# Steady-State Examples

!!! warning "Documentation TODO"
    This page is a work in progress.

All examples can be accessed by cloning the FullFlow [Github repo](https://github.com/saakethramoju/FullFlow). The examples are located under the *examples* folder.

Clone the repository:

```bash
git clone https://github.com/saakethramoju/FullFlow.git
cd FullFlow
```

Install dependencies:

```bash
uv sync
```

Run an example:

```bash
uv run python examples/pump_fed_engine.py
```

You can also simply download the example files directly and run them in any environment you want.

## Pump-Fed Rocket Engine

FullFlow can be used to model complete liquid rocket propulsion systems, including pressurization systems, tanks, pumps, injector manifolds, combustion chambers, and nozzles.

Run the example:

```bash
uv run python examples/pump_fed_engine.py
```

```python
from fullflow import *

PumpNetwork = Network("Pumped System")

fuel_shaft_speed = State(25000)
ox_shaft_speed = State(25000)

FuelTankFluid = FluidLookup(...)
OxTankFluid = FluidLookup(...)

FuelPump = PolytropicPump(...)
OxPump = PolytropicPump(...)

MainChamber = MainCombustionChamber(...)
Nozzle = RocketCEAChokedNozzle(...)

solution = SteadyState(PumpNetwork).solve()
```

See `examples/pump_fed_engine.py` for the complete model.

## Mixture Splitter

FullFlow supports fluid mixtures, composition tracking, mixing, and separation.

Run the example:

```bash
uv run python examples/mixture_splitter.py
```

```python
from fullflow import *

SourceFluid = FluidLookup(
    "Source Fluid",
    MixtureNetwork,
    {"gn2": 0.75, "O2": 0.01, "Ar": 0.24},
    pressure=3e5,
    temperature=300,
)

Separator = FlowSplitter(
    "Separator",
    MixtureNetwork,
    pressure=VolumeFluid.pressure,
    composition=VolumeFluid.composition,
    composition_out1=SeparatorOutlet1Composition,
    composition_out2=SeparatorOutlet2Composition,
)

solution = SteadyState(MixtureNetwork).solve()
```

This example demonstrates:

* Multicomponent fluid mixtures
* Composition tracking
* Flow splitting
* Composition balances
* Mixture thermodynamic property evaluation

See `examples/mixture_splitter.py` for the complete model.

## Counterflow Heat Exchanger

FullFlow supports coupled fluid and thermal simulations, allowing heat exchangers to be modeled using fluid networks, thermal networks, material properties, and heat-transfer correlations within a unified framework.

Run the example:

```bash
uv run python examples/heat_exchanger.py
```

```python
from fullflow import *

HeatExchanger = Network("Heat Exchanger")

LiquidSource = FluidLookup(
    "Liquid Source",
    HeatExchanger,
    "rp-1",
    pressure=6e5,
    temperature=1000,
)

CoolantSource = FluidLookup(
    "Coolant Source",
    HeatExchanger,
    "water",
    pressure=20e5,
    temperature=300,
)

TubeNode1 = Solid(...)
TubeNode2 = Solid(...)

TubeConduction = Conduction(...)

Liquid1Solid1Convection = Convection(...)
Coolant2Solid1Convection = Convection(...)

HeatTransferModel = Model(
    "Heat Transfer Correlation",
    HeatExchanger,
    GnielinskiOption,
    DittusBoelterOption,
)

solution = SteadyState(HeatExchanger).solve(
    model="Heat Transfer Correlation"
)
```

This example demonstrates:

* Counterflow heat exchanger modeling
* Coupled fluid and thermal networks
* Temperature-dependent material properties
* Conduction and convection
* Internal and annular flow passages
* Gnielinski and Dittus-Boelter heat-transfer correlations
* Model switching with `Model` and `ModelOption`

See `examples/heat_exchanger.py` for the complete model.

## Model Comparison and Correlation Sweeps

FullFlow supports interchangeable physics models through `Model` and `ModelOption`.

This allows multiple component formulations to be evaluated within the same network without rebuilding the system.

Run the example:

```bash
uv run python examples/model_comparison.py
```

```python
from fullflow import *

PumpModel = Model(
    "Main Pump",
    PumpNetwork,
    ConstantDensityPumpOption,
    PolytropicPumpOption,
)

solution = SteadyState(PumpNetwork).solve(
    model="Main Pump",
    evaluate_all_model_options=True,
)
```

This example demonstrates:

* Model switching
* Alternative component formulations
* Pump-model comparison
* Shared turbomachinery maps
* Correlation sweeps
* Automated evaluation of multiple model options

See `examples/model_comparison.py` for the complete model.