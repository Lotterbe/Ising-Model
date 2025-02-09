from numba import jitclass, int64, float64, boolean
import numpy as np
from scipy.special import ellipk as elli

spec = [('NX', int64), ('NY', int64), ('total_number_of_points', int64),
        ('itersteps', int64), ('first_skip', int64), ('skip', int64),
        ('inter', float64), ('beta', float64), ('beta_crit', float64),
        ('actual_config', int64[:, :]), ('save_number', int64),
        ('save_lenght', int64), ('all_configs', int64[:, :, :]),
        ('b_ext', float64), ('flip', boolean)]

@jitclass(spec)
class Metropolis:
    def __init__(self, x_lenght, y_lenght, beta=0.20, external_field=0, flip=True):
        """ Constructor - defines the attributes

        :param x_lenght: x-lenght of lattice
        :param y_lenght: y-lenght of lattice
        :param beta: the inverse temperature
        :param external_field: external magnetic field
        :param flip: Boolean for flip on or off
        """
        self.NX = x_lenght
        self.NY = y_lenght
        self.total_number_of_points = self.NX * self.NY
        # check if (itersteps - first_skip) % skip == 0
        self.itersteps = 4500 * self.total_number_of_points
        self.first_skip = 500 * self.total_number_of_points
        self.skip = 20 * self.total_number_of_points
        #self.itersteps = 2200 * self.total_number_of_points
        #self.first_skip = 200 * self.total_number_of_points
        #self.skip = 20 * self.total_number_of_points
        # J = inter
        self.inter = 1
        self.beta = beta
        # ca. 0.4406
        self.beta_crit = np.log(1 + np.sqrt(2)) / 2
        self.actual_config = self._init_config()
        self.save_number = 0
        self.save_lenght = int((self.itersteps - self.first_skip)
                               / self.skip) + \
                           (self.itersteps - self.first_skip) % self.skip
        self.all_configs = np.zeros((self.save_lenght, self.NX, self.NY),
                                    dtype=np.int64)
        self.b_ext = external_field
        self.flip = flip

    def _init_config(self):
        """Initialize start configuration hot or cold.

        :return: the initial config of lattice
        """
        # cold one
        if self.beta >= self.beta_crit:
            return np.ones((self.NX, self.NY), dtype=np.int64)
        # hot one
        else:
            return np.random.choice(np.array((-1, 1)), (self.NX, self.NY))

    def __configurator(self):
        """Choose random spin out of lattice

        :return: The corresponding line and column of the choosen spin
        """
        random_number = np.random.randint(self.total_number_of_points)
        i = int(random_number / self.NY)
        j = random_number % self.NY
        return i, j

    def save(self):
        """Saves actual config in an array """
        # copy is very important here!
        self.all_configs[self.save_number] = np.copy(self.actual_config)
        self.save_number += 1

    def reset(self):
        self.save_lenght = int((self.itersteps - self.first_skip)
                               / self.skip) + \
                           (self.itersteps - self.first_skip) % self.skip
        self.all_configs = np.zeros((self.save_lenght, self.NX, self.NY),
                                    dtype=np.int64)
        self.save_number = 0

    def __update_step(self, step):
        """The main update routine:
        - Chooses random spin and flips it
        - Checks how action changes
        - If accepted, then leaves the flipped spin otherwise undoes it
        - Skip a few configs in the saved configs array
        for autocorrelation reasons

        :param step: Number of updates
        """
        nx, ny = self.__configurator()
        neighbours = self.actual_config[nx - 1, ny] \
                     + self.actual_config[nx, ny - 1] \
                     + self.actual_config[(nx + 1) % self.NX, ny] \
                     + self.actual_config[nx, (ny + 1) % self.NY]
        dE = 2 * self.inter * self.actual_config[nx, ny] * neighbours \
             - self.b_ext * self.actual_config[nx, ny] * (-1)
        # insgesamt + weil - E = - (- salt) = - sneu
        # faktor zwei oder in bext reinziehen
        r = np.random.random(1)[0]
        if np.exp(-self.beta * dE) >= r:
            self.actual_config[nx, ny] *= (-1)
            # Vermeidung von Autokorrelationen
        if step >= self.first_skip and step % self.skip == 0:
            self.save()
            # Flip Flop
            if self.flip == True:
                self.actual_config *= (-1)

    def start_simulation(self):
        """This method starts the whole simulation and updates
        the configs itersteps times.

        :return: The saved configs after itersteps updates.
        """
        print('Starting Simulation..')
        print(self.save_lenght, ' configs will come out.')
        for step in range(0, self.itersteps):
            self.__update_step(step)
        return self.all_configs


