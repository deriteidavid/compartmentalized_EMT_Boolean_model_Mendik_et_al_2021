from __future__ import print_function

import os
import pickle
import random
import re
import sys
from datetime import datetime
from functools import reduce

import numpy as np
import pandas as pd
from openpyxl import load_workbook

import __init__
import state

#
# handy shortcuts
#

true = lambda x: True
randbool = lambda x: random.random() <= 0.5
false = lambda x: False
truth = lambda x: x
notcomment = lambda x: x and not x.startswith('#')
strip = lambda x: x.strip()
upper = lambda x: x.upper()


def join(data, sep="\t", patt="%s\n"):
    """Joins a list by sep and formats it via pattern"""
    return patt % sep.join(list(map(str, data)))


def error(msg):
    """Prints an error message and stops"""
    print('*** error: %s' % msg)
    sys.exit()


def warn(msg):
    """Prints a warning message"""
    print('*** warning: %s' % msg)


def tuple_to_bool(value):
    """
    Converts a value triplet to boolean values
    From a triplet: concentration, decay, threshold
    Truth value = concentration > threshold/decay
    """
    return value[0] > value[2] / value[1]


def bool_to_tuple(value):
    """
    Converts a boolean value to concentration, decay, threshold triplets
    """
    return value and (1.0, 1.0, 0.5) or (0.0, 1.0, 0.5)


def check_case(nodes):
    """
    Checks names are unique beyond capitalization
    """
    upcased = set(list(map(upper, nodes)))
    if len(upcased) != len(nodes):
        error('some node names are capitalized in different ways -> %s!' % list(nodes))


def split(text):
    """
    Strips lines and returns nonempty lines
    """
    return list(filter(notcomment, list(map(strip, text.splitlines()))))


def unnesting(df, explode):
    if not isinstance(explode, list):
        explode = [explode]
    idx = df.index.repeat(df[explode[0]].str.len())
    df1 = pd.concat([
        pd.DataFrame({x: np.concatenate(df[x].values)}) for x in explode], axis=1)
    df1.index = idx

    return df1.join(df.drop(explode, 1), how='right')


def multiple(x, y):
    multiples = []
    for i in range(0, len(y)):
        if x % y[i] == 0:
            multiples.append(y[i])
    return multiples


def default_shuffler(lines):
    """Default shuffler"""
    temp = lines[:]
    random.shuffle(temp)
    return temp

def weighted_shuffler(lines, rank, steps=None):
    """Weighted shuffler - lines with higher rank are selected with lower probability"""
    if steps is None: steps = len(lines)

    ranks = set(rank)
    ranks = dict(zip(ranks, sorted(ranks, reverse=True)))
    rank = [ranks.get(item, item) for item in rank]

    temp = random.choices(lines, rank, k=steps)
    return temp


def random_choice(lines):
    """Default shuffler"""
    return [random.choice(lines)]


def node_diff(state1, state2):
    if type(state1) is dict: state1 = state.State(**state1)
    if type(state2) is dict: state2 = state.State(**state2)
    return [key for key, value in state1.items() if str(value) != str(getattr(state2, key))]


