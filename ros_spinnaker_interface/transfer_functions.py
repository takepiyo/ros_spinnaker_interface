#!/usr/bin/env python
# -*- coding: utf-8 -*-


"""
The transfer functions (actually classes) define simple transformations, from incoming ROS values to the injected
live spikes or from observed spikes in ROS live output.

The base classes do all the work, so all you do here is inherit from them and define their behaviour
via the following functions.


Spike Source:

    The spike source must inherit from BasicSpikeSource.
    The behaviour of a spike source is defined by just one function:

    on_update:

        This function is called every time when a neuron needs a new inter spike interval.
        Basically every time a neuron has spiked, it asks when to spike next.

        Args:
            ros_value (usually int): The value of the last ros message. The type depends on the ros message type used.

            neuron (int): The ID of the neuron asking when to spike next.

            n_neurons (int): The total number of neurons of the spike source.

        Returns (int):
            The next inter spike interval in ms.


Spike Sink:

    The spike sink must inherit from BasicSpikeSink.
    The behaviour of the Spike Sink is defined by two different functions and one static variable:

    on_update_calling_rate (int): This static variable defines the rate in which on_update is called.
        For example a value of 10 means on_update is called every 10 ms.
        Defaults to 1 (on_update is called every 1 ms).

    on_update:
        This function is called periodically and can be used for periodic changes of the ROS output value.
        The calling rate can be set explicitly (see above).

        Args:
            neurons (list): list of neurons. A neuron has the following data structure:
                neuron.spike_times (list): list of times when the neuron had spiked:
                    spike_time (int): Number of ms since start of the spinnaker simulation:
                        Example: 5819 -> spike occured after 5819 ms
                neuron.key (int): The key (=ID) of the neuron. 0 <= key <= n_neurons

            sim_time (int): Current Time. Number of ms since start of the simulation.

            curr_ros_value (usually int): The current ROS value being published. Use it if you want to calculate
                the new ros value in dependency of the current one.

        Returns (int):
            The new ROS value. Again the default type is int, because the default ROS message type used is Int64.

    on_spike:
        This function is called every time a spike occurs in the output population. Use it for event-based changes
        of the ROS output value.

        Args:
            spike_time (int): The time of the spike in number of ms since start of the simulation.

            neuron_id (int): The ID (=key) of the neuron that spiked.

            curr_ros_value (usually int): The current ROS value being published. Use it if you want to calculate
                the new ros value in dependency of the current one.


Plotting:
    In both classes you can optionally define a plot function without parameters.
    If you define it, it is called once at the end of the simulation. I stored all the ros values in a list and
    used it to plot the ROS values over time in the end. I found it useful while testing the behaviour.
    Changing the name (for example from plot to _plot, you will see this in here) can be used to disable it again.
    Have a look at the examples.


Notes:
    - The base classes use 1 ms timesteps internally.
    - You should be able to specify a lot of different transfer functions with the methods above.
      However if this does not meet your requirements (you need smaller timesteps, ...), have a look at the
      base classes and simply change their internal logic. It should be pretty straight forward, since the
      technical part is in the ros_spinnaker_interface.py.

"""


from ast import Num
import random
import numpy as np
from .population import (
    BasicSpikeSink,
    BasicSpikeSource,
    BasicSpikeSinkMulti,
)


class SpikeSourceConstantRate(BasicSpikeSource):
    """
    Make all neurons spike with the specified rate.

    Returns the next inter spike interval in ms.
    """

    def on_update(self, ros_value, neuron, n_neurons):
        if ros_value is None or ros_value <= 0:
            return None

        rate = ros_value
        return rate


class SpikeSourcePoisson(BasicSpikeSource):
    """
    Generate a Poisson Spike Train for each neuron, with the ros input being the lambda.

    More Information why this results in a poisson spike train at
    http://www.cns.nyu.edu/~david/handouts/poisson.pdf, Chapter: Generating Poisson Spike Trains
    """
    intervals = []

    def on_update(self, ros_value, neuron, n_neurons):
        # random.seed(10)

        if ros_value is None or ros_value <= 0:
            return None

        lambd = ros_value
        interval = int(random.expovariate(1.0 / lambd))
        self.intervals.append((interval, neuron))
        return interval

    def _plot(self):
        import matplotlib.pyplot as plt
        data = [x for x, neuron in self.intervals if neuron == 1]
        binwidth = 10
        plt.hist(data, bins=range(min(data), max(data) + binwidth, binwidth))
        plt.title('Interspike Intervals Over Time Of Neuron 1')
        plt.show()


class SpikeSourceNumNeurons(BasicSpikeSource):
    """
    Make a certain number of neurons spike with a fixed rate.
    """

    def on_update(self, ros_value, neuron, n_neurons):
        number_neurons, rate = (ros_value, 1000) if ros_value is not None else (0, None)
        interval = rate if 0 < neuron + 1 <= number_neurons else None
        return interval


