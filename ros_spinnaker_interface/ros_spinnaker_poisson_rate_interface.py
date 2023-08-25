#!/usr/bin/env python
"""
@file 	ROS_Spinnaker_Poisson_Rate_Interface.py
@author Stephan Reith
@date 	13.07.2016

"""

import rospy
import time
import pydoc
from std_msgs.msg import Float32MultiArray

# from std_msgs.msg import Int64
from multiprocessing import Process, Queue, Lock
from itertools import count

import spynnaker8 as p

lock = Lock()


class _ROS_Spinnaker_Poisson_Rate_Interface(object):

    """
    Transform incoming ROS Messages into spikes and inject them into the Spinnaker Board and the other way round.


    Args:

    n_neurons (int):  The number of neurons of the Spike Source.

    transfer_function_send (function handle): A handle to the transfer function used to convert
        the ROS input data into spikes.

    transfer_function_recv (function handle): A handle to the transfer function used to convert
        the live spikes to a ROS value.

    output_population (pynn.Population): The pyNN.Population you want to get the live spikes from.
        Defaults to None, so the live output is disabled.

    ros_topic_send (str): The ROS Topic used for sending into spinnaker.
        Defaults to "to_spinnaker".

    ros_topic_recv (str): The ROS Topic used for sending into ROS.
        Defaults to "from_spinnaker".

    clk_rate (int): The frequency the ROS Node is running with in Hz.
        Defaults to 1000 Hz.

    ros_output_rate (int): The frequency with which ros messages are sent out.
        Defaults to 10 Hz.

    benchmark (bool): Receive a timing output at the end of the simulation.
        Defaults to False.


    Attributes:

    InjectorPopulation: The ExternalDevices.SpikeInjector instance which is used internally.


    Functions:

        is_roscore_running(): True if the ros core is runnig else False.

        activate_live_output_for(pynn.Population): Set the pynn population you want to get the live spikes from.

        add_simulation_start_callback(function): Register the function as callback at simulation start.


    Examples:
        Have a look at the ROS_Spinnaker_Poisson_Rate_Interface_example.py or other example scripts.

    Notes:
        This interface uses the Spinnaker LiveSpikesConnection internally with the local ports
        19999 and 17895 and the spinnaker port 12345. These ports are widely used for live spikes and
        therefore should'nt cause any problems, however you can also simply change them in the constructor if needed.
        For each parallel interface used, these port numbers are increased by one, so the second interface will use
        the local ports 20000 and 17896 and 12346 on spinnaker, etc.

        If you want to change or extend this interface, consider that there is a sub process started by the
        interface itself, as well as a thread controlled by spinnaker. Make sure they terminate and communicate properly.

        Currently only the std_msgs.msg.Int64 type is supported for ROS Messages. If you want to use your own
        ros message types it is possible, but you need to change some code yourself:
            - in the _incoming_ros_package_callback unpack the ros message fields and decide what to do with it.
            - in run_ros_node adjust the Publisher and Subscriber message types and (if needed) the publisher callback.
    """

    _instance_counter = count()

    def __init__(
        self,
        n_neurons=None,
        poisson_population=None,
        ros_topic_poisson_rate="to_spinnaker_poisson",
        clk_rate=1000,
        ros_output_rate=10,
        benchmark=False,
    ):
        # Members
        self.n_neurons = n_neurons if n_neurons is not None else 1
        self._poisson_population = poisson_population
        self.send_poisson_topic = ros_topic_poisson_rate
        self._clk_rate = clk_rate  # in Hz
        self._ros_output_rate = ros_output_rate  # Hz
        self._benchmark = benchmark

        self.interface_id = next(self._instance_counter)
        self.poisson_rate_control_port = 30000 + self.interface_id

        self._queue_ros_poisson_rate = Queue()

        p.external_devices.add_poisson_live_rate_control(
            self._poisson_population,
            database_notify_port_num=self.poisson_rate_control_port
        )

        poisson_control = p.external_devices.SpynnakerPoissonControlConnection(
            poisson_labels=[self._poisson_population.label], local_port=self.poisson_rate_control_port)

        poisson_control.add_start_resume_callback(self._poisson_population.label, self._poisson_rate_control_callback)

    def _poisson_rate_control_callback(self, label, connection):
        pr = Process(target=self._run_ros_node, args=(label, connection))
        pr.daemon = True
        print("Poisson Rate Interface {} started".format(self.interface_id))
        pr.start()

    def _run_ros_node(self, label, connection):
        rospy.init_node(
            "spinnaker_poisson_rate_ros_interface_{}".format(self.interface_id), anonymous=True
        )
        rospy.Subscriber(
            self.send_poisson_topic,
            Float32MultiArray,
            self._incoming_ros_poisson_rate_callback,
        )
        ros_timer = rospy.Rate(self._clk_rate)
        self.interface_start_time = time.time()
        while not rospy.is_shutdown():
            # print("################==========################")
            if not self._queue_ros_poisson_rate.empty():
                ros_msg = self._queue_ros_poisson_rate.get()
                connection.set_rates(
                    label, [(i, ros_msg[i]) for i in range(self.n_neurons)]
                )
            ros_timer.sleep()

    def _incoming_ros_poisson_rate_callback(self, ros_msg):
        """
        Callback for the incoming data. Forwards the data via UDP to the Spinnaker Board.
        """
        self._queue_ros_poisson_rate.put(
            ros_msg.data
        )  # data is the name of the ros std_msgs data field.

    def __str__(self):
        return "ROS-Spinnaker-Interface"

    def __repr__(self):
        return self._spike_injector_population.label


def ROS_Spinnaker_Poisson_Rate_Interface(*args, **kwargs):
    """
    ROS_Spinnaker_Poisson_Rate_Interface is the factory function for the actual _ROS_Spinnaker_Poisson_Rate_Interface.

    Returns the pynn.SpikeInjector population instead of the interface instance,
    so the interface can be used directly for pynn.Projections.

    Help for the actual _ROS_Spinnaker_Poisson_Rate_Interface:

    """
    # try:
    #     interface = _ROS_Spinnaker_Poisson_Rate_Interface(*args, **kwargs)
    #     return interface.InjectorPopulation

    # except TypeError:
    #     print("\nOops the Initialisation went wrong.")
    #     print("Please use help(_ROS_Spinnaker_Poisson_Rate_Interface) and double check the arguments.")
    #     raise
    interface = _ROS_Spinnaker_Poisson_Rate_Interface(*args, **kwargs)
    return interface


ROS_Spinnaker_Poisson_Rate_Interface.__doc__ += pydoc.text.document(
    _ROS_Spinnaker_Poisson_Rate_Interface
)  # append help(_ROS_Spinnaker_Poisson_Rate_Interface)


if __name__ == "__main__":
    pass
