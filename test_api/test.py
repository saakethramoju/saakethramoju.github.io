class Component:
    pass


class Network:
    pass


class State:
    pass

class Composition: pass


class FlowMixer(Component):
    """
    Two-inlet mixing volume with optional energy and species conservation.

    `FlowMixer` combines two incoming streams into a single outlet stream while
    enforcing steady-state mass conservation. Optional energy and species
    balances may also be solved when the corresponding states are provided.

    The outlet composition is calculated from the mass-flow-weighted mixture of
    the two inlet compositions.

    Species mixing:

    `Y_out = (mdot1 * Y1 + mdot2 * Y2) / (mdot1 + mdot2)`

    for each species present in either inlet stream.

    Residuals
    ---------
    mass_balance : float
        Enforces steady-state mass conservation:

        `mass_flow_in1 + mass_flow_in2 - mass_flow_out = 0`

    energy_balance : float, optional
        Enforces steady-state flow energy conservation:

        `mass_flow_in1 * total_enthalpy_in1
        + mass_flow_in2 * total_enthalpy_in2
        - mass_flow_out * total_enthalpy_out
        + heat_rate = 0`

        Included only when energy solving is enabled.

    Iteration Variables
    -------------------
    pressure : State
        Mixer pressure

    enthalpy : State, optional
        Mixer specific enthalpy when energy conservation is enabled

    Parameters
    ----------
    name : str
        Component name
    network : Network
        Network that owns this component
    pressure : State
        Mixer pressure
    volume : float
        Mixer control volume
    enthalpy : State, optional
        Mixer specific enthalpy
    temperature : State, optional
        Mixer temperature
    density : State, optional
        Mixer density
    internal_energy : State, optional
        Mixer specific internal energy
    heat_rate : State or float, optional
        Net heat rate into the mixer
    composition : Composition, optional
        Mixed outlet composition
    composition_in1 : Composition, optional
        Composition of inlet stream 1
    composition_in2 : Composition, optional
        Composition of inlet stream 2
    total_enthalpy_in1 : State, optional
        Total specific enthalpy of inlet stream 1
    total_enthalpy_in2 : State, optional
        Total specific enthalpy of inlet stream 2
    total_enthalpy_out : State, optional
        Outlet total specific enthalpy. If omitted, the mixer enthalpy is used
    mass_flow_in1 : State, optional
        Inlet mass flow rate 1
    mass_flow_in2 : State, optional
        Inlet mass flow rate 2
    mass_flow_out : State, optional
        Outlet mass flow rate
    """

    def __init__(
        self,
        name: str,
        network: Network,
        pressure: State,
        volume: float,
        enthalpy: State | None = None,
        temperature: State | None = None,
        density: State | None = None,
        internal_energy: State | None = None,
        heat_rate: State | float | None = None,
        composition: Composition = Composition(),
        composition_in1: Composition = Composition(),
        composition_in2: Composition = Composition(),
        total_enthalpy_in1: State | None = None,
        total_enthalpy_in2: State | None = None,
        total_enthalpy_out: State | None = None,
        mass_flow_in1: State | None = None,
        mass_flow_in2: State | None = None,
        mass_flow_out: State | None = None,
    ):
        self.setup()

        self._solve_energy = (
            self.total_enthalpy_in1.is_assigned
            and self.enthalpy.is_assigned
            and self.total_enthalpy_in2.is_assigned
        )

        self._solve_species = (
            self.composition.is_assigned
            and self.composition_in1.is_assigned
            and self.composition_in2.is_assigned
        )

    def evaluate_states(self):
        if not self._solve_species:
            return

        extra_species = set(self.composition.species) - (
            set(self.composition_in1.species)
            | set(self.composition_in2.species)
        )

        if extra_species:
            raise ValueError(
                f"{self.name}: composition contains species not in "
                f"composition_in1 or composition_in2: {extra_species}"
            )

        self.composition.copy_from(self.composition_in1, copy_values=False)
        self.composition.copy_from(self.composition_in2, copy_values=False)

        if (
            not self.mass_flow_in1.is_assigned
            or not self.mass_flow_in2.is_assigned
            or not self.mass_flow_out.is_assigned
        ):
            return

        mdot1 = self.mass_flow_in1.value
        mdot2 = self.mass_flow_in2.value
        mdot_total = mdot1 + mdot2

        if abs(mdot_total) < 1e-12:
            return

        for species in self.composition.species:
            yi1 = (
                self.composition_in1[species].value
                if species in self.composition_in1.species
                else 0.0
            )

            yi2 = (
                self.composition_in2[species].value
                if species in self.composition_in2.species
                else 0.0
            )

            self.composition[species].value = (
                mdot1 * yi1 + mdot2 * yi2
            ) / mdot_total

    @property
    def iteration_variables(self) -> list[State]:
        variables = [self.pressure]

        if self._solve_energy:
            variables.append(self.enthalpy)

        return variables

    @property
    def residuals(self) -> list[float]:
        residuals = [
            self.mass_flow_in1.value
            + self.mass_flow_in2.value
            - self.mass_flow_out.value
        ]

        if self._solve_energy:
            qdot = self.heat_rate.value if self.heat_rate.is_assigned else 0.0

            h_out = (
                self.total_enthalpy_out.value
                if self.total_enthalpy_out.is_assigned
                else self.enthalpy.value
            )

            residuals.append(
                self.mass_flow_in1.value * self.total_enthalpy_in1.value
                + self.mass_flow_in2.value * self.total_enthalpy_in2.value
                - self.mass_flow_out.value * h_out
                + qdot
            )

        return residuals
    


