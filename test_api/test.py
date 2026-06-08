class Component:
    pass


class Network:
    pass


class State:
    pass


class Boundary(Component):
    """
    Fixed pressure and temperature boundary condition.

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