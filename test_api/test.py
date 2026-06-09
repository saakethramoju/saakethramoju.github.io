import numpy as np

class Component:
    pass


class Network:
    pass


class State:
    pass

class Composition: pass


class FlowSplitter(Component):
    """
    One-inlet, two-outlet flow splitter with optional energy and species conservation.

    `FlowSplitter` divides a single incoming stream into two outlet streams while
    enforcing steady-state mass conservation. Optional energy conservation may be
    solved, and optional species conservation can be used to determine the
    composition of the second outlet stream.

    When species conservation is enabled, the composition of outlet 1 is treated
    as known and the composition of outlet 2 is calculated from species mass
    balances.

    Residuals
    ---------
    mass_balance : float
        Enforces steady-state mass conservation.

        ``mass_flow_in
        - mass_flow_out1
        - mass_flow_out2 = 0``

    energy_balance : float, optional
        Enforces steady-state flow energy conservation.

        ``mass_flow_in * total_enthalpy_in
        - mass_flow_out1 * total_enthalpy_out1
        - mass_flow_out2 * total_enthalpy_out2
        + heat_rate = 0``

        Included only when energy solving is enabled.

    Iteration Variables
    -------------------
    pressure : State
        Splitter pressure

    enthalpy : State, optional
        Splitter specific enthalpy when energy conservation is enabled

    Parameters
    ----------
    name : str
        Component name
    network : Network
        Network that owns this component
    pressure : State
        Splitter pressure
    volume : float
        Splitter control volume
    enthalpy : State, optional
        Splitter specific enthalpy
    temperature : State, optional
        Splitter temperature
    density : State, optional
        Splitter density
    internal_energy : State, optional
        Splitter specific internal energy
    heat_rate : State or float, optional
        Net heat rate into the splitter
    composition : Composition, optional
        Internal splitter composition
    composition_in : Composition, optional
        Inlet composition
    composition_out1 : Composition, optional
        Outlet 1 composition
    composition_out2 : Composition, optional
        Outlet 2 composition
    total_enthalpy_in : State, optional
        Inlet total specific enthalpy
    total_enthalpy_out1 : State, optional
        Outlet 1 total specific enthalpy. If omitted, the splitter enthalpy is used.
    total_enthalpy_out2 : State, optional
        Outlet 2 total specific enthalpy. If omitted, the splitter enthalpy is used.
    mass_flow_in : State, optional
        Inlet mass flow rate
    mass_flow_out1 : State, optional
        Outlet mass flow rate 1
    mass_flow_out2 : State, optional
        Outlet mass flow rate 2

    Notes
    -----
    Species conservation solves only for the composition of outlet 2. The
    composition of outlet 1 must be specified.

    Outlet 2 species composition is evaluated from:

        ``Y_out2 =
        ((mdot_out1 + mdot_out2) * Y_internal
        - mdot_out1 * Y_out1)
        / mdot_out2``

    The relation is applied for each species in the splitter composition.
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
        composition_in: Composition = Composition(),
        composition_out1: Composition = Composition(),
        composition_out2: Composition = Composition(),
        total_enthalpy_in: State | None = None,
        total_enthalpy_out1: State | None = None,
        total_enthalpy_out2: State | None = None,
        mass_flow_in: State | None = None,
        mass_flow_out1: State | None = None,
        mass_flow_out2: State | None = None,
    ):
        self.setup()

        self._solve_energy = (
            self.total_enthalpy_in.is_assigned
            and self.enthalpy.is_assigned
        )

        if self.composition_in.is_assigned:
            self.composition.copy_from(
                self.composition_in,
                copy_values=True,
            )

        self._solve_species = (
            self.composition.is_assigned
            and self.composition_out1.is_assigned
        )

        if self._solve_species:
            extra_species = (
                set(self.composition_out1.species)
                - set(self.composition.species)
            )

            if extra_species:
                raise ValueError(
                    f"{self.name}: composition_out1 contains species not in "
                    f"composition: {extra_species}"
                )

            self.composition_out2.copy_from(
                self.composition,
                copy_values=True,
            )

        elif self.composition.is_assigned:
            self.composition_out1.copy_from(
                self.composition,
                copy_values=True,
            )

            self.composition_out2.copy_from(
                self.composition,
                copy_values=True,
            )

    def evaluate_states(self) -> None:
        if self.composition_in.is_assigned:
            self.composition.copy_from(
                self.composition_in,
                copy_values=True,
            )

        if not self._solve_species:
            if self.composition.is_assigned:
                self.composition_out1.copy_from(
                    self.composition,
                    copy_values=True,
                )
                self.composition_out2.copy_from(
                    self.composition,
                    copy_values=True,
                )
            return

        if (
            not self.mass_flow_out1.is_assigned
            or not self.mass_flow_out2.is_assigned
        ):
            return

        mdot1 = self.mass_flow_out1.value
        mdot2 = self.mass_flow_out2.value

        if abs(mdot2) < 1e-12:
            return

        mdot_total = mdot1 + mdot2

        for species in self.composition.species:
            x_internal = self.composition[species].value
            x_out1 = self.composition_out1[species].value

            self.composition_out2[species].value = (
                mdot_total * x_internal
                - mdot1 * x_out1
            ) / mdot2

        self.composition_out2.validate()

    @property
    def iteration_variables(self) -> list[State]:
        variables = [self.pressure]

        if self._solve_energy:
            variables.append(self.enthalpy)

        return variables

    @property
    def residuals(self) -> list[float]:
        residuals = [
            self.mass_flow_in.value
            - self.mass_flow_out1.value
            - self.mass_flow_out2.value
        ]

        if self._solve_energy:
            qdot = self.heat_rate.value if self.heat_rate.is_assigned else 0.0

            h_out1 = (
                self.total_enthalpy_out1.value
                if self.total_enthalpy_out1.is_assigned
                else self.enthalpy.value
            )

            h_out2 = (
                self.total_enthalpy_out2.value
                if self.total_enthalpy_out2.is_assigned
                else self.enthalpy.value
            )

            residuals.append(
                self.mass_flow_in.value * self.total_enthalpy_in.value
                - self.mass_flow_out1.value * h_out1
                - self.mass_flow_out2.value * h_out2
                + qdot
            )

        return residuals


class DischargeCoefficient(Component):
    """
    Incompressible restriction flow model using a discharge coefficient.

    `DischargeCoefficient` computes mass flow through a restriction from the
    pressure difference, fluid density, discharge coefficient, and flow area. The
    sign of the mass flow follows the sign of the pressure difference, allowing
    reverse flow when downstream pressure exceeds upstream pressure.

    Relations
    ---------
    Restriction mass flow:

    `mass_flow = sign(P1 - P2) * Cd * A * sqrt(2 * rho * abs(P1 - P2))`

    Parameters
    ----------
    name : str
        Component name
    network : Network
        Network that owns this component
    upstream_pressure : State
        Upstream pressure
    downstream_pressure : State
        Downstream pressure
    density : State
        Fluid density
    discharge_coefficient : float
        Discharge coefficient
    cross_sectional_area : float
        Flow area

    Outputs
    -------
    mass_flow : State, optional
        Computed mass flow rate
    """

    def __init__(
        self,
        name: str,
        network: Network,
        upstream_pressure: State,
        downstream_pressure: State,
        density: State,
        discharge_coefficient: float,
        cross_sectional_area: float,
        mass_flow: State | None = None,
    ):
        self.setup()

    def evaluate_states(self) -> None:
        P1 = self.upstream_pressure.value
        P2 = self.downstream_pressure.value
        rho = self.density.value
        Cd = self.discharge_coefficient.value
        A = self.cross_sectional_area.value

        self.mass_flow.value = (
            np.sign(P1 - P2)
            * Cd
            * A
            * np.sqrt(2.0 * rho * np.abs(P1 - P2))
        )



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

    `Volume` represents an internal fluid control volume whose pressure and
    specific enthalpy are solved from continuity and energy balance. It is useful
    for compressible, heated, cooled, or mixed-flow nodes where both pressure and
    thermodynamic state must be solved.

    Residuals
    ---------
    mass_balance : float
        Enforces steady-state mass conservation.

        ``mass_flow_in - mass_flow_out = 0``

    energy_balance : float
        Enforces steady-state flow energy conservation.

        ``mass_flow_in * total_enthalpy_in
        - mass_flow_out * total_enthalpy_out
        + heat_rate = 0``

        If `total_enthalpy_out` is not assigned, the volume enthalpy is used as
        the outlet total enthalpy. If `heat_rate` is not assigned, it is treated
        as zero.

    Iteration Variables
    -------------------
    pressure : State
        Internal volume pressure.
    enthalpy : State
        Internal volume specific enthalpy.

    Parameters
    ----------
    name : str
        Component name.
    network : Network
        Network that owns this component.
    pressure : State
        Internal volume pressure.
    enthalpy : State
        Internal volume specific enthalpy.
    volume : float
        Volume of the control volume.
    total_enthalpy_in : State
        Total specific enthalpy entering the volume.
    total_enthalpy_out : State, optional
        Total specific enthalpy leaving the volume. If omitted, `enthalpy`
        is used.
    heat_rate : State or float, optional
        Net heat rate into the volume. Positive values add energy.
    temperature : State, optional
        Fluid temperature in the volume.
    density : State, optional
        Fluid density in the volume.
    internal_energy : State, optional
        Fluid specific internal energy in the volume.
    mass_flow_in : State, optional
        Total mass flow rate entering the volume.
    mass_flow_out : State, optional
        Total mass flow rate leaving the volume.
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
    


class Bartz(Component):
    """
    Bartz convective heat transfer coefficient correlation for
    compressible flow in rocket thrust chambers and nozzles.

    Correlation
    -----------
        h_g = X * σ * G

        X = (0.026 / D^0.2)
            * (μ0^0.2 * Cp0 / Pr0^0.6)
            * (mdot / A)^0.8

        σ = (ρ_am / ρ)^0.8
            * (μ_am / μ0)^0.2

    Optional geometric correction:

        G = D / rc

    where:

        A = π D² / 4

    Parameters
    ----------
    name : str
        Component name
    network : Network
        Network that owns this component
    mass_flow : State
        Local mass flow rate. The absolute value is used
    hydraulic_diameter : State or float
        Local hydraulic diameter or equivalent nozzle diameter
    chamber_specific_heat_cp : State
        Specific heat capacity evaluated at stagnation conditions
    chamber_prandtl_number : State
        Prandtl number evaluated at stagnation conditions
    chamber_dynamic_viscosity : State
        Dynamic viscosity evaluated at stagnation conditions
    local_freestream_density : State
        Local gas density at the evaluation location
    mean_temperature_density : State
        Gas density evaluated at the arithmetic mean temperature
        `T_am = (T + T_wall) / 2`. T is the local freestream static temperature.
    mean_temperature_dynamic_viscosity : State
        Dynamic viscosity evaluated at the arithmetic mean temperature
        T_am = (T + T_wall) / 2. T is the local freestream static temperature
    throat_converging_radius : float, optional
        Radius of curvature of the throat converging section. When supplied,
        the geometric correction D / rc is applied

    Outputs
    -------
    convection_coefficient : State, optional
        Gas-side convective heat transfer coefficient. If omitted, a new State is created

    Derived Quantities
    ------------------
    Mass flux:

        G_m = mdot / A

    Property correction factor:

        σ = (ρ_am / ρ)^0.8
            * (μ_am / μ0)^0.2

    Base Bartz coefficient:

        X = (0.026 / D^0.2)
            * (μ0^0.2 * Cp0 / Pr0^0.6)
            * G_m^0.8

    Final heat transfer coefficient:

        h_g = X * σ * G

    Assumptions
    -----------
    * Turbulent, high-Reynolds-number compressible flow.
    * Developed for rocket combustion gases.
    * Chamber properties are evaluated at stagnation conditions.
    * Local property variation in the boundary layer is
      represented through the Bartz correction factor σ.
    * Hydraulic diameter is used as the characteristic length scale.
    * The nozzle cross section is circular.
    * Radiation heat transfer is neglected.

    Recommended Use
    ---------------
    * Rocket thrust chambers.
    * Converging-diverging nozzles.
    * Regeneratively cooled rocket engines.
    * Preliminary and system-level thermal analyses.

    Notes
    -----
    This implementation follows the classical Bartz engineering
    correlation using chamber (stagnation) transport properties and
    the mean-temperature correction factor:

        T_am = (T_g + T_w) / 2

    The Bartz correlation is empirical and is most accurate for
    chemically reacting rocket exhaust gases.

    Bartz tends to underpredict when the effects of radiation are
    strong, when there is a lot dissociation/recombination in the
    boundary layer, or when there are significant combustion
    instabilities.

    Bartz tends to overpredict when soot deposition on the walls is
    significant or when the combustion is incomplete.
    """
    def __init__(self, 
                 name: str, 
                 network: Network,
                 mass_flow: State,
                 hydraulic_diameter: State | float,
                 chamber_specific_heat_cp: State,
                 chamber_prandtl_number: State,
                 chamber_dynamic_viscosity: State,
                 local_freestream_density: State,
                 mean_temperature_density: State,
                 mean_temperature_dynamic_viscosity: State,
                 throat_converging_radius: float | None = None,
                 convection_coefficient: State | None = None):
        self.setup()

    def evaluate_states(self):
        mdot = abs(self.mass_flow.value)
        D = self.hydraulic_diameter.value
        Cp0 = self.chamber_specific_heat_cp.value
        Pr0 = self.chamber_prandtl_number.value
        mu0 = self.chamber_dynamic_viscosity.value
        rho = self.local_freestream_density.value
        rho_am = self.mean_temperature_density.value
        mu_am = self.mean_temperature_dynamic_viscosity.value
        A = (np.pi/4) * D**2

        if self.throat_converging_radius.is_assigned:
            rc = self.throat_converging_radius.value

            if rc <= 0.0:
                raise ValueError(
                    f"{self.name}: throat_converging_radius must be greater than zero. Got {rc}."
                )
            
            geometric_correction = D/rc
        else:
            geometric_correction = 1

        if D <= 0.0:
            raise ValueError(
                f"{self.name}: hydraulic_diameter must be greater than zero. Got {D}."
            )
        
        X = (0.026/(D**0.2)) * (mu0**0.2 * Cp0 / Pr0**0.6) * (mdot/A)**0.8
        sigma = (rho_am/rho)**0.8 * (mu_am/mu0)**0.2
        hg = X * sigma * geometric_correction

        self.convection_coefficient.value = hg