def detect_cycles(data):
    """
    Detects cycles in the data

    Returns a tuple where the first item is the index at which the cycle occurs
    the first time and the second number indicates the length of the cycle
    (it is 1 for a steady state)
    """

    fsize = len(data)

    # maximum size
    for msize in range(1, fsize // 2 + 1):
        for index in range(fsize):
            left = data[index:index + msize]
            right = data[index + msize:index + 2 * msize]
            if left == right:
                return index, msize

    return 0, 0


def point_attractor_index(state_index):
    """Returns the index of the list where a fix point attractor starts."""
    position = list(enumerate(state_index))
    position = pd.DataFrame(position, columns=['Index', 'State'])
    position = position.loc[position['State'].diff() != 0.0]

    return position["Index"].iloc[-1]


def detect_point_attractor(text, states, sim_mode):
    if sim_mode == "sync":
        return states[-2] == states[-1]
    else:
        model_temp = __init__.Model(text, mode="sync")
        model_temp.initialize(missing=false, defaults=states[-1])
        model_temp.iterate(steps=2)
        return model_temp.states[0] == model_temp.states[1]


def phenotype(states, pheno=None):
    if type(states) is dict: states = state.State(**states)

    pheno = pd.DataFrame(pheno).T
    if type(None) != "NoneType":
        node_states = []
        for i in range(0, pheno.shape[1]):
            node_states.append(str(getattr(states, pheno.columns[i])))

        for i in range(0, len(pheno)):
            if list(pheno.iloc[i,].values) == node_states:
                attractor_type = pheno.index[i]
                return attractor_type
    else:
        print("Matching phenotype not found")
        return "A"


def attractor_naming(states, attractors, pheno=None):
    attractor_type = phenotype(states, pheno)
    attractor_name = sum([attractor_type == re.split("(\d+)", key)[0] for key in list(attractors.keys())])
    attractor_name = attractor_type + str(attractor_name)

    return attractor_name


def pair_gcd(a, b):
    """Return greatest common divisor using Euclid's Algorithm."""
    while b:
        a, b = b, a % b
    return a


def list_gcd(data):
    """Recursive gcd calculation that applies for all elements of a list"""
    if len(data) == 2:
        return pair_gcd(*data)
    else:
        return pair_gcd(data[0], list_gcd(data[1:]))


def as_set(nodes):
    """Wraps input into a set if needed. Allows single input or any iterable"""
    if isinstance(nodes, str):
        return set([nodes])
    else:
        return set(nodes)


def know_state(s, attractors):
    for attractor_name, attractor_state in attractors.items():
        if str(state.State(**s)) in str(state.State(**attractor_state)):
            return 1, attractor_name
    return 0, None


def bsave(obj, fname='data.bin'):
    """
    Saves (pickles) objects
    >>> obj = { 1:[2,3], 2:"Hello" }
    >>> bsave( obj )
    >>> obj == bload()
    True
    """
    pickle.dump(obj, open(fname, 'wb'), protocol=2)  # maximal compatibility


def bload(fname='data.bin'):
    """Loads a pickle from a file"""
    return pickle.load(open(fname, 'rb'))


def find_by_name(folder, search):
    path = None
    for dir, dirnames, filenames in os.walk(folder):
        for filename in [f for f in filenames if f == search]:
            path = os.path.normpath(os.path.join(dir, filename))
            break
    return path

def output_dir(folder, simulation_mode, perturbation_type, iterations, steps):
    model_type_dir = "/04_Simulations/01_Single cell/"

    if simulation_mode == "sync":
        sim_mode_dir = "01_Synchronous/"
    elif simulation_mode == "time":
        sim_mode_dir = "02_Time/" # Deterministic asynchronous (DA)
    elif simulation_mode == "async":
        sim_mode_dir = "03_General asynchronous/"
    elif simulation_mode == "wasync":
        sim_mode_dir = "04_Weighted general asynchronous/"
    elif simulation_mode == "roa":
        sim_mode_dir = "05_Random order asynchronous/"
    elif simulation_mode == "wroa":
        sim_mode_dir = "06_Weighted random order asynchronous/"
    elif simulation_mode == "rank":
        sim_mode_dir = "07_Ranked random order asynchronous/"
    elif simulation_mode == "plde":
        sim_mode_dir = "08_Piece-wise linear differential/"

    if perturbation_type == "None":
        perturb_type_dir = "01_Attractor stability/"
    elif perturbation_type == "Noise":
        perturb_type_dir = "02_Noise perturbation/"
    elif perturbation_type == "KI/KO":
        perturb_type_dir = "03_KI or KO perturbation/"

    if iterations == 1:
        result_dir = str(iterations) + " iteration " + str(steps) + " steps"
    else:
        result_dir = str(iterations) + " iterations " + str(steps) + " steps"

    dir = os.path.normpath(folder + model_type_dir + sim_mode_dir + perturb_type_dir + result_dir)

    try:
        os.makedirs(dir)
    except:
        pass

    return dir


def fsave(obj, fname="file.txt", dir=None):
    """Save object as text file"""
    if dir is not None: fname = find_by_name(dir, fname)
    if ".txt" in fname:
        if isinstance(obj, pd.DataFrame):
            obj = obj.to_string(header=True, index=True)
        file = open(fname, "w")
        file.write(obj)
        file.close()
    elif ".xlsx" in fname:
        now = datetime.now()

        if os.path.isfile(fname):
            book = load_workbook(fname)
            writer = pd.ExcelWriter(fname, engine='openpyxl')
            writer.book = book
        else:
            writer = pd.ExcelWriter(fname, engine='openpyxl')

        obj.to_excel(writer, sheet_name=now.strftime("%Y%m%d_%H%M"))
        writer.save()


def fopen(fname="file.txt", dir=None):
    """Loads text from a file"""
    if dir is not None: fname = find_by_name(dir, fname)
    with open(fname) as file:
        text = file.read()
    return text


def nested_dict(dictionary, value):
    for k, v in dictionary.items():
        if list(v.values())[0] == value:
            return [k] + list(v.keys())
    return None

def reshape_trajectory_info(trajectories):
    new_dict = {}
    for name, v in trajectories.items():
        for trajectory, v in v.items():
            for count, node_difference in v.items():
                new_dict[name + "_trajectory_" + str(trajectory)] = [count] + node_difference

    trajectories = pd.DataFrame.from_dict(new_dict, orient='index')
    trajectories.columns = ["count"] + list(trajectories.columns[1:])
    return trajectories

def average_node_activation(node_state):
    average_node_activity = {}
    for pertubation, node_states in node_state.items():
        average_activity = pd.DataFrame()
        for node in node_states.keys():
            node_activation = pd.DataFrame(node_state[pertubation][node]).T
            node_activation = node_activation.fillna(method='ffill')
            average_activity[node]=node_activation.mean(axis=1)
        average_node_activity[pertubation] = average_activity

    return average_node_activity

class Collector(object):
    """
    Collects data over a run
    """

    def __init__(self, dir, **kwargs):
        """Default constructor"""
        self.folder = dir
        self.node_state = {}
        self.trajectory = {}
        self.init_state = {}
        self.attractor = {}
        self.final_state = {}

        if kwargs["attractors"] is None or len(open(find_by_name(self.folder, kwargs["attractors"])).read()) == 0:
            for key, value in kwargs.items():
                if key == "attractors": continue
                file = find_by_name(self.folder, value)
                if file is not None:
                    text = fopen(fname=file)
                    model = __init__.Model(text, mode="sync")
                    model.initialize(missing=false)
                    model.iterate(steps=2)
                    #if model.states[0] == model.states[1]:
                    self.attractors(model.first, attractor_name=key)
        else:
            file = find_by_name(self.folder, kwargs["attractors"])
            attractors = pd.read_csv(file, delim_whitespace=True, index_col=0)
            for i in range(0, attractors.shape[0]):
                attractor = {}
                for j in range(0, attractors.shape[1]): attractor[attractors.columns[j]] = attractors.iloc[i,j]
                self.attractors(state.State(**attractor), attractor_name=str(attractors.index[i]))

    def initial_states(self, states, name):
        """Collect initial state"""
        if name not in self.init_state.keys():
            self.init_state[name] = {node: str(node_state) for node, node_state in states.items()}
            self.init_state[name]["count"] = 1

            self.init_state[name]["node_diff_from_E"] = "\n".join(node_diff(states, self.attractor["E"]))
            self.init_state[name]["dist_from_E"] = len(node_diff(states, self.attractor["E"]))
            self.init_state[name]["node_diff_from_M"] = "\n".join(node_diff(states, self.attractor["M"]))
            self.init_state[name]["dist_from_M"] = len(node_diff(states, self.attractor["M"]))

        else:
            self.init_state[name]["count"] += 1

    def collect(self, states, name):
        """Collects the node values into a list"""
        nodes = as_set(states[0].keys())
        for node in nodes:
            print(node)
            LAST_STATE = None
            for state in states:
                if LAST_STATE is None:
                    values = [int(getattr(state, node))]
                    LAST_STATE = state
                elif LAST_STATE != state:
                    values.append(int(getattr(state, node)))
                    LAST_STATE = state

            if name in self.node_state.keys():
                if node in self.node_state[name].keys():
                    self.node_state[name][node].append(values)
                else:
                    self.node_state[name][node] = [values]
            else:
                self.node_state[name] = {node: [values]}

    def trajectories(self, states, name):
        """Collection of node changes."""
        LAST_STATE = None
        node_differnece = []

        for state in states:
            keys = []
            if LAST_STATE is not None:
                keys = node_diff(state, LAST_STATE)
            if len(keys) != 0:
                node_differnece.append(','.join(keys))
            LAST_STATE = state

        if name not in self.trajectory.keys():
            self.trajectory[name] = {1: {1: node_differnece}}
        elif name in self.trajectory.keys():
            keys = nested_dict(self.trajectory[name], node_differnece)
            if keys is not None:
                self.trajectory[name][keys[0]][keys[1] + 1] = self.trajectory[name][keys[0]].pop(keys[1])
            else:
                self.trajectory[name][max(list(self.trajectory[name].keys())) + 1] = {1: node_differnece}


    def attractors(self, states, name=None, attractor_name=None, index=None, pheno=None):
        """Collect attractor states"""
        if index is None:
            final_state = states
        else:
            final_state = states[index]

        if attractor_name is None: known, attractor_name = know_state(final_state, self.attractor)
        if attractor_name is None and known == 0: attractor_name = attractor_naming(final_state, self.attractor, pheno)
        if attractor_name not in self.attractor.keys():
            self.attractor[attractor_name] = {node: str(node_state) for node, node_state in final_state.items()}

        if index is not None:
            self.trajectories(states, name + "_" + attractor_name)
            self.initial_states(states[0], name)
            self.final_states(states, name + "_" + attractor_name, index)
            self.collect(states, name + "_" + attractor_name)

    def final_states(self, states, name, index):
        """Collect final states"""
        final_state = states[index]
        init_state = states[0]

        if name not in self.final_state.keys():
            self.final_state[name] = {node: str(node_state) for node, node_state in final_state.items()}
            self.final_state[name]["count"] = 1
            self.final_state[name]["min steps"] = index
            self.final_state[name]["max steps"] = index
            self.final_state[name]["average steps"] = index

            self.final_state[name]["node_diff_from_E"] = "\n".join(node_diff(final_state, self.attractor["E"]))
            self.final_state[name]["dist_from_E"] = len(node_diff(final_state, self.attractor["E"]))
            self.final_state[name]["node_diff_from_M"] = "\n".join(node_diff(final_state, self.attractor["M"]))
            self.final_state[name]["dist_from_M"] = len(node_diff(final_state, self.attractor["M"]))
            self.final_state[name]["node_diff_from_init_state"] = "\n".join(node_diff(final_state, init_state))
            self.final_state[name]["dist_from_init_state"] = len(node_diff(final_state, init_state))

        else:
            n = self.final_state[name]["count"]
            self.final_state[name]["count"] += 1
            self.final_state[name]["min steps"] = min(index, self.final_state[name]["min steps"])
            self.final_state[name]["max steps"] = max(index, self.final_state[name]["max steps"])
            self.final_state[name]["average steps"] = ((self.final_state[name]["average steps"] * n) + index)/(n+1)

    def get_averages(self, normalize=True):
        """
        Averages the collected data for the each node
        Returns a dictionary keys by nodes containing the

        """
        out = {}
        for node in self.node_state:
            all = self.node_state[node]
            size = float(len(all))

            # this sums lists!
            def listadd(xlist, ylist):
                return [x + y for x, y in zip(xlist, ylist)]

            values = reduce(listadd, all)

            if normalize:
                def divide(x):
                    return x / size

                values = list(map(divide, values))
            out[node] = values
        return out


def test():
    import doctest
    doctest.testmod()


if __name__ == '__main__':
    test()