class Boundary(Component):
    """
    Fixed pressure and temperature boundary condition.

    `Boundary` represents a thermodynamic boundary where both pressure and
    temperature are prescribed. It is commonly used as a source, sink, ambient
    condition, reservoir, or external system interface.

    This component introduces no iteration variables and contributes no
    residual equations.

    Parameters
    ----------
    name : str
        Component name.
    network : Network
        Network that owns this component.
    pressure : State
        Boundary pressure [Pa].
    temperature : State
        Boundary temperature [K].
    """

    def __init__(
        self,
        name: str,
        network: Network,
        pressure: State,
        temperature: State,
    ):
        self.setup()


class Volume(Component):
    """
    Lumped fluid volume with steady-state mass and energy conservation.

    Parameters
    ----------
    name : str
        Component name.
    network : Network
        Network that owns this component.
    pressure : State
        Internal volume pressure [Pa].
    enthalpy : State
        Internal volume specific enthalpy [J/kg].
    volume : float
        Volume of the control volume [m^3].
    total_enthalpy_in : State
        Total specific enthalpy entering the volume [J/kg].
    total_enthalpy_out : State, optional
        Total specific enthalpy leaving the volume [J/kg]. If omitted, enthalpy
        is used.
    heat_rate : State or float, optional
        Net heat rate into the volume [W]. Positive values add energy.
    temperature : State, optional
        Fluid temperature in the volume [K].
    density : State, optional
        Fluid density in the volume [kg/m^3].
    internal_energy : State, optional
        Fluid specific internal energy in the volume [J/kg].
    mass_flow_in : State, optional
        Total mass flow rate entering the volume [kg/s].
    mass_flow_out : State, optional
        Total mass flow rate leaving the volume [kg/s].

    Iteration Variables
    -------------------
    pressure : State
        Internal volume pressure.
    enthalpy : State
        Internal volume specific enthalpy.

    Residuals
    ---------
    mass_balance : float
        Enforces steady-state mass conservation.

        Equation:
            mass_flow_in - mass_flow_out = 0

    energy_balance : float
        Enforces steady-state flow energy conservation.

        Equation:
            mass_flow_in * total_enthalpy_in
            - mass_flow_out * total_enthalpy_out
            + heat_rate = 0

        If total_enthalpy_out is not assigned, the volume enthalpy is used as
        the outlet total enthalpy. If heat_rate is not assigned, it is treated
        as zero.
    """

    def __init__(
        self,
        name: str,
        network: Network,
        pressure: State,
        enthalpy: State,
        volume: float,
        total_enthalpy_in: State,
        total_enthalpy_out: State | None = None,
        heat_rate: State | float | None = None,
        temperature: State | None = None,
        density: State | None = None,
        internal_energy: State | None = None,
        mass_flow_in: State | None = None,
        mass_flow_out: State | None = None,
    ):
        self.setup()

    @property
    def iteration_variables(self) -> list[State]:
        return [self.pressure, self.enthalpy]

    @property
    def residuals(self) -> list[float]:
        qdot = self.heat_rate.value if self.heat_rate.is_assigned else 0.0

        h_out = (
            self.total_enthalpy_out.value
            if self.total_enthalpy_out.is_assigned
            else self.enthalpy.value
        )

        return [
            self.mass_flow_in.value - self.mass_flow_out.value,
            (
                self.mass_flow_in.value * self.total_enthalpy_in.value
                - self.mass_flow_out.value * h_out
                + qdot
            ),
        ]