class Observables:
    def __init__(self, configs, beta, inter=1, external_field=0):
        """Constructor - defines some attributes

        :param configs: the simulated configs of lattice
        :param beta: inverse temperature
        :param inter: interaction
        :param external_field: external magnetic field
        """
        self.all_configs = configs
        self.total_number_of_points = len(self.all_configs[0]) \
                                      * len(self.all_configs[0][0])
        self.beta = beta
        self.beta_crit = np.log(1 + np.sqrt(2)) / 2
        self.inter = inter
        self.b_ext = external_field
        self.save_lenght = len(configs)
        self.energy_per_config = np.zeros(self.save_lenght,
                                          dtype=np.float64)
        self.energy_average = 0
        self.m_per_config = np.zeros(self.save_lenght,
                                     dtype=np.float64)
        self.m_average = 0
        self.nabs_m_per_config = np.zeros(self.save_lenght,
                                     dtype=np.float64)
        self.nabs_m_average = 0
        self.chi = 0
        self.heat_per_lattice = 0
        self.energy_var = 0
        self.magnetisation_var = 0
        self.heat_var = 0
        self.chi_var = 0
        self.yang_magnetisation = 0
        self.onsager_energy = 0

    def magnetisation(self):
        """Calculates the magnetisation of lattice

        """
        self.m_per_config = np.abs(np.sum(np.sum(self.all_configs, axis=2),
                                          axis=1)) \
                            / self.total_number_of_points
        self.m_average = np.mean(self.m_per_config)

    def configs_magnetisation(self, configs):
        """Calculates the magnetisation of lattice

        """
        ret = np.abs(np.sum(np.sum(configs, axis=2),
                                          axis=1)) \
                            / self.total_number_of_points
        return ret

    def nabs_magnetisation(self):
        self.nabs_m_per_config = np.sum(np.sum(self.all_configs, axis=2),
                                          axis=1) \
                            / self.total_number_of_points
        self.nabs_m_average = np.mean(self.nabs_m_per_config)


    def total_energy(self):
        """Calculates the energy of the lattice

        """
        #self.beta *
        self.energy_per_config = -  self.beta*self.inter * np.sum(np.sum((
                self.all_configs * (np.roll(self.all_configs, shift=1,
                                            axis=1)
                                    + np.roll(self.all_configs, shift=1,
                                              axis=2))), axis=2), axis=1) \
                                 - self.b_ext * np.sum(self.all_configs)
        self.energy_average = np.mean(self.energy_per_config)

    def configs_energy(self, configs):
        ret = -  self.beta*self.inter * np.sum(np.sum((configs * (np.roll(configs, shift=1,axis=1)
                                                + np.roll(configs, shift=1,axis=2))), axis=2), axis=1) \
                                                 - self.b_ext * np.sum(configs)
        return ret

    def debug_energy(self, beta=None):
        if beta == None:
            beta = self.beta
        return -16 * np.sinh(8*beta)/(12+2*np.cosh(8*beta))

    def specific_heat(self):
        """Calculates the specific heat, the variance of energy

        """
        squared_energy_average = np.mean(self.energy_per_config ** 2)
        self.heat_per_lattice = self.beta ** 2 * (
                squared_energy_average - self.energy_average ** 2
        ) / self.total_number_of_points

    def magnetic_susceptibility(self):
        """Calculates the magnetic susceptibility,
        the variance of magnetisation

        """
        squared_magnetisation_average = np.mean(self.m_per_config ** 2)
        self.chi = self.beta * (
                squared_magnetisation_average - self.m_average ** 2
        ) * self.total_number_of_points


    def measure_observables(self):
        """This method starts the whole measuring of the observables
         for the simulated lattice

        """
        print('Start Measuring...')
        self.total_energy()
        self.specific_heat()
        self.magnetisation()
        self.magnetic_susceptibility()

        variances = self.bootstrap(100)
        self.energy_var = variances[0]
        self.magnetisation_var = variances[1]
        self.heat_var = variances[2]
        self.chi_var = variances[3]
        self.OnsagerEnergy()
        self.YangMagn()

    def save_simulation(self, filename):
        array_list = ['#' + str(len(self.all_configs)) + ' Konfigurationen',
                      '#' + str(self.total_number_of_points) + ' Gitterpunkte',
                      '#' + ' beta =' + str(self.beta),
                      '#' + ' Wechselwirkung = ' + str(self.inter),
                      '#' + ' externes Magnetfeld = ' + str(self.b_ext)]
        np.savez_compressed(filename, infos=array_list, configs=self.all_configs,
                            magnetisation=self.m_average, magnetisation_var=self.magnetisation_var,
                            energy=self.energy_average/self.total_number_of_points,
                            energy_var=self.energy_var/self.total_number_of_points,
                            specific_heat=self.heat_per_lattice, heat_var=self.heat_var,
                            chi=self.chi, chi_var=self.chi_var,
                            Onsager_Energy = self.onsager_energy,
                            Yang_Magnetisation = self.yang_magnetisation)

    def jackknife_onedel(self, observable_per_config):
        """Calculates the error with jackknife for primary observables.

        :param observable_per_config: The observable for which
        error will be calculated
        :param del_number: How big the blocks are and therefore
        how much values are 'deleted' for creating new data set
        :return: estimator for standard deviation for the observable
        """
        observable = observable_per_config
        number_of_configs = len(observable)
        obs_part = [np.mean(np.roll(observable, shift=-part,
                                    axis=0)[:-1])
                    for part in range(int(number_of_configs))]
        obs_part_mean = np.mean(obs_part)
        obs_var = (number_of_configs - 1) / number_of_configs * \
                  np.sum((np.array(obs_part) - obs_part_mean) ** 2)
        return np.sqrt(obs_var)

    def jackknife_onedel_for_var(self, observable_per_config):
        """Calculates the error with jackknife for secundary observables.

        :param observable_per_config: The primary observable
        :param del_number: How big the blocks are and therefore
        how much values are 'deleted' for creating new data set
        :return: estimator for standard deviation
        for the secundary observable
        """
        base_observable = observable_per_config
        number_of_configs = len(base_observable)
        obs_base_part_squared = np.array([np.mean(
            np.roll(base_observable, shift=-part,
                    axis=0)[:- 1]
        ) ** 2 for part in range(int(number_of_configs))])
        obs_base_square_part = np.array([np.mean(
            np.roll(base_observable ** 2, shift=-part,
                    axis=0)[:- 1]
        ) for part in range(int(number_of_configs))])
        obs_part = obs_base_square_part - obs_base_part_squared
        obs_part_mean = np.mean(obs_part)
        obs_var = (number_of_configs - 1) / number_of_configs * \
                  np.sum((obs_part - obs_part_mean) ** 2)
        return np.sqrt(obs_var)

    def bootstrap(self, samples):
        number_of_configs = self.save_lenght
        energy_arr = np.zeros(shape=(samples, number_of_configs))
        magneti_arr = np.zeros(shape=(samples, number_of_configs))
        heat_arr = np.zeros(shape=(samples, number_of_configs))
        chi_arr = np.zeros(shape=(samples, number_of_configs))
        for s in range(samples):
            new_conf_arr = np.zeros_like(self.all_configs)
            for conf_num in range(number_of_configs):
                rnumber = np.random.randint(0,int(number_of_configs))
                new_conf_arr[conf_num] = self.all_configs[rnumber]
            energy_arr[s] = self.configs_energy(new_conf_arr)
            meansquare = np.mean(energy_arr[s]**2)
            squaremean = np.mean(energy_arr[s])**2
            heat_arr[s] = self.beta**2*(meansquare - squaremean)
            magneti_arr[s] = self.configs_magnetisation(new_conf_arr)
            meansquare = np.mean(magneti_arr[s]**2)
            squaremean = np.mean(magneti_arr[s])**2
            chi_arr[s] = self.beta * (meansquare - squaremean) * self.total_number_of_points
        return np.std(energy_arr), np.std(magneti_arr), np.std(heat_arr)/self.total_number_of_points, np.std(chi_arr)


    def OnsagerEnergy(self):
        # Some variables for simpler calculating
        k = 2 * np.tanh(2 * self.beta * self.inter) ** 2 - 1
        l = (2 * np.sinh(2 * self.beta * self.inter)) \
             / (np.cosh(2 * self.beta * self.inter) ** 2 )
        integral = elli(l)
        self.onsager_energy = (-(self.beta * self.inter)
                               / (np.tanh(2 * self.beta * self.inter))) *\
                              (1 + 2 / np.pi * k * integral)

    def YangMagn(self):
        # Is only for T < T_c not equal to zero => beta > beta_c
        if self.beta > self.beta_crit:
            self.yang_magnetisation = (1 - np.sinh(
                np.log(1 + np.sqrt(2) * self.beta / self.beta_crit)
            ) ** (-4)) ** (1 / 8)
        else:
            self.yang_magnetisation = 0
