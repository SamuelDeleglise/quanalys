"""
This is the general tests that verify the front-end implementation.
So there is not tests on internal logic of the code. It's just a
verification of the api. So as soon as saving and opening works,
everything is good.
"""

import os
import shutil
from typing import Union

import unittest
import numpy as np

from labmate.acquisition import AcquisitionLoop, AcquisitionManager
from labmate.syncdata import SyncData

TEST_DIR = os.path.dirname(__file__)
DATA_DIR = os.path.join(TEST_DIR, "tmp_test_data")


class AcquisitionLoopTest(unittest.TestCase):
    """Test of saving simple data."""

    @staticmethod
    def get_some_data(freq, points):
        x = np.linspace(0, 10*np.pi, points)
        y = np.sin(freq*2*np.pi*x)
        return x, y

    # @classmethod
    def setUp(self) -> None:
        """This setUp method runs ones of LoopTest.
        It creates a dictionary to verify with."""
        self.name = "LoopTest"
        self.aqm = AcquisitionManager(DATA_DIR, save_on_edit=True)
        self.aqm.new_acquisition(self.name)

        self.points = 101
        self.freqs = np.linspace(0, 0.4, 10)
        self.freqs2 = np.linspace(0, 0.4, 20)
        self.freqs3 = np.linspace(0, 1, 5)
        self.data = {}

        # return super().setUpClass()

    def test_dir_was_created(self):
        self.assertTrue(os.path.exists(
            os.path.join(DATA_DIR, self.name)
        ))

    def test_classical_loop(self):
        """Save and load the simplest list.

        Protocol:

        for freq in freqs:
            x, y = ...
            push_to_save(y, freq)
        push_to_save(x)
        save()

        """
        # Protocol
        self.aqm.aq.loop = loop = AcquisitionLoop()
        self.data = {"freq": [], "y": [], "x": []}

        for freq in loop.iter(self.freqs):
            x, y = self.get_some_data(freq, self.points)
            loop.append(y=y, freq=freq)

            self.data['y'].append(y)
            self.data['freq'].append(freq)

        self.data['x'].append(x)  # type: ignore
        loop.append(x=x)  # type: ignore

        # Verification
        self.data_verification()

    def test_classical_loop_call(self):
        """Save and load the simplest list.
        """
        # Protocol
        self.aqm.aq.loop = loop = AcquisitionLoop()
        self.data = {"freq": [], "y": [], "x": []}

        for freq in loop(10):
            x, y = self.get_some_data(freq, self.points)
            loop(y=y, freq=freq)

            self.data['y'].append(y)
            self.data['freq'].append(freq)

        self.data['x'].append(x)  # type: ignore
        loop(x=x)  # type: ignore

        # Verification
        self.data_verification()

    def test_classical_loop_range(self):
        """Save and load the simplest list.
        """
        # Protocol
        self.aqm.aq.loop = loop = AcquisitionLoop()
        self.data = {"freq": []}

        for freq in loop(1, 10, .5):
            loop(freq=freq)
            self.data['freq'].append(freq)

        # Verification
        self.data_verification()

    def test_classical_loop_iterator(self):
        """Save and load the simplest list.
        """
        def iterator():
            for i in range(10):
                yield i
        # Protocol
        self.aqm.aq.loop = loop = AcquisitionLoop()
        self.data = {"freq": []}

        for freq in loop(iterator()):
            loop(freq=freq)
            self.data['freq'].append(freq)

        # Verification
        self.data_verification()

    def test_classical_loop_call_nothing(self):
        """ Raise an exception when no args given to loop"""
        self.aqm.aq.loop = loop = AcquisitionLoop()
        with self.assertRaises(ValueError):
            loop(iterable=None)

        with self.assertRaises(ValueError):
            loop()

    def test_1level_2loop(self):

        self.aqm.aq.loop = loop = AcquisitionLoop()
        self.data = {"freq": [], "y": [], "x": []}

        # Protocol
        for freq in loop.iter(self.freqs):
            x, y = self.get_some_data(freq, self.points)
            loop.append(y=y, freq=freq)

            self.data['y'].append(y)
            self.data['freq'].append(freq)

        for freq in loop.iter(self.freqs):
            x, y = self.get_some_data(freq, self.points)
            loop.append(y=y, freq=freq)

            self.data['y'].append(y)
            self.data['freq'].append(freq)

        self.data['x'].append(x)  # type: ignore
        loop.append(x=x)  # type: ignore

        # Verification
        self.data_verification()

    def test_2level_1loop(self):

        self.aqm.aq.loop = loop = AcquisitionLoop()
        self.data = {"freq": [], "y": [], "x": [], 'y2': [], 'freq2': []}

        # Protocol
        for freq in loop.iter(self.freqs):
            x, y = self.get_some_data(freq, self.points)
            self.data['y2'].append([])
            self.data['freq2'].append([])
            for freq2 in loop.iter(self.freqs2):
                x, y2 = self.get_some_data(freq2, self.points)
                loop.append(y2=y2, freq2=freq2)
                self.data['y2'][-1].append(y2)
                self.data['freq2'][-1].append(freq2)
            loop.append(y=y, freq=freq)
            self.data['y'].append(y)
            self.data['freq'].append(freq)

        self.data['x'].append(x)  # type: ignore
        loop.append(x=x)  # type: ignore

        # Verification
        self.data_verification()

    def test_2level_2loop(self):

        self.aqm.aq.loop = loop = AcquisitionLoop()
        self.data = {"freq": [], "y": [], "x": [], 'y2': [], 'freq2': []}

        # Protocol
        for freq in loop.iter(self.freqs):
            x, y = self.get_some_data(freq, self.points)

            self.data['y2'].append([])
            self.data['freq2'].append([])

            for freq2 in loop.iter(self.freqs2):
                x, y2 = self.get_some_data(freq2, self.points)
                loop.append(y2=y2, freq2=freq2)
                self.data['y2'][-1].append(y2)
                self.data['freq2'][-1].append(freq2)

            for freq2 in loop.iter(self.freqs2):
                x, y2 = self.get_some_data(freq2, self.points)
                loop.append(y2=y2, freq2=freq2)
                self.data['y2'][-1].append(y2)
                self.data['freq2'][-1].append(freq2)

            loop.append(y=y, freq=freq)
            self.data['y'].append(y)
            self.data['freq'].append(freq)

        self.data['x'].append(x)  # type: ignore
        loop.append(x=x)  # type: ignore

        # Verification
        self.data_verification()

    def data_verification(self):
        loop_freq = SyncData(self.aqm.current_filepath).get("loop")
        assert loop_freq is not None, "Cannot get LoopData from saved data."

        for key, value in self.data.items():
            self.assertAlmostEqual(
                compare_np_array(np.array(value), loop_freq.get(key)), 0)

    @classmethod
    def tearDownClass(cls):
        """Remove tmp_test_data directory ones all test finished."""
        # data_directory = os.path.join(os.path.dirname(__file__), DATA_DIR)
        if os.path.exists(DATA_DIR):
            shutil.rmtree(DATA_DIR)
        return super().tearDownClass()


def compare_np_array(array1: Union[list, np.ndarray],
                     array2: Union[list, np.ndarray]):
    return np.abs(np.array(array1) - np.array(array2)).sum()  # type: ignore


class AcquisitionLoopWithoutSaveOnEditTest(AcquisitionLoopTest):
    def setUp(self) -> None:
        """This setUp method runs ones of LoopTest.
        It creates a dictionary to verify with."""
        super().setUp()
        self.aqm = AcquisitionManager(DATA_DIR, save_on_edit=False)
        self.aqm.new_acquisition(self.name)

    def data_verification(self):
        # print(self.aqm.aq.loop._save_on_edit)
        self.aqm.aq.save()
        super().data_verification()


if __name__ == '__main__':
    unittest.main()