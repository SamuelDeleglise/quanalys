"""
This is the general tests that verify the front-end implementation.
So there is not tests on internal logic of the code. It's just a
verification of the api. So as soon as saving and opening works,
everything is good.
"""

import os
import shutil

import unittest
import numpy as np

from labmate.acquisition import AcquisitionManager, AnalysisData

from labmate.acquisition.acquisition_loop import AcquisitionLoop
from .utils import compare_np_array

TEST_DIR = os.path.dirname(__file__)
DATA_DIR = os.path.join(TEST_DIR, "tmp_test_data")


class BasicTest(unittest.TestCase):
    """Test of saving simple data."""

    @classmethod
    def setUpClass(cls):
        cls.name = "BasicTest"
        cls.aqm = AcquisitionManager(DATA_DIR)
        cls.aqm.new_acquisition(cls.name)

    def test_dir_was_created(self):
        self.assertTrue(os.path.exists(os.path.join(DATA_DIR, self.name)))

    def test_simple_save(self):
        """Save and load the simplest list."""
        x = np.linspace(0, 20 * np.pi, 101)
        y = np.sin(x)
        self.aqm.save_acquisition(x=x, y=y)

        data = AnalysisData(self.aqm.current_filepath)

        assert data is not None

        self.assertTrue(np.all(x == data.get("x")))
        self.assertTrue(np.all(y == data.get("y")))

    def test_open_old_file(self):
        basedir = os.path.dirname(__file__)
        old_file_path = os.path.join(basedir, "data/old_data_example.h5")
        data = AnalysisData(old_file_path)
        assert data, "File probably exists, but create DH5 object"
        x = np.linspace(0, 10 * np.pi, 101)
        self.assertAlmostEqual(np.abs(data.get("x") - x).sum(), 0)
        self.assertAlmostEqual(np.abs(data.get("y") - np.sin(x)).sum(), 0)

    def test_manager_die(self):
        """Save, make reload on AcquisitionManager and verify that it will found current acquisition."""
        x = np.linspace(0, 20 * np.pi, 101)
        y = np.sin(x)
        self.aqm.save_acquisition(x=x, y=y)

        self.aqm = AcquisitionManager(DATA_DIR)

        data = AnalysisData(self.aqm.current_filepath)

        assert data is not None

        self.assertTrue(np.all(x == data.get("x")))
        self.assertTrue(np.all(y == data.get("y")))

    @classmethod
    def tearDownClass(cls):
        """Remove tmp_test_data directory ones all test finished."""
        # if os.path.exists(DATA_DIR):
        #     shutil.rmtree(DATA_DIR)
        return super().tearDownClass()


class AcquisitionLoopTest(unittest.TestCase):
    """Test of saving simple data."""

    @staticmethod
    def acquire_sine(freq, points):
        x = np.linspace(0, 10 * np.pi, points)
        y = np.sin(freq * 2 * np.pi * x)
        return x, y

    @classmethod
    def setUpClass(cls) -> None:
        """Create a dictionary to verify with."""
        cls.name = "LoopTest"
        cls.aqm = AcquisitionManager(DATA_DIR)
        cls.aqm.new_acquisition(cls.name)

        cls.points = 101
        cls.freqs = np.linspace(0, 0.4, 10)

        cls.data = {"freq": [], "y": []}
        for freq in cls.freqs:
            x, y = cls.acquire_sine(freq, cls.points)
            cls.data["y"].append(y)
            cls.data["freq"].append(freq)
        cls.data["x"] = x  # type: ignore

        return super().setUpClass()

    def test_dir_was_created(self):
        self.assertTrue(os.path.exists(os.path.join(DATA_DIR, self.name)))

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
        loop = AcquisitionLoop()
        for freq in loop.iter(self.freqs):
            x, y = self.acquire_sine(freq, self.points)
            loop.append(y=y, freq=freq)
        loop.append(x=x)  # type: ignore
        self.aqm.save_acquisition(loop_freq=loop)

        # Verification
        self.data_verification_for_simple_loop()

    def test_classical_loop_call(self):
        """Save and load the simplest list.

        Protocol:

        for freq in freqs:
            x, y = ...
            push_to_save(y, freq)
        push_to_save(x)
        save()

        """
        # Protocol
        loop = AcquisitionLoop()
        for freq in loop(self.freqs):
            x, y = self.acquire_sine(freq, self.points)
            loop(y=y, freq=freq)
        loop(x=x)  # type: ignore
        self.aqm.save_acquisition(loop_freq=loop)

        # Verification
        self.data_verification_for_simple_loop()

    def test_classical_loop_with_level(self):
        """Save and load the same list as the previous one.

        But we put push_to_save(x) inside loop with parameter level=-1,
        so it should give as the same result.

        Protocol:

        for freq in freqs:
            x, y = ...
            push_to_save(y, freq)
            push_to_save(x, level=-1)
        save()

        """
        # Protocol
        loop = AcquisitionLoop()
        for freq in loop.iter(self.freqs):
            x, y = self.acquire_sine(freq, self.points)
            loop.append(y=y, freq=freq)
            loop.append(x=x, level=-1)
        self.aqm.save_acquisition(loop_freq=loop)

        # Verification
        self.data_verification_for_simple_loop()

    def test_classical_loop_multisave(self):
        """Save and load the same list as previous one.

        But now we save on every iteration of cycle.

        Protocol:

        for freq in freqs:
            x, y = ...
            push_to_save(y, freq)
            push_to_save(x, level=-1)
            save()

        """
        # Protocol
        loop = AcquisitionLoop()
        for freq in loop.iter(self.freqs):
            x, y = self.acquire_sine(freq, self.points)
            loop.append(y=y, freq=freq)
            loop.append(x=x, level=-1)
            self.aqm.save_acquisition(loop_freq=loop)

        # Verification
        self.data_verification_for_simple_loop()

    def data_verification_for_simple_loop(self):
        # fullpath = AcquisitionManager.current_acquisition.filepath

        data = AnalysisData(self.aqm.current_filepath)

        assert data is not None

        loop_freq = data.get("loop_freq")
        assert loop_freq is not None, "Cannot get LoopData from saved data."

        self.assertAlmostEqual(compare_np_array(self.data["freq"], loop_freq.get("freq")), 0)
        self.assertAlmostEqual(compare_np_array(self.data["y"], loop_freq.get("y")), 0)
        self.assertAlmostEqual(compare_np_array(self.data["x"], loop_freq.get("x")), 0)

        # for i, d in enumerate(loop_freq):
        #     self.assertAlmostEqual(self.data['freq'][i], d.freq)
        #     self.assertAlmostEqual(compare_np_array(self.data['y'][i], d.y), 0)
        #     self.assertAlmostEqual(compare_np_array(self.data['x'], d.x), 0)  # type: ignore

    @classmethod
    def tearDownClass(cls):
        """Remove tmp_test_data directory ones all test finished."""
        # data_directory = os.path.join(os.path.dirname(__file__), DATA_DIR)
        if os.path.exists(DATA_DIR):
            shutil.rmtree(DATA_DIR)
        return super().tearDownClass()


