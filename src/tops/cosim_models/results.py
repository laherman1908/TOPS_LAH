# Result class to store the result of the simulation
import matplotlib.pyplot as plt
import numpy as np
from collections import defaultdict
from tops.cosim_models.windturbine import WindTurbine
from tops.dynamic import PowerSystemModel
import os



class Results:
    def __init__(self):
        self.results = defaultdict(list)

    # region Store results
    def store_time(self, t : float):
        self.results["Time"].append(t)

    def store_fmu_results(self, WT : WindTurbine):
        for key, value in WT.fast.vrs.items():
            self.results[f"{WT.name}_{key}"].append(WT.fast.fmu.getReal([value])[0])
        
    def store_pmsm_results(self, WT : WindTurbine):
        self.results[f"{WT.name}_PMSM T_e"].append(WT.pmsm.get_T_e())
        self.results[f"{WT.name}_PMSM T_e_ref"].append(WT.pmsm.torque_ref * WT.pmsm.params["T_r"])
        self.results[f"{WT.name}_PMSM t_e_ref"].append(WT.pmsm.torque_ref)
        self.results[f"{WT.name}_PMSM speed"].append(WT.pmsm.speed)
        self.results[f"{WT.name}_PMSM SPEED"].append(WT.pmsm.SPEED)
        self.results[f"{WT.name}_PMSM p_e"].append(WT.pmsm.get_p_e())
        self.results[f"{WT.name}_PMSM P_e"].append(WT.pmsm.get_P_e())
        self.results[f"{WT.name}_PMSM q_e"].append(WT.pmsm.get_q_e())
        self.results[f"{WT.name}_PMSM Q_e"].append(WT.pmsm.get_Q_e())
        self.results[f"{WT.name}_PMSM i_d"].append(WT.pmsm.i_d)
        self.results[f"{WT.name}_PMSM i_q"].append(WT.pmsm.i_q)
        self.results[f"{WT.name}_PMSM v_d"].append(WT.pmsm.msc.v_d)
        self.results[f"{WT.name}_PMSM v_q"].append(WT.pmsm.msc.v_q)
        self.results[f"{WT.name}_PMSM i_q_ref"].append(WT.pmsm.i_q_ref)
        self.results[f"{WT.name}_PMSM i_d_ref"].append(WT.pmsm.i_d_ref)
        self.results[f"{WT.name}_PMSM v_qII"].append(WT.pmsm.v_qII)
        self.results[f"{WT.name}_PMSM v_dII"].append(WT.pmsm.v_dII)


    def store_msc_results(self, WT : WindTurbine):
        self.results[f"{WT.name}_MSC_v_q"].append(WT.msc.v_q)
        self.results[f"{WT.name}_MSC_v_d"].append(WT.msc.v_d)
        self.results[f"{WT.name}_MSC_v_q_ctrl"].append(WT.msc.pmsm.v_q_ctrl)
        self.results[f"{WT.name}_MSC_v_d_ctrl"].append(WT.msc.pmsm.v_d_ctrl)
        self.results[f"{WT.name}_MSC_i_dc"].append(WT.msc.i_dc())
        self.results[f"{WT.name}_MSC_v_dc"].append(WT.msc.dclink.vdc)
        self.results[f"{WT.name}_MSC_p_e_dc"].append(WT.msc.p_e_dc())
        self.results[f"{WT.name}_MSC_p_e_dq"].append(WT.msc.p_e_dq())

    def store_dclink_results(self, WT : WindTurbine):
        self.results[f"{WT.name}_DC_vdc"].append(WT.dclink.vdc)
        self.results[f"{WT.name}_DC_vdc_ref"].append(WT.dclink.vdc_ref)
        self.results[f"{WT.name}_DC_i_chopper"].append(WT.dclink.i_chopper())
        self.results[f"{WT.name}_DC_p_adjust"].append(WT.dclink.p_adjust())
        self.results[f"{WT.name}_DC_gsc_p_ref"].append(WT.dclink.gsc_p_ref())
        self.results[f"{WT.name}_DC_duty"].append(WT.dclink.duty())


    def store_gsc_results(self, WT : WindTurbine , ps : PowerSystemModel, x, v):
        self.results[f"{WT.name}_GSC_p_e"].append(ps.vsc["GridSideConverter"].p_e(x, v)[WT.index].copy())
        self.results[f"{WT.name}_GSC_q_e"].append(ps.vsc["GridSideConverter"].q_e(x, v)[WT.index].copy())
        self.results[f"{WT.name}_GSC_i_inj"].append(abs(ps.vsc["GridSideConverter"].i_inj(x, v)[WT.index].copy()))
        self.results[f"{WT.name}_GSC_p_ref_grid"].append(ps.vsc["GridSideConverter"].par["p_ref_grid"][WT.index].copy())
        self.results[f"{WT.name}_GSC_q_ref_grid"].append(ps.vsc["GridSideConverter"].par["q_ref_grid"][WT.index].copy())



    def store_generator_results(self, ps : PowerSystemModel, x, v, index = None):
        if index is not None:
            self.results[f"Generator_{index}_speed"].append(ps.gen['GEN'].speed(x, v)[index].copy())
            self.results[f"Generator_{index}_i_inj"].append(abs(ps.gen['GEN'].i(x, v)[index].copy()))
            self.results[f"Generator_{index}_p_e"].append(ps.gen['GEN'].p_e(x, v)[index].copy())

        else:
            self.results["Generators_speed"].append(ps.gen['GEN'].speed(x, v).copy())
            self.results["Generators_i_inj"].append(abs(ps.gen['GEN'].i(x, v).copy()))
            self.results["Generators_p_e"].append(ps.gen['GEN'].p_e(x, v).copy())


    # endregion


    # region Plot PMSM

    def plot_pmsm_overview(self, sim_name : str, WT : WindTurbine):
        fig, axs = plt.subplots(3, 2, figsize=(15, 10), sharex=True)

        # First column, first row: PMSM p_e and q_e
        axs[0, 0].plot(self.results['Time'], self.results[f'{WT.name}_PMSM p_e'], label='p_e')
        axs[0, 0].plot(self.results['Time'], self.results[f'{WT.name}_PMSM q_e'], label='q_e')
        axs[0, 0].set_ylabel('Power (pu)')
        axs[0, 0].legend()
        axs[0, 0].grid(True)
        axs[0, 0].set_title('PMSM Electrical Power')

        # First column, second row: PMSM currents
        axs[1, 0].plot(self.results['Time'], self.results[f'{WT.name}_PMSM i_d'], label='i_d')
        axs[1, 0].plot(self.results['Time'], self.results[f'{WT.name}_PMSM i_q'], label='i_q')
        axs[1, 0].set_ylabel('Current (pu)')
        axs[1, 0].legend()
        axs[1, 0].grid(True)
        axs[1, 0].set_title('PMSM Currents')

        # First column, third row: PMSM voltages
        axs[2, 0].plot(self.results['Time'], self.results[f'{WT.name}_PMSM v_d'], label='v_d')
        axs[2, 0].plot(self.results['Time'], self.results[f'{WT.name}_PMSM v_q'], label='v_q')
        axs[2, 0].set_ylabel('Voltage (pu)')
        axs[2, 0].legend()
        axs[2, 0].grid(True)
        axs[2, 0].set_title('PMSM Voltages')

        # Second column, first row: PMSM T_e and T_e_ref
        axs[0, 1].plot(self.results['Time'], self.results[f'{WT.name}_PMSM T_e'], label='T_e')
        axs[0, 1].plot(self.results['Time'], self.results[f'{WT.name}_PMSM T_e_ref'], label='T_e_ref')
        axs[0, 1].set_ylabel('Torque (Nm)')
        axs[0, 1].legend()
        axs[0, 1].grid(True)
        axs[0, 1].set_title('PMSM Torque')

        # Second column, second row: GenSpeed and PMSM speed
        axs[1, 1].plot(self.results['Time'], self.results[f'{WT.name}_GenSpeed'], label='GenSpeed')
        axs[1, 1].plot(self.results['Time'], self.results[f'{WT.name}_PMSM SPEED'], label='PMSM SPEED')
        axs[1, 1].set_ylabel('Speed (rpm)')
        axs[1, 1].legend()
        axs[1, 1].grid(True)
        axs[1, 1].set_title('Generator and PMSM Speed')

        # Second column, third row: Difference between HSShftTq and GenTq
        diff = np.array(self.results[f'{WT.name}_HSShftTq']) - np.array(self.results[f'{WT.name}_GenTq'])
        axs[2, 1].plot(self.results['Time'], diff, label='HSShftTq - GenTq')
        axs[2, 1].set_ylabel('Torque Difference (Nm)')
        axs[2, 1].legend()
        axs[2, 1].grid(True)
        axs[2, 1].set_title('Torque Difference')

        # Set the common xlabel and adjust spacing
        fig.text(0.5, 0.04, 'Time (s)', ha='center')
        plt.tight_layout(rect=[0, 0.05, 1, 1])  # Adjust bottom margin
        # plt.savefig(f"Figures/co_sim/PMSM_Overview_{sim_name}.png")

        # Create directory if it does not exist
        output_dir = f"Figures/co_sim/{sim_name}"
        if not os.path.exists(output_dir):
            os.makedirs(output_dir)
        plt.savefig(f"{output_dir}/PMSM_Overview_{sim_name}.png")
    
    # endregion

    # region plot FMU

    def plot_fmu_overview(self, sim_name : str, WT : WindTurbine):
        fig, axs = plt.subplots(3, 2, figsize=(15, 10), sharex=True)

        # First column, first row: HSShftTq
        axs[0, 0].plot(self.results['Time'], self.results[f'{WT.name}_HSShftTq'], label='HSShftTq')
        axs[0, 0].set_ylabel('Torque (Nm)')
        axs[0, 0].legend()
        axs[0, 0].grid(True)
        axs[0, 0].set_title('High Speed Shaft Torque')

        # First column, second row: GenTq and GenSpdOrTrq
        axs[1, 0].plot(self.results['Time'], self.results[f'{WT.name}_GenTq'], label='GenTq')
        axs[1, 0].plot(self.results['Time'], self.results[f'{WT.name}_GenSpdOrTrq'], label='GenSpdOrTrq')
        axs[1, 0].set_ylabel('Torque (Nm)')
        axs[1, 0].legend()
        axs[1, 0].grid(True)
        axs[1, 0].set_title('Generator Torque')

        # First column, third row: Speeds
        axs[2, 0].plot(self.results['Time'], self.results[f'{WT.name}_GenSpeed'], label='GenSpeed')
        axs[2, 0].plot(self.results['Time'], self.results[f'{WT.name}_RefGenSpd'], label='RefGenSpd')
        axs[2, 0].plot(self.results['Time'], self.results[f'{WT.name}_RotSpeed'], label='RotSpeed')
        axs[2, 0].set_ylabel('Speed (rpm)')
        axs[2, 0].legend()
        axs[2, 0].grid(True)
        axs[2, 0].set_title('Generator Speed')

        # Second column, first row: Windspeed
        axs[0, 1].plot(self.results['Time'], self.results[f'{WT.name}_Wind1VelX'], label='Wind1VelX')
        axs[0, 1].plot(self.results['Time'], self.results[f'{WT.name}_RtVAvgxh'], label='RtVAvgxh')
        axs[0, 1].set_ylabel('Wind speed [m/s]')
        axs[0, 1].legend()
        axs[0, 1].grid(True)
        axs[0, 1].set_title('Wind speeds')

        # Second column, third row: Blade pitch
        axs[2, 1].plot(self.results['Time'], self.results[f'{WT.name}_BldPitch1'], label='BldPitch1')
        axs[2, 1].set_ylabel('Pitch (deg)')
        axs[2, 1].legend()
        axs[2, 1].grid(True)
        axs[2, 1].set_title('Blade pitch')

        # Second column, second row: GenPwr and ElecPwrCom
        axs[1, 1].plot(self.results['Time'], self.results[f'{WT.name}_GenPwr'], label='GenPwr')
        axs[1, 1].plot(self.results['Time'], self.results[f'{WT.name}_ElecPwrCom'], label='ElecPwrCom')
        axs[1, 1].set_ylabel('Power (W)')
        axs[1, 1].legend()
        axs[1, 1].grid(True)
        axs[1, 1].set_title('Generator and Electrical Power')

        # Set the common xlabel and adjust spacing
        fig.text(0.5, 0.04, 'Time (s)', ha='center')
        plt.tight_layout(rect=[0, 0.05, 1, 1])  # Adjust bottom margin
        
        # Create directory if it does not exist
        output_dir = f"Figures/co_sim/{sim_name}"
        if not os.path.exists(output_dir):
            os.makedirs(output_dir)
        plt.savefig(f"{output_dir}/FMU_Overview_{sim_name}.png")

    # endregion    
        
    # region plot MSC
    def plot_msc_overview(self, sim_name : str, WT : WindTurbine):
        fig, axs = plt.subplots(3, 2, figsize=(15, 10), sharex=True)

        # First column, first row: MSC v_q, v_d, v_q_ref, and v_d_ref
        axs[0, 0].plot(self.results['Time'], self.results[f'{WT.name}_MSC_v_q'], label='v_q')
        axs[0, 0].plot(self.results['Time'], self.results[f'{WT.name}_MSC_v_d'], label='v_d')
        axs[0, 0].plot(self.results['Time'], self.results[f'{WT.name}_MSC_v_q_ctrl'], label='v_q_ctrl')
        axs[0, 0].plot(self.results['Time'], self.results[f'{WT.name}_MSC_v_d_ctrl'], label='v_d_ctrl')
        axs[0, 0].set_ylabel('Voltage (pu)')
        axs[0, 0].legend()
        axs[0, 0].grid(True)
        axs[0, 0].set_title('MSC Voltages and References')

        # First column, second row: MSC v_qII and v_dII
        axs[1, 0].plot(self.results['Time'], self.results[f'{WT.name}_PMSM v_qII'], label='v_qII')
        axs[1, 0].plot(self.results['Time'], self.results[f'{WT.name}_PMSM v_dII'], label='v_dII')
        axs[1, 0].set_ylabel('Voltage (pu)')
        axs[1, 0].legend()
        axs[1, 0].grid(True)
        axs[1, 0].set_title('MSC Feedforward Terms')

        # First column, third row: MSC i_dc and v_dc
        axs[2, 0].plot(self.results['Time'], self.results[f'{WT.name}_MSC_i_dc'], label='i_dc')
        axs[2, 0].plot(self.results['Time'], self.results[f'{WT.name}_MSC_v_dc'], label='v_dc')
        axs[2, 0].set_ylabel('Current (pu)')
        axs[2, 0].legend()
        axs[2, 0].grid(True)
        axs[2, 0].set_title('MSC DC Current and Voltage')

        # Second column, first row: MSC p_e_dc and p_e_dq
        axs[0, 1].plot(self.results['Time'], self.results[f'{WT.name}_MSC_p_e_dc'], label='p_e_dc')
        axs[0, 1].plot(self.results['Time'], self.results[f'{WT.name}_MSC_p_e_dq'], label='p_e_dq')
        axs[0, 1].set_ylabel('Power (pu)')
        axs[0, 1].legend()
        axs[0, 1].grid(True)
        axs[0, 1].set_title('MSC Power')

        # Second column, second row: PMSM i_q and i_q_ref
        axs[1, 1].plot(self.results['Time'], self.results[f'{WT.name}_PMSM i_q'], label='i_q')
        axs[1, 1].plot(self.results['Time'], self.results[f'{WT.name}_PMSM i_q_ref'], label='i_q_ref')
        axs[1, 1].set_ylabel('Current (pu)')
        axs[1, 1].legend()
        axs[1, 1].grid(True)
        axs[1, 1].set_title('PMSM q-axis Current')

        # Second column, third row: PMSM i_d and i_d_ref
        axs[2, 1].plot(self.results['Time'], self.results[f'{WT.name}_PMSM i_d'], label='i_d')
        axs[2, 1].plot(self.results['Time'], self.results[f'{WT.name}_PMSM i_d_ref'], label='i_d_ref')
        axs[2, 1].set_ylabel('Current (pu)')
        axs[2, 1].legend()
        axs[2, 1].grid(True)
        axs[2, 1].set_title('PMSM d-axis Current')

        # Set the common xlabel and adjust spacing
        fig.text(0.5, 0.04, 'Time (s)', ha='center')
        plt.tight_layout(rect=[0, 0.05, 1, 1])  # Adjust bottom margin
        
        # Create directory if it does not exist
        output_dir = f"Figures/co_sim/{sim_name}"
        if not os.path.exists(output_dir):
            os.makedirs(output_dir)
        plt.savefig(f"{output_dir}/MSC_Overview_{sim_name}.png")

    # endregion

    # region Plot DC-link
    
    def plot_dclink_overview(self, sim_name : str, WT : WindTurbine):
        fig, axs = plt.subplots(3, 2, figsize=(15, 15), sharex=True)

        # First column, first row: DC-link voltage and reference voltage
        axs[0, 0].plot(self.results['Time'], self.results[f'{WT.name}_DC_vdc'], label='vdc')
        axs[0, 0].plot(self.results['Time'], self.results[f'{WT.name}_DC_vdc_ref'], label='vdc_ref')
        axs[0, 0].set_ylabel('Voltage (pu)')
        axs[0, 0].legend()
        axs[0, 0].grid(True)
        axs[0, 0].set_title('DC-link Voltage and Reference')

        # First column, second row: Chopper current
        axs[1, 0].plot(self.results['Time'], self.results[f'{WT.name}_DC_i_chopper'], label='i_chopper')
        axs[1, 0].set_ylabel('Current (pu)')
        axs[1, 0].legend()
        axs[1, 0].grid(True)
        axs[1, 0].set_title('Chopper Current')

        # First column, third row: Power adjustment
        axs[2, 0].plot(self.results['Time'], self.results[f'{WT.name}_DC_p_adjust'], label='p_adjust')
        axs[2, 0].set_ylabel('Power (pu)')
        axs[2, 0].legend()
        axs[2, 0].grid(True)
        axs[2, 0].set_title('Power Adjustment')

        # Second column, first row: Duty cycle
        axs[0, 1].plot(self.results['Time'], self.results[f'{WT.name}_DC_duty'], label='duty')
        axs[0, 1].set_ylabel('Duty Cycle')
        axs[0, 1].legend()
        axs[0, 1].grid(True)
        axs[0, 1].set_title('Chopper Duty Cycle')

        # Second column, second row: GSC power reference
        axs[1, 1].plot(self.results['Time'], self.results[f'{WT.name}_DC_gsc_p_ref'], label='gsc_p_ref')
        axs[1, 1].set_ylabel('Power (pu)')
        axs[1, 1].legend()
        axs[1, 1].grid(True)
        axs[1, 1].set_title('GSC Power Reference')

        # Second column, third row: DC-link current
        axs[2, 1].plot(self.results['Time'], self.results[f'{WT.name}_MSC_i_dc'], label='i_dc')
        axs[2, 1].set_ylabel('Current (pu)')
        axs[2, 1].legend()
        axs[2, 1].grid(True)
        axs[2, 1].set_title('DC-link Current')

        plt.xlabel('Time (s)')
        plt.tight_layout()

        # Create directory if it does not exist
        output_dir = f"Figures/co_sim/{sim_name}"
        if not os.path.exists(output_dir):
            os.makedirs(output_dir)
        plt.savefig(f"{output_dir}/DClink_Overview_{sim_name}.png")

    # region Plot GSC
    def plot_gsc_overview(self, sim_name : str, WT : WindTurbine):
        fig, axs = plt.subplots(4, 1, figsize=(15, 20), sharex=True)

        # GSC p_e and p_ref_grid
        axs[0].plot(self.results['Time'], self.results[f'{WT.name}_GSC_p_e'], label='p_e')
        axs[0].plot(self.results['Time'], self.results[f'{WT.name}_GSC_p_ref_grid'], label='p_ref_grid')
        axs[0].set_ylabel('Power (pu)')
        axs[0].legend()
        axs[0].grid(True)
        axs[0].set_title('GSC Active Power and Reference')

        # GSC q_e and q_ref_grid
        axs[1].plot(self.results['Time'], self.results[f'{WT.name}_GSC_q_e'], label='q_e')
        axs[1].plot(self.results['Time'], self.results[f'{WT.name}_GSC_q_ref_grid'], label='q_ref_grid')
        axs[1].set_ylabel('Reactive Power (pu)')
        axs[1].legend()
        axs[1].grid(True)
        axs[1].set_title('GSC Reactive Power and Reference')

        # GSC i_inj
        axs[2].plot(self.results['Time'], self.results[f'{WT.name}_GSC_i_inj'], label='i_inj')
        axs[2].set_ylabel('Current (pu)')
        axs[2].legend()
        axs[2].grid(True)
        axs[2].set_title('GSC Current Injection')

        # GSC v_q and v_d
        axs[3].plot(self.results['Time'], self.results[f'{WT.name}_MSC_v_q'], label='v_q')
        axs[3].plot(self.results['Time'], self.results[f'{WT.name}_MSC_v_d'], label='v_d')
        axs[3].set_ylabel('Voltage (pu)')
        axs[3].legend()
        axs[3].grid(True)
        axs[3].set_title('MSC Voltages')

        plt.xlabel('Time (s)')
        plt.tight_layout()

        # Create directory if it does not exist
        output_dir = f"Figures/co_sim/{sim_name}"
        if not os.path.exists(output_dir):
            os.makedirs(output_dir)
        plt.savefig(f"{output_dir}/GSC_Overview_{sim_name}.png")

    # endregion

    # region Plot TOPS

    def plot_tops_overview(self, sim_name : str, WT : WindTurbine):
        fig, axs = plt.subplots(3, 1, figsize=(15, 15), sharex=True)

        # Generator speeds
        axs[0].plot(self.results['Time'], self.results["Generators_speed"], label='Generator speeds')
        axs[0].set_ylabel('Speed (rpm)')
        axs[0].legend()
        axs[0].grid(True)
        axs[0].set_title('Generator speeds')

        # Generator current injections
        axs[1].plot(self.results['Time'], self.results["Generators_p_e"], label='P_e')
        axs[1].set_ylabel('Active power (pu)')
        axs[1].legend()
        axs[1].grid(True)
        axs[1].set_title('Generators p_e injections')

        # WT GSC p_e
        axs[2].plot(self.results['Time'], self.results[f'{WT.name}_GSC_p_e'], label=f'{WT.name} GSC p_e')
        axs[2].set_ylabel('Power (pu)')
        axs[2].legend()
        axs[2].grid(True)
        axs[2].set_title(f'{WT.name} GSC Active Power')


        plt.xlabel('Time (s)')
        plt.tight_layout()

        # Create directory if it does not exist
        output_dir = f"Figures/co_sim/{sim_name}"
        if not os.path.exists(output_dir):
            os.makedirs(output_dir)
        plt.savefig(f"{output_dir}/TOPS_Overview_{sim_name}.png")
    # endregion

  


    # def plot_vsc_overview(self, sim_name : str, WT : WindTurbine):

    #     fig, axs = plt.subplots(3, 1, figsize=(15, 15), sharex=True)

    #     # WT1 DC Link Voltage
    #     axs[0].plot(self.results['Time'], self.results[f'{WT.name}_GSC_vdc'], label='WT1 vdc')
    #     axs[0].plot(self.results['Time'], self.results[f'{WT.name}_GSC_vdc_ref'], label='WT1 vdc_ref')
    #     axs[0].set_ylabel('vdc (pu)')
    #     axs[0].legend()
    #     axs[0].grid(True)
    #     axs[0].set_title('WT1 DC Link Voltage')

    #     # WT1 Active Power Reference
    #     axs[1].plot(self.results['Time'], self.results[f'{WT.name}_GSC_p_ref_gen'], label='WT1 p_ref_gen')
    #     axs[1].plot(self.results['Time'], self.results[f'{WT.name}_GSC_p_e'], label='WT1 p_e')
    #     axs[1].set_ylabel('p_ref (pu)')
    #     axs[1].legend()
    #     axs[1].grid(True)
    #     axs[1].set_title('WT1 Active Power Reference')

    #     # WT1 Active Power Reference Adjustment
    #     axs[2].plot(self.results['Time'], self.results[f'{WT.name}_GSC_p_ref_adj'], label='WT1 p_ref_adj')
    #     axs[2].set_ylabel('p_ref_adj (pu)')
    #     axs[2].legend()
    #     axs[2].grid(True)
    #     axs[2].set_title('WT1 Active Power Reference Adjustment')

    #     plt.xlabel('Time (s)')
    #     plt.tight_layout()
    #     # plt.savefig(f"Figures/co_sim/GSC_Overview_{sim_name}.png")
    #     # plt.show()

    #     # Create directory if it does not exist
    #     output_dir = f"Figures/co_sim/{sim_name}"
    #     if not os.path.exists(output_dir):
    #         os.makedirs(output_dir)
    #     plt.savefig(f"{output_dir}/GSC_Overview_{sim_name}.png")