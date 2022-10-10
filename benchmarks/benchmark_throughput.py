# called!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
@author Stephan Reith
@date 	31.08.2016

You will also need a ROS Listener and a ROS Talker to send and receive data.
Make sure they communicate over the same ROS topics and std_msgs.Int64 ROS Messages used in here.
"""


import spynnaker8 as p
import pylab
import numpy as np
from ros_spinnaker_interface import ROS_Spinnaker_Interface
# import transfer_functions as tf
from ros_spinnaker_interface import SpikeSourceConstantRate, SpikeSourcePoisson
from ros_spinnaker_interface import SpikeSinkSmoothing

import pyNN.utility.plotting as plot


ts = 0.1  # ms

tau_m = 0.01  # ms
cm = 10.0  # nF
weight = 10.0  # nA

n_neurons = 1
n_spikes = 1000
n_interfaces = 2
simulation_time = 5000  # ms


nticks = int(simulation_time / ts)

# p.setup(timestep=1.0, min_delay=1.0, max_delay=144.0)
p.setup(timestep=0.1)

cell_params_lif = {'cm': cm,            # nF
                   'i_offset': 0.0,     # nA
                   'tau_m': tau_m,      # ms
                   'tau_refrac': 0.0,   # ms
                   'tau_syn_E': 10.0,   # ms
                   'tau_syn_I': 10.0,   # ms
                   'v_reset': -101.0,   # mV
                   'v_rest': -100.0,    # mV
                   'v_thresh': -1.0     # mV
                   }

ros_interfaces = []
populations = []

for i in range(n_interfaces):
    pop = p.Population(size=n_neurons,
                       cellclass=p.IF_curr_exp,
                       cellparams=cell_params_lif,
                       label='pop{}'.format(i))

    ros_interface = ROS_Spinnaker_Interface(
        n_neurons_source=n_neurons,
        Spike_Source_Class=SpikeSourcePoisson,
        Spike_Sink_Class=SpikeSinkSmoothing,
        output_population=pop,
        ros_topic_send='to_spinnaker',
        ros_topic_recv='from_spinnaker',
        clk_rate=1000,
        ros_output_rate=10,
        benchmark=False)

    p.Projection(ros_interface, pop, p.OneToOneConnector(), p.StaticSynapse(weight=weight, delay=1))

    ros_interfaces.append(ros_interface)
    populations.append(pop)

    pop.record(["spikes", "v"])
    ros_interface.record(["spikes"])


p.run(simulation_time)

neo_list = [pop.get_data(variables=["spikes", "v"]) for pop in populations]
pop_spike_list = [neo.segments[0].spiketrains for neo in neo_list]
pop_volt_list = [neo.segments[0].filter(name="v")[0] for neo in neo_list]

neo_list = [pop.get_data(variables=["spikes"]) for pop in ros_interfaces]
ros_spike_list = [neo.segments[0].spiketrains for neo in neo_list]

p.end()

# Analysis
for i in range(n_interfaces):
    # for i, voltages in enumerate(pop_volt_list):
    # timeline = voltages[:, 1]  # neuron_id, time, voltage
    # membrane_voltage = voltages[:, 2]
    # dVs = pylab.diff(membrane_voltage)

    # print("\nInterface {}".format(i))

    # # time with actual spiking activity
    # spike_times = [timeline[i + 1] for i, dv in enumerate(dVs) if dv > 0]
    # time_first_spike, time_last_spike = spike_times[0], spike_times[-1]
    # active_time = int(time_last_spike - time_first_spike)  # ms
    # # print("First spike occured at {}, last spike at {}".format(time_first_spike, time_last_spike))

    # # mean spike height
    # mean_decrease = np.mean([dv for dv in dVs if dv < 0])
    # dv_mean = np.mean([dv - mean_decrease for dv in dVs if dv > 0])  # mean decrease per timestep needs to be added
    # # because it exists even if there is a spike
    # print("Mean Spike Height: {} mV".format(dv_mean))

    # # expected spike height
    # exp_tc = np.exp(float(-ts) / tau_m)                             # time constant multiplier
    # dv_expected = (tau_m / cm) * weight * (1.0 - exp_tc)            # equation for pulse input
    # print("Expected Spike Height: {} mV".format(dv_expected))

    # # Difference
    # discrepancy = dv_expected - dv_mean
    # print("Discrepancy between mean and expected: {} mV".format(discrepancy))
    # # TODO Open Question: Is the discrepancy small enough and can the above formula be applied?

    # # Use the mean spike height to count the spikes
    # spike_height = dv_mean
    # spike_count = 0
    # spikes = [dv for dv in dVs if dv > 0]

    # for spike in spikes:
    #     spike_count += int(round(spike / spike_height))

    # print("[SPIKE COUNT] {} spikes counted in {} ms.".format(spike_count, active_time))
    # print("({} spikes per ms)".format(spike_count / float(active_time)))

    # print("")

    fig = plot.Figure(
        # plot voltage for first ([0]) neuron
        plot.Panel(pop_volt_list[i], ylabel="POP Membrane potential (mv)", data_labels=[
            pop.label], yticks=True, xlim=(0, simulation_time)),
        # plot spikes (or in this case spike)
        plot.Panel(pop_spike_list[i], yticks=True, markersize=5, xlim=(0, simulation_time)),
        # plot spikes (or in this case spike)
        plot.Panel(ros_spike_list[i], yticks=True, markersize=5, xlim=(0, simulation_time)), title="pop ros", annotations="Simulated with {}".format(p.name())
    )
    # plt.show()
    fig.save("reports/{}_pop_{}.png".format(__file__, i).replace(".py", ""))


# import IPython
# IPython.embed()