class AnalysisLoopTest(AcquisitionLoopTest):
    """Test for the AnalysisLoop.

    Take the same preparation that for the AcquisitionLoopTest,
    but has different data_verification function.
    """

    def data_verification_for_simple_loop(self):
        data = AnalysisData(self.aqm.current_filepath)

        assert data is not None

        loop_freq: dict = data.get("loop_freq")  # type: ignore
        assert loop_freq is not None, "Cannot get LoopData from saved data."

        for i, d in enumerate(loop_freq):
            self.assertAlmostEqual(self.data["freq"][i], d.freq)
            self.assertAlmostEqual(compare_np_array(self.data["y"][i], d.y), 0)
        self.assertAlmostEqual(compare_np_array(self.data["x"], loop_freq.x), 0)  # type: ignore

        # print(loop_freq['freq'][5])
        self.assertAlmostEqual(self.data["freq"][5], loop_freq["freq"][5])  # pylint: disable=E1136
        self.assertAlmostEqual(
            compare_np_array(self.data["y"][5], loop_freq[4:7]["y"][1]), 0
        )  # pylint: disable=E1136

        self.assertEqual(len(loop_freq), len(self.data["freq"]))


class MultiAnalysisLoopTest(unittest.TestCase):
    """Test of saving simple data."""

    @staticmethod
    def acquire_sine(freq, points, tau):
        x = np.linspace(10 * tau, 10 * tau + 10 * np.pi, points)
        y = np.sin(freq * 2 * np.pi * x)
        y *= np.exp(-x * tau)
        return x, y

    @classmethod
    def setUpClass(cls) -> None:
        """Create a dictionary to verify with."""
        cls.aqm = AcquisitionManager(DATA_DIR)
        cls.aqm.new_acquisition("MultiLoopTest2")

        cls.points = 101
        cls.freqs = np.linspace(0, 0.4, 10)
        cls.taus = np.linspace(0, 0.3, 5)

        cls.data = {"tau": [], "freq": [], "x": [], "y": []}
        for tau in cls.taus:
            cls.data["tau"].append(tau)
            cls.data["y"].append([])
            cls.data["freq"].append([])

            for freq in cls.freqs:
                x, y = cls.acquire_sine(freq, cls.points, tau)
                cls.data["y"][-1].append(y)
                cls.data["freq"][-1].append(freq)
            cls.data["x"].append(x)  # type: ignore

        return super().setUpClass()

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
        loop = AcquisitionLoop()

        for tau in loop.iter(self.taus):
            loop.append(tau=tau)
            for freq in loop.iter(self.freqs):
                x, y = self.acquire_sine(freq, self.points, tau)
                loop.append(y=y, freq=freq)
            loop.append(x=x)  # type: ignore

            self.aqm.save_acquisition(loop_tau_freq=loop)

        # Verification
        self.data_verification_for_2d_loop()

    def data_verification_for_2d_loop(self):
        data = AnalysisData(self.aqm.current_filepath)

        assert data is not None

        loop_freq = data.get("loop_tau_freq")
        assert loop_freq is not None, "Cannot get LoopData from saved data."

        for i, d in enumerate(loop_freq):
            for j, dd in enumerate(d):
                self.assertAlmostEqual(self.data["tau"][i], dd.tau)
                self.assertAlmostEqual(self.data["freq"][i][j], dd.freq)
                self.assertAlmostEqual(compare_np_array(self.data["y"][i][j], dd.y), 0)
            self.assertAlmostEqual(compare_np_array(self.data["x"][i], d.x), 0)  # type: ignore

    @classmethod
    def tearDownClass(cls):
        """Remove tmp_test_data directory ones all test finished."""
        if os.path.exists(DATA_DIR):
            shutil.rmtree(DATA_DIR)
        return super().tearDownClass()


if __name__ == "__main__":
    unittest.main()
