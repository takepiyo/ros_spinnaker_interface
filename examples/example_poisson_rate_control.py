import spynnaker8 as p
from ros_spinnaker_interface import ROS_Spinnaker_Interface
from ros_spinnaker_interface import SpikeSinkSmoothingMulti

from ros_spinnaker_interface import ROS_Spinnaker_Poisson_Rate_Interface
import pyNN.utility.plotting as plot

import time

ts = 1.0
n_neurons = 2
simulation_time = 50 * 1000  # ms

p.setup(timestep=ts, min_delay=ts, max_delay=2.0 * ts)

output_pop = p.Population(size=n_neurons, cellclass=p.IF_curr_exp, cellparams={}, label='output_pop')
poisson_pop = p.Population(size=n_neurons, cellclass=p.SpikeSourcePoisson(rate=0), label='poisson_input')

ros_poisson_interface = ROS_Spinnaker_Poisson_Rate_Interface(
    n_neurons=n_neurons,
    poisson_population=poisson_pop,
)

ros_interface = ROS_Spinnaker_Interface(
    n_neurons=n_neurons,
    Spike_Sink_Class=SpikeSinkSmoothingMulti,
    output_population=output_pop
)

p.Projection(poisson_pop, output_pop, p.OneToOneConnector(), p.StaticSynapse(weight=5, delay=1))

output_pop.record(["spikes"])
poisson_pop.record(["spikes"])

# port = 51234
# p.external_devices.add_poisson_live_rate_control(
#     poisson_pop, database_notify_port_num=port
# )
# poisson_control = p.external_devices.SpynnakerPoissonControlConnection(
#     poisson_labels=[poisson_pop.label], local_port=port)


# def start_callback(label, connection):
#     print("=================simulation start====================")
#     print(f"{label=}")
#     print(f"{connection=}")
#     print(f"{type(connection)=}")
#     for rate in [50, 10, 20]:
#         connection.set_rates(label, [(i, rate) for i in range(n_neurons)])
#         time.sleep(10.0)


# poisson_control.add_start_resume_callback(poisson_pop.label, start_callback)

p.run(simulation_time)

neo = output_pop.get_data(variables=["spikes"])
pop_spikes = neo.segments[0].spiketrains
neo = poisson_pop.get_data(["spikes"])
poisson_pop_spikes = neo.segments[0].spiketrains

p.end()

fig = plot.Figure(
    plot.Panel(pop_spikes, yticks=True, markersize=5, xlim=(0, simulation_time)),
    plot.Panel(poisson_pop_spikes, yticks=True, markersize=5, xlim=(0, simulation_time)), title="Simple Example", annotations="Simulated with {}".format(p.name())
)
# plt.show()
fig.save("reports/{}.png".format(__file__).replace(".py", ""))
