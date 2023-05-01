from abc import (ABC, abstractmethod)


class CatalogABC(ABC):
    @abstractmethod
    def waveform_filename_from_simname(self, sim_name):
        raise NotImplementedError()

    @abstractmethod
    def waveform_filepath_from_simname(self, sim_name):
        raise NotImplementedError()

    @abstractmethod
    def metadata_filename_from_simname(self, sim_name):
        raise NotImplementedError()

    @abstractmethod
    def metadata_filepath_from_simname(self, sim_name):
        raise NotImplementedError()

    @abstractmethod
    def download_waveform_data(self, sim_name):
        raise NotImplementedError()

    @abstractmethod
    def waveform_url_from_simname(self, sim_name):
        raise NotImplementedError()


import os
import sxs
from . import waveform


class CatalogBase(CatalogABC, sxs.Catalog):
    def __init__(self, *args, **kwargs) -> None:
        sxs.Catalog.__init__(self, *args, **kwargs)

    def get(self, sim_name):
        if sim_name not in self.simulations_dataframe[
                'simulation_name'].to_list():
            raise IOError(f"Simulation {sim_name} not found in catalog."
                          f"Please check that it exists")
        filepath = self.waveform_filepath_from_simname(sim_name)
        if not os.path.exists(filepath) or os.path.getsize(filepath) == 0:
            if self._verbosity > 1:
                print(f"..As data does not exist in cache:"
                      f"  (in {filepath}),\n"
                      f"..we will now download it from"
                      " {}".format(self.waveform_url_from_simname(sim_name)))
            self.download_waveform_data(sim_name)
        metadata = self.get_metadata(sim_name)
        if type(metadata) is not dict and hasattr(metadata, "to_dict"):
            metadata = metadata.to_dict()
        return waveform.WaveformModes.load_from_h5(filepath, metadata=metadata)

    def get_metadata(self, sim_name):
        df = self.simulations_dataframe
        if sim_name not in df['simulation_name'].to_list():
            raise IOError(f"Simulation {sim_name} not found in catalog."
                          f"Please check that it exists")
        return sxs.Metadata(df.loc[sim_name].to_dict())

    def set_attribute_in_waveform_data_file(self, sim_name, attr, attr_value):
        """Set attributes in the HDF5 file holding waveform data for a given
        simulation

        Args:
            sim_name (str): Name/Tag of the simulation
            attr (str): Name of the attribute to set
            attr_value (any/serializable): Value of the attribute
        """
        import h5py
        file_path = self.waveform_filepath_from_simname(sim_name)
        with h5py.File(file_path, 'a') as fp:
            if attr not in fp.attrs:
                fp.attrs[attr] = attr_value
