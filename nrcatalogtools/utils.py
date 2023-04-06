# Copyright (C) 2023 Aditya Vijaykumar, Md Arif, Prayush Kumar
# This program is free software; you can redistribute it and/or modify it
# under the terms of the GNU General Public License as published by the
# Free Software Foundation; either version 3 of the License, or (at your
# option) any later version.
#
# This program is distributed in the hope that it will be useful, but
# WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU General
# Public License for more details.
#
# You should have received a copy of the GNU General Public License along
# with this program; if not, write to the Free Software Foundation, Inc.,
# 51 Franklin Street, Fifth Floor, Boston, MA  02110-1301, USA.
import lal
import numpy as np
import pathlib
import requests
import sxs

## --------------------------------------------------------------
nrcatalog_cache_dir = pathlib.Path('~/.nr_data/').expanduser().resolve()

rit_catalog_info = {}
rit_catalog_info['cache_dir'] = nrcatalog_cache_dir / 'RIT'
rit_catalog_info['metadata_dir'] = rit_catalog_info['cache_dir'] / 'metadata'
rit_catalog_info['data_dir'] = rit_catalog_info['cache_dir'] / 'data'

rit_catalog_info['url'] = 'https://ccrgpages.rit.edu/~RITCatalog/'
rit_catalog_info['metadata_url'] = rit_catalog_info['url'] + '/Metadata/'
rit_catalog_info['data_url'] = rit_catalog_info['url'] + '/Data/'
rit_catalog_info['possible_resolutions'] = [
    100, 120, 88, 118, 130, 140, 144, 160, 200
]

rit_catalog_info['metadata_file_fmts'] = [
    'RIT:BBH:{:04d}-n{:3d}-id{:d}_Metadata.txt',
    'RIT:eBBH:{:04d}-n{:3d}-ecc_Metadata.txt',
]
rit_catalog_info['waveform_file_fmts'] = [
    'ExtrapStrain_RIT-BBH-{:04d}-n{:3d}.h5',
    'ExtrapStrain_RIT-eBBH-{:04d}-n{:3d}.h5',
]
rit_catalog_info['max_id_val'] = 6

maya_catalog_info = {
    'cache_dir': nrcatalog_cache_dir / 'MAYA',
    'url': '',
    'metadata_file_fmts': [],
    'waveform_file_fmts': [],
}

## --------------------------------------------------------------


def url_exists(link, num_retries=100):
    """Check if a given URL exists on the web.

    Args:
        link : complete web URL

    Returns:
        bool: True/False whether the URL could be found on WWW.
    """
    requests.packages.urllib3.disable_warnings()
    for n in range(num_retries):
        try:
            response = requests.head(link, verify=False)
            if response.status_code == requests.codes.ok:
                return True
            else:
                return False
        except:
            continue
    return False


def download_file(url, path, progress=False, if_newer=True):
    if url_exists(url):
        return sxs.utilities.downloads.download_file(url,
                                                     path,
                                                     progress=progress,
                                                     if_newer=if_newer)
    return None


def call_with_timeout(myfunc, args=(), kwargs={}, timeout=5):
    '''
    This function calls user-provided `myfunc` with user-provided
    `args` and `kwargs` in a separate multiprocessing.Process.
    if the function evaluation takes more than `timeout` seconds, the
    `Process` is terminated and error raised. If it evalutes within
    `timeout` seconds, the results are fetched from the `Queue` and
    returned.
    '''
    from multiprocessing import (Process, Queue)

    def funcwrapper(p, *args, **kwargs):
        '''
        This thin wrapper calls the user-provided function, and puts
        its result into the multiprocessing `Queue`  so that it can be
        obtained via `Queue().get()`.
        '''
        res = myfunc(*args, **kwargs)
        p.put(res)

    queue = Queue()
    task = Process(target=funcwrapper, args=(queue, *args))
    task.start()
    task.join(timeout=timeout)
    task.terminate()
    try:
        result = queue.get(timeout=0)
        return result
    except:
        raise Exception("Timeout")


def time_to_physical(M):
    """Factor to convert time from dimensionless units to SI units

    parameters
    ----------
    M: mass of system in the units of solar mass

    Returns
    -------
    converting factor
    """

    return M * lal.MTSUN_SI


def amp_to_physical(M, D):
    """Factor to rescale strain to mass M and distance D convert from
    dimensionless units to SI units

    parameters
    ----------
    M: mass of the system in units of solar mass
    D: Luminosity distance in units of megaparsecs

    Returns
    -------
    Scaling factor
    """

    return lal.G_SI * M * lal.MSUN_SI / (lal.C_SI**2 * D * 1e6 * lal.PC_SI)


def dlm(ell, m, theta):
    """Wigner d function
    parameters
    ----------
    ell: lvalue
    m: mvalue
    theta: theta angle, e. g in GW, inclination angle iota

    Returns:
    value of d^{ell m}(theta)
    """
    kmin = max(0, m - 2)
    kmax = min(ell + m, ell - 2)
    d = 0
    for k in range(kmin, kmax + 1):
        numerator = np.sqrt(
            float(
                np.math.factorial(ell + m) * np.math.factorial(ell - m) *
                np.math.factorial(ell + 2) * np.math.factorial(ell - 2)))
        denominator = (np.math.factorial(k - m + 2) *
                       np.math.factorial(ell + m - k) *
                       np.math.factorial(ell - k - 2))
        d += (((-1)**k / np.math.factorial(k)) * (numerator / denominator) *
              (np.cos(theta / 2))**(2 * ell + m - 2 * k - 2) *
              (np.sin(theta / 2))**(2 * k - m + 2))
    return d


def ylm(ell, m, theta, phi):
    """
    parameters:
    -----------
    ell: lvalue
    m: mvalue
    theta: theta angle, e. g in GW, inclination angle iota
    phi: phi angle, e. g. in GW, orbital phase

    Returns:
    --------
    ylm_s(theta, phi)
    """
    return (np.sqrt((2 * ell + 1) / (4 * np.pi)) * dlm(ell, m, theta) *
            np.exp(1j * m * phi))
