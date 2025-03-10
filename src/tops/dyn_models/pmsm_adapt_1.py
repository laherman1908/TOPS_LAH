# Setting up a WindTurbine system that contains a PMSM with a MSC connected to a FAST FMU

import numpy as np
from fmpy import read_model_description, extract
from fmpy.fmi2 import FMU2Slave


# region PI Controller class
class PIController_LAH:
    def __init__(self, kp, ti):
        self.kp = kp
        self.ti = ti
        self.integral = 0.0

    def compute(self, error, dt):
        self.integral += error * dt

        # Anti-windup
        if self.integral > 1.5:
            self.integral = 1.5
        if self.integral < -1.5:
            self.integral = -1.5
        
        return self.kp * error + (self.kp/self.ti) * self.integral

# endregion


# region Converter class

class MachineSideConverter:

    def __init__(self, params):

        self.params = params

        self.v_d = self.params["v_d_0"]
        self.v_q = self.params["v_q_0"]

        self.v_d_ref = self.v_d
        self.v_q_ref = self.v_q

        self.T = self.params["T_conv"]
        
    def clamp_value(self, value, limit):
        if value > limit:
            value = limit
        if value < -limit:
            value = -limit
        return value

    def set_reference_voltages(self, v_d_ref, v_q_ref):
        self.v_d_ref = v_d_ref
        self.v_q_ref = v_q_ref

    def update_voltages(self, v_d_ctrl, v_q_ctrl, dt):
        # Apply first-order filter to v_d and v_q
        self.v_d += (1/self.T) * (v_d_ctrl - self.v_d) * dt        # Tsw = 2/3*fsw 
        self.v_q += (1/self.T) * (v_q_ctrl - self.v_q) * dt

        # Limit the voltages
        self.v_d = self.clamp_value(self.v_d, 2)
        self.v_q = self.clamp_value(self.v_q, 2)

    def get_voltages(self):
        self.update_voltages()
        return self.v_d, self.v_q
    
# endregion

# region PMSM class

