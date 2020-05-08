# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
# Copyright 2018 SerialLab Corp.  All rights reserved.
from haikunator import Haikunator as H
import uuid


class Haikunator(H):
    """
    Override the random element generation.
    """
    def haikunate(self, delimiter='-', token_length=4, token_hex=False, token_chars='0123456789'):
        """
        Generate heroku-like random names to use in your python applications

        :param delimiter: Delimiter
        :param token_length: TokenLength
        :param token_hex: TokenHex
        :param token_chars: TokenChars
        :type delimiter: str
        :type token_length: int
        :type token_hex: bool
        :type token_chars: str
        :return: heroku-like random string
        :rtype: str
        """
        if token_hex:
            token_chars = '0123456789abcdef'

        adjective = self._random_element(self._adjectives)
        noun = self._random_element(self._nouns)

        sections = [adjective, noun, self._token()]
        return delimiter.join(filter(None, sections))

    def _token(self):
        val = hex(hash(uuid.uuid4()))
        return str(val[2:])


adjectives = [
    'active', 'alveolar', 'autumn', 'bonded', 'comparative', 'conchoidal',
    'convective',
    'constant', 'cartesian', 'close', 'crystalline',
    'conductive', 'current', 'crimson',
    'eutropic', 'inorganic',
    'diffracted', 'dimensional', 'dissolved', 'diatomic',
    'deuterated', 'erosive', 'endemic', 'exothermic',
    'entropic',
    'isomorphic', 'prospective', 'grey', 'green',
    'hybrid', 'heliocentric', 'insoluble', 'inert', 'ionized', 'iterative',
    'igneous', 'intrepid', 'inferential',
    'kinetic', 'lunar', 'pythagorean', 'linear', 'opaque',
    'median', 'magnetic', 'malleable', 'metric', 'mechanical', 'macroscopic',
    'neural', 'nuclear', 'nucleic', 'metamorphic', 'micorbial',
    'oblique',
    'optical', 'polar',
    'organic', 'interstitial', 'periodic', 'photosynthetic', 'polymorphic',
    'seismic',
    'random',
    'riparian', 'radioactive', 'variable', 'rectangular', 'reflective',
    'relativistic',
    'solvent', 'statistical',
    'square', 'second', 'singular', 'spectral',
    'scalar', 'soluble',
    'theoretical',
    'thermal', 'terrestrial', 'ultraviolet', 'viscous',
    'whole',
    'quantum', 'xerophilous', 'xenodochial'
]

nouns = [
    'allotropy', 'amplitude', 'atom', 'anode', 'base', 'beam', 'binomial',
    'biome', 'buffer',
    'alkaloid', 'blueshift', 'compound', 'cathode', 'spectrograph', 'catalyst',
    'cell', 'conference',
    'chromosome', 'diffusion', 'density', 'data', 'disk', 'delta',
    'chloroplast',
    'effusion', 'electrolyte', 'element', 'emulsion', 'enzyme',
    'formula', 'force', 'gamete', 'geosphere',
    'frequency', 'genome', 'gravity', 'hall', 'hypothesis',
    'hominid', 'lattice', 'lab', 'line', 'light', 'limit',
    'lithosphere', 'math', 'neuron',
    'mode', 'moon', 'mesosphere', 'magnitude', 'matter', 'mineral', 'molecule',
    'meosis', 'nitrogen', 'network',
    'nucleus', 'neutron',
    'patent', 'particle', 'parameter', 'polymer',
    'quartz', 'resonance',
    'relativity', 'regression',
    'serum', 'trigonometry', 'serum', 'radian', 'scale', 'scale',
    'spectrograph',
    'solution', 'solute', 'volume', 'star', 'RNA',
    'term', 'trachyte', 'theorum', 'universe', 'travel', 'time',
    'telemetry',
    'union',
    'volume', 'velocity', 'wave', 'wavelength',
    'water', 'vector'
]
