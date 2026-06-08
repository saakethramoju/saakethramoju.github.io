# Components

!!! warning "Documentation TODO"
    This page is a work in progress.

All simulations are comprised of **Components**, which are modular blocks that represent engineering functions like `DischargeCoefficient` or `DarcyWeisbach`. Both of these components are used to calculate mass flow using momentum conservation but use different methodologies. Effectively, these components both represent an incompressible fluid flow through a pipe but are two different engineering methodologies used for different pruposes. `DarcyWeisbach` explicitly calculates frictional losses in the flow while `DischargeCoefficient` uses an empirical/experimental correction factor to account for losses.

Components can represent anything from pipes to pumps to combustion chambers to any mathematical equation you want. For example, if you used a simulation to calculate the pressure in a thin-walled cylindrical pressure vessel, you could define a `HoopStress` component that calculates the circumferential stress in that pressure vessel's wall: