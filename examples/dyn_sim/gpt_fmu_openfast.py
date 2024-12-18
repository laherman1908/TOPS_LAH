# GPT FMU aaah nr 2
# hard copy of gptfmu2.py to adjust into OpenFAST FMU

# Custom input - adapted from https://github.com/CATIA-Systems/FMPy/blob/main/fmpy/examples/custom_input.py

""" This example demonstrates how to use the FMU.get*() and FMU.set*() functions
 to set custom input and control the simulation """

from fmpy import read_model_description, extract
from fmpy.fmi2 import FMU2Slave
from fmpy.util import plot_result
import numpy as np
import shutil
import os
import matplotlib.pyplot as plt

def simulate_custom_input(show_plot=True):

    # define the model name and simulation parameters
    fmu_filename = 'C:/Users/larsi/OpenFAST/OpenFASTFMU2PF_Export/fast.fmu'
    

    start_time = 0.0
    stop_time = 5
    step_size = 0.01
    
    # traditional stepsize 0.025


    # read the model description
    model_description = read_model_description(fmu_filename)

    # collect the value references
    vrs = {}
    for variable in model_description.modelVariables:
        vrs[variable.name] = variable.valueReference


    # # Print the value references to verify them
    # for name, vr in vrs.items():
    #     print(f"Variable: {name}, Value Reference: {vr}")

    # Is defined in SIMULINK as getReal(6-19)
    # get the value references for the variables we want to get/set
    generator_power = vrs['GenPwr']  # Replace 'Output1' with the actual variable name
    generator_torque = vrs['GenTq']  # Replace 'Output2' with the actual variable name
    high_speed_shaft = vrs['HSShftV']  # Replace 'Output3' with the actual variable name
    generator_speed = vrs['GenSpeed']


    vrs['testNr'] = 1002
    vrs['timeStart'] = 0.0
    vrs['Mode'] = 1.0
    # vrs['HSShftV'] = 0.0
    # vrs['GenPwr'] = 0.0
    # vrs['ElecPwrCom'] = 0.0


    # Print the value references to verify them
    for name, vr in vrs.items():
        print(f"Variable: {name}, Value Reference: {vr}")


    # extract the FMU
    unzipdir = extract(fmu_filename)

    fmu = FMU2Slave(guid=model_description.guid,
                    unzipDirectory=unzipdir,
                    modelIdentifier=model_description.coSimulation.modelIdentifier,
                    instanceName='instance1')


    # initialize
    fmu.instantiate()
    fmu.setupExperiment(startTime=start_time)
    fmu.enterInitializationMode()
    fmu.exitInitializationMode()

    time = start_time
    rows = []  # list to record the results

    # Simulation loop
    while time < stop_time:
        # Set initial values for the variables
        # fmu.setReal([3],[7.55])
        # fmu.setReal([4],[0.0])
        # fmu.setReal([5],[20_000])

        # Perform one step
        try:
            # print(f"Performing doStep at time {time}")
            fmu.doStep(currentCommunicationPoint=time, communicationStepSize=step_size)
        except Exception as e:
            print(f"Error during doStep at time {time}: {e}")
            break

        # Get the outputs
        try:
            output1 = fmu.getReal([generator_power])[0]
            output2 = fmu.getReal([generator_torque])[0]
            output3 = fmu.getReal([high_speed_shaft])[0]
            output4 = fmu.getReal([generator_speed])[0]
            # print(f"Outputs at time {time}: {output1}, {output2}, {output3}, {output4}")
        except Exception as e:
            print(f"Error getting output at time {time}: {e}")
            break

        # Append the results
        rows.append((time, output1, output2, output3, output4))


        # advance the time
        time += step_size

    # Terminate the FMU
    try:
        fmu.terminate()
    except Exception as e:
        print(f"Error during termination: {e}")

    fmu.freeInstance()

    # clean up
    shutil.rmtree(unzipdir, ignore_errors=True)

    # Convert results to a structured numpy array
    result = np.array(rows, dtype=np.dtype([
        ('time', np.float64),
        ('output1', np.float64),
        ('output2', np.float64),
        ('output3', np.float64),
        ('output4', np.float64)
    ]))

    # Save the results
    np.savetxt('results.csv', result, delimiter= ',', header = 'time, Generator_power, Generator_torque, High_speed_shaft, Generator_speed', comments='')

    if show_plot:
        times = result['time']
        outputs1 = result['output1']
        outputs2 = result['output2']
        outputs3 = result['output3']
        outputs4 = result['output4']
        fig, axs = plt.subplots(4, 1, figsize=(10, 8), sharex=True)
    
        axs[0].plot(times, outputs1, label='Generator_power')
        axs[0].set_ylabel('Generator_power')
        axs[0].legend()
        
        axs[1].plot(times, outputs2, label='Generator_torque')
        axs[1].set_ylabel('Generator_torque')
        axs[1].legend()
        
        axs[2].plot(times, outputs3, label='High_speed_shaft')
        axs[2].set_ylabel('High_speed_shaft')
        axs[2].legend()
        
        axs[3].plot(times, outputs4, label='Generator_speed')
        axs[3].set_xlabel('Time (s)')
        axs[3].set_ylabel('Generator_speed')
        axs[3].legend()
        
        plt.tight_layout()
        plt.show()


if __name__ == '__main__':
    simulate_custom_input(show_plot=True)