# Tror jeg kan unngå å bruke DAEModel ettersom at MSC er dekoblet fra det dynamiske nettet, stemmer
class PMSM:

    """
    Internally Permanent Magnet Synchrnous Machine

    """
    
    def __init__(self, pmsm_params : dict):

        """
        # pmsm_params = {
        #     "s_n" : 15e6,     # 15 MW
        #     "w_r" : 0.792*(60/(2*np.pi)),  # Rated speed in rpm
        #     "U_n" : 4770.34,    # Rated phase voltage
        #     "I_n" : 1084.55,    # Nominal phase current
        #     "T_r" : 21.03e3,   # kNm torque        
        #     "rs": 0.03,     # Stator resistance
        #     "x_d": 0.4,     # Stator d-axis inductance
        #     "x_q": 0.4,     # Stator q-axis inductance
        #     "Psi_m": 0.9,   # Magnetic flux
        # }

        # https://www.nrel.gov/docs/fy20osti/75698.pdf

        """
        

        ### Might need to adress an eventuall gearbox ratio
        
        # Assigning the basic parameters of the PMSM
        self.params = pmsm_params
        self.converter = MachineSideConverter(self.params)

        # Initiating some basic initial values of operation, should be updated later based of load flow solution
        self.speed = 0.0
        self.torque_ref = 0.0

        # Initialize PI controllers for i_d, i_q, and speed with parameters adjusted for a larger timestep
        self.pi_controller_id = PIController_LAH(kp=1, ti=0.1)
        self.pi_controller_iq = PIController_LAH(kp=1, ti=0.1)

        # Initiate reference values
        self.i_d_ref = 0.0          # Må kanskje endres senere
        self.i_q_ref = self.torque_ref / self.params["Psi_m"]

        self.i_d = 0.0
        self.i_q = self.i_q_ref

    # region Derivatives

    def derivatives(self):
        """
        V3
        From block diagram electric drives PMSM SIMULINK, currents as state variables

        parmas = {% Electrical
                    r_s   = 0.03; [pu] stator resistance
                    x_s   = 0.4;  [pu] stator inductance
                    x_d   = 0.4;  [pu] stator inductance
                    x_q   = 0.4;  [pu] stator inductance
                    psi_m = 0.66; [pu] magnetic flux 

                    f_n = 50;       [Hz] nominal frequency
                    w_n = 2*pi*f_n; [rad/s] nominal frequency

                    % Mechanical
                    T_m = 0.8; [s] mechanical time constant

        """
        dX = {}
        p = self.params
        psi_q = self.i_q*p["x_q"]
        psi_d = self.i_d*p["x_d"] + p["Psi_m"]

        # Motor convention
        dX["i_d"] = (self.converter.v_d - p["rs"]*self.i_d + psi_q*self.speed) * (p["w_n"]/p["x_d"])
        dX["i_q"] = (self.converter.v_q - p["rs"]*self.i_q - psi_d*self.speed) * (p["w_n"]/p["x_q"])

        # Speed is here exluded from the derivatives, as it is updated from the FAST FMU

        return dX
       
    # endregion
    
    # region Speed controll functions

    def update_torque_control(self, fast : 'FAST', step_size):
        """
        Method to update the reference torque based on the speed error
        Input: dt - time step
        
        Output: self.i_q_ref - updated reference q-axis current
        """
        # fast.fmu: FMU2Slave

        self.torque_ref = fast.fmu.getReal([fast.vrs['GenTq']])[0]/self.params["T_r"]       # Torque reference from FAST FMU in pu

        # Limit torque reference
        self.torque_ref = self.clamp_value(self.torque_ref, max_value=1.5, min_value=0)        

        # Calculate the required i_q_ref to produce the needed torque (algebraic)
        self.i_q_ref = self.torque_ref / self.params["Psi_m"]

    # endregion


    # region Current controll functions
    def update_current_control(self, dt):
        p = self.params

        # Compute errors
        error_id = self.i_d_ref - self.i_d
        error_iq = self.i_q_ref - self.i_q

        ### Decoupling and current control ###
        # Compute decoupled voltage control signals
        v_dII = -self.i_q * p["x_q"] * self.speed
        v_qII = self.i_d * p["x_d"] + p["Psi_m"] * self.speed

        # I_d current control
        v_d_ctrl = v_dII + self.pi_controller_id.compute(error_id, dt)
        v_d_ctrl = self.clamp_value(v_d_ctrl, max_value=2, min_value=-2)
        
        # I_q current control
        v_q_ctrl = v_qII + self.pi_controller_iq.compute(error_iq, dt)
        v_q_ctrl = self.clamp_value(v_q_ctrl, max_value=2, min_value=-2)

        # Input voltage control signal to converter and update the voltages
        self.set_converter_voltages(v_d_ctrl, v_q_ctrl, dt)
    
    # endregion

    def step_pmsm(self, fast : 'FAST', time : float, step_size : float):
        
        # Update states from fast FMU
        self.speed = fast.fmu.getReal([fast.vrs['RotSpeed']])[0] / self.params["w_n"]
        self.SPEED = self.speed * self.params["w_n"]        # Mulig drit kodepraksis menmen     (rpm)

        # Torque control
        self.update_torque_control(fast, step_size)

        # Update reference voltages using PI controllers
        self.update_current_control(step_size)

        # Calculate the derivatives
        dX = self.derivatives()

        # # Update the states using Euler integration
        self.i_d += dX["i_d"] * step_size
        self.i_q += dX["i_q"] * step_size

    def set_converter_voltages(self, v_d_ctrl, v_q_ctrl, dt):
        # self.converter.set_reference_voltages(v_d_ctrl, v_q_ctrl)
        self.converter.v_d_ref = v_d_ctrl
        self.converter.v_q_ref = v_q_ctrl
        self.converter.update_voltages(v_d_ctrl, v_q_ctrl, dt)

    def set_prime_mover_reference(self, speed_ref, torque_ref, ramp_time, current_time, dt):
        self.target_speed_ref = speed_ref
        self.target_torque_ref = torque_ref
        self.ramp_duration = ramp_time / dt
        self.ramp_start_time = current_time

    def set_primemover_ramp_reference_values(self, current_time):
        if self.ramp_duration > 0:
            elapsed_time = current_time - self.ramp_start_time
            if elapsed_time < self.ramp_duration:
                ramp_factor = elapsed_time / self.ramp_duration
                self.primemover.speed_ref = (1 - ramp_factor) * self.primemover.speed_ref + ramp_factor * self.target_speed_ref
                self.primemover.torque_ref = (1 - ramp_factor) * self.primemover.torque_ref + ramp_factor * self.target_torque_ref
            else:
                self.primemover.speed_ref = self.target_speed_ref
                self.primemover.torque_ref = self.target_torque_ref
                self.ramp_duration = 0  # Ramp completed

    # region Utility functions

    def clamp_value(self, value, min_value=None, max_value=None):
        """
        Clamp the value within the specified minimum and maximum limits.

        Parameters:
        value (float): The value to be clamped.
        min_value (float, optional): The minimum limit. Defaults to None.
        max_value (float, optional): The maximum limit. Defaults to None.

        Returns:
        float: The clamped value.
        """
        if min_value is not None and max_value is not None:
            # Clamp value between min_value and max_value
            return max(min_value, min(value, max_value))
        elif min_value is not None:
            # Clamp value to be at least min_value
            return max(min_value, value)
        elif max_value is not None:
            # Clamp value to be at most max_value
            return min(value, max_value)
        else:
            # No clamping needed
            return value


    def get_t_e(self):
        p = self.params
        psi_q = self.i_q*p["x_q"]
        psi_d = self.i_d*p["x_d"] + p["Psi_m"]

        return psi_d*self.i_q - psi_q*self.i_d
    
    def get_T_e(self):
        return self.get_t_e()*self.params["T_r"]

    def get_v_d(self):
        return self.converter.v_d
    
    def get_v_q(self):
        return self.converter.v_q

    def get_speed(self):
        return self.speed
    
    def get_p_e(self):
        return (3/2)*(self.converter.v_d*self.i_d + self.converter.v_q*self.i_q)      # -3/2 fac to adjust to three-phase power and change direction as injection

    def get_P_e(self):
        return self.get_p_e()*self.params["s_n"]

    def get_q_e(self):
        return (3/2)*(self.converter.v_q*self.i_d - self.converter.v_d*self.i_q)      # 3/2 fac?
    
    def get_Q_e(self):
        return self.get_q_e()*self.params["s_n"]

    def get_Pm(self):
        return self.speed * self.primemover.torque

    # endregion

# region FAST

class FAST():
    def __init__(self, params : dict):
        self.params = params
        self.fmu, self.vrs = self.initiate_FAST_FMU(params.get("fast_fmu_filename", "fast.fmu"), params.get("start_time", 0.0), params.get("mode", 3))

    def initiate_FAST_FMU(self, fmu_filename: str, start_time : float, mode : int) ->  FMU2Slave:

        # read the model description
        model_description = read_model_description(fmu_filename, validate=False)    #, validate=False

        # # collect the value references
        vrs = {}
        for variable in model_description.modelVariables:
            vrs[variable.name] = variable.valueReference

        # Print the value references to verify them
        print("Value References: \n")
        for name, vr in vrs.items():
            print(f"Variable: {name}, Value Reference: {vr}")

        # # extract the FMU
        unzipdir = extract(fmu_filename)

        wd_file_path = 'openfast_fmu/resources/wd.txt'
        new_directory = 'C:/Users/larsi/Master/TOPS_LAH/TOPS_LAH'

        # Write the new directory to the wd.txt file
        with open(wd_file_path, 'w') as f:
            f.write(new_directory)

        fmu = FMU2Slave(guid=model_description.guid,
                        unzipDirectory=unzipdir,
                        modelIdentifier=model_description.coSimulation.modelIdentifier,
                        instanceName='instance1')

        fmu.instantiate()
        fmu.setReal([vrs['testNr']], [1002])
        fmu.setReal([vrs['Mode']], [mode])
        fmu.setupExperiment(startTime=start_time)
        fmu.enterInitializationMode()
        fmu.exitInitializationMode()

        return fmu, vrs

    def step_fmu(self, pmsm : PMSM, time : float, step_size : float):
        self.fmu.setReal([self.vrs['GenSpdOrTrq']], [pmsm.get_T_e()])         # Torque input to FAST FMU in actual value
        self.fmu.setReal([self.vrs['GenPwr']], [pmsm.get_P_e()])

        if time < 10:              # Is the power input needed in fmu mode 3?
            self.fmu.setReal([self.vrs['ElecPwrCom']], [20e3])
        else:                    # Is the speed input needed in fmu mode
            self.fmu.setReal([self.vrs['ElecPwrCom']], [10e3])
        
        self.fmu.doStep(currentCommunicationPoint=time, communicationStepSize = step_size)

    def terminate_fmu(self):
        self.fmu.terminate()
        self.fmu.freeInstance()


# endregion