class SpikeSinkSpikesPerWindow(BasicSpikeSink):
    """
    Return the number of spikes in the last x ms.
    """

    def on_spike(self, spike_time, neuron_id, curr_ros_value):
        pass

    def on_update(self, neurons, sim_time, curr_ros_value):
        time_window = 100  # ms

        num_spikes_per_neuron = 0
        for neuron in neurons:
            num_spikes_per_neuron += sum(
                sim_time - time_window < spike_time for spike_time in neuron.spike_times
            )

        # print('\t[SPIKE]\tReceived {} spikes in the last {} ms'.format(num_spikes_per_neuron, time_window))
        return num_spikes_per_neuron


class SpikeSinkSmoothing(BasicSpikeSink):
    """
    Each incoming spike adds a fixed amount to the output value.
    Every 10 ms the output value is multiplied by 0.95.
    """

    on_update_calling_rate = 10  # ms, defaults to 1 if undefined
    ros_values = []

    def on_spike(self, spike_time, neuron_id, curr_ros_value):
        new_ros_value = curr_ros_value + 1
        self.ros_values.append(new_ros_value)
        return new_ros_value

    def on_update(self, neurons, sim_time, curr_ros_value):
        new_ros_value = curr_ros_value * 0.95
        self.ros_values.append(new_ros_value)
        return new_ros_value

    def _plot(self):
        import matplotlib.pyplot as plt

        plt.plot(self.ros_values)
        plt.title("ROS Values Over Time")
        plt.show()


class SpikeSinkSmoothingMulti(BasicSpikeSinkMulti):
    """
    Each incoming spike adds a fixed amount to the output value.
    Every 10 ms the output value is multiplied by 0.95.
    """

    on_update_calling_rate = 10  # ms, defaults to 1 if undefined

    def on_spike(self, spike_time, neuron_id, curr_ros_value):
        new_ros_value = curr_ros_value.copy()
        new_ros_value[neuron_id] = curr_ros_value[neuron_id] + 1
        # self.ros_values.append(new_ros_value)
        return new_ros_value

    def on_update(self, neurons, sim_time, curr_ros_value):
        new_ros_value = [val * 0.95 for val in curr_ros_value]
        # self.ros_values.append(new_ros_value)
        return new_ros_value

    def plot(self):
        import matplotlib.pyplot as plt
        import numpy as np

        fig, ax = plt.subplots()
        val = np.array(self.ros_values).T
        for i in range(self._n_neurons):
            ax.plot(val[i, :])
        # ax.title('ROS Values Over Time')
        fig.savefig("reports/ros_values.png")


class SpikeSinkConvolution(BasicSpikeSink):
    """
    Each spikes creates a spike response, which quickly increases and then slowly decreases.
    Convolution / Summation of these functions produce a smoothed output value.

    The function chosen for the spike response here is f(x) = 0.1*x*exp(2-x)
    """

    on_update_calling_rate = 10  # ms, defaults to 1 if undefined

    spike_response = [i * np.exp(2 - i) for i in np.arange(0, 6, 0.1)]
    output = [1 for i in range(len(spike_response))]
    ros_values = []

    def on_spike(self, spike_time, neuron_id, curr_ros_value):
        self.output = np.convolve(self.output, self.spike_response, "same")

    def on_update(self, neurons, sim_time, curr_ros_value):
        new_ros_value, self.output = self.output[0], np.append(
            self.output[1:], 1
        )  # FIFO
        self.ros_values.append(new_ros_value)
        return new_ros_value

    def plot(self):
        import matplotlib.pyplot as plt

        plt.figure(1)

        plt.subplot(211)
        plt.plot(self.spike_response)
        plt.title("Spike Response")

        plt.subplot(212)
        plt.plot(self.ros_values)
        plt.title("ROS Values Over Time")

        plt.show()


class SpikeSinkConvolutionMultipleChannels(BasicSpikeSink):
    """
    Each spikes creates a spike response, which quickly increases and then slowly decreases.
    Convolution / Summation of these functions produce a smoothed output value.

    The function chosen for the spike response here is f(x) = x*exp(2-x)

    This class is the same as the SpikeSinkConvolution, but uses one output channel per neuron.
    But there is still just one ros output, so the channels are combined to one output (Summation? Convolution?).

    TODO complete
    """

    on_update_calling_rate = 10  # ms, defaults to 1 if undefined

    spike_response = [i * np.exp(2 - i) for i in np.arange(0, 6, 0.1)]
    output_ = [1 for _ in range(len(spike_response))]
    output = []
    for _ in range(10):
        output.append(output_)
    # output = [[1 for i in range(len(spike_response))] for n in range(10)]  # TODO get n_neurons dynamically #"souje_response is not difined error is occured?"
    ros_values = []

    def on_spike(self, spike_time, neuron_id, curr_ros_value):
        self.output[neuron_id] = np.convolve(self.output, self.spike_response, "same")

    def on_update(self, neurons, sim_time, curr_ros_value):
        values = []
        for neuron in neurons:
            v, self.output[neuron.key] = self.output[neuron.key][0], np.append(
                self.output[neuron.key][1:], 1
            )  # FIFO
            values.append(v)
        new_ros_value = sum(values)
        self.ros_values.append(new_ros_value)
        return new_ros_value


if __name__ == "__main__":
    pass
