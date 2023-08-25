#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
@author Stephan Reith
@date 	31.08.2016

This is a simple example to demonstrate how the ROS Spinnaker Interface can be used.

You will also need a ROS Listener and a ROS Talker to send and receive data.
Make sure they communicate over the same ROS topics and std_msgs.Int64 ROS Messages used in here.
"""

import spynnaker8 as p

from ros_spinnaker_interface import ROS_Spinnaker_Interface
# import transfer_functions as tf
from ros_spinnaker_interface import SpikeSourcePoisson
from ros_spinnaker_interface import SpikeSinkSmoothing

import pyNN.utility.plotting as plot

ts = 0.1
n_neurons = 1
simulation_time = 10000  # ms


p.setup(timestep=ts, min_delay=ts, max_delay=2.0 * ts)


pop = p.Population(size=n_neurons, cellclass=p.IF_curr_exp, cellparams={}, label='pop')


# The ROS_Spinnaker_Interface just needs to be initialised. The following parameters are possible:
ros_interface = ROS_Spinnaker_Interface(
    n_neurons=n_neurons,                 # number of neurons of the injector population
    Spike_Source_Class=SpikeSourcePoisson,   # the transfer function ROS Input -> Spikes you want to use.
    Spike_Sink_Class=SpikeSinkSmoothing,     # the transfer function Spikes -> ROS Output you want to use.
    # You can choose from the transfer_functions module
    # or write one yourself.
    output_population=pop,                      # the pynn population you wish to receive the
    # live spikes from.
    ros_topic_send='to_spinnaker',              # the ROS topic used for the incoming ROS values.
    ros_topic_recv='from_spinnaker',            # the ROS topic used for the outgoing ROS values.
    clk_rate=1000,                              # mainloop clock (update) rate in Hz.
    ros_output_rate=10)                         # number of ROS messages send out per second.

# Build your network, run the simulation and optionally record the spikes and voltages.
p.Projection(ros_interface, pop, p.OneToOneConnector(), p.StaticSynapse(weight=5, delay=1))

pop.record(["spikes", "v"])
p.run(simulation_time)

neo = pop.get_data(variables=["spikes", "v"])
spikes = neo.segments[0].spiketrains
print(spikes)
v = neo.segments[0].filter(name="v")[0]
print(v)

p.end()
fig = plot.Figure(
    # plot voltage for first ([0]) neuron
    plot.Panel(v, ylabel="Membrane potential (mv)", data_labels=[
               pop.label], yticks=True, xlim=(0, simulation_time)),
    # plot spikes (or in this case spike)
    plot.Panel(spikes, yticks=True, markersize=5, xlim=(0, simulation_time)), title="Simple Example", annotations="Simulated with {}".format(p.name())
)
# plt.show()
fig.save("reports/{}.png".format(__file__).replace(".py", ""))
