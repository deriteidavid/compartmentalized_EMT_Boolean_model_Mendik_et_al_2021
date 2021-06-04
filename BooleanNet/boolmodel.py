from ruleparser import Parser
import tokenizer, util, state
import pandas as pd
import random
import itertools as it


class BoolModel(Parser):
    """
    Maintains the functionality for all models
    """

    def initialize(self, missing=None, defaults={}):
        """
        Initializes the model, needs to be called to reset the simulation 
        """

        # create a new lexer                
        self.lexer = tokenizer.Lexer().lexer

        self.parser.old = state.State()
        self.parser.new = state.State()

        # references must be attached to the parser class 
        # to be visible during parsing
        self.states = self.parser.states = [self.parser.old]

        # parser the initial data
        list(map(self.local_parse, self.init_lines))

        # deal with uninitialized nodes
        if self.uninit_nodes:
            if missing:
                for node in self.uninit_nodes:
                    value = missing(node)

                    self.parser.RULE_SETVALUE(self.parser.old, node, value, None)
                    self.parser.RULE_SETVALUE(self.parser.new, node, value, None)
            else:
                util.error('uninitialized nodes: %s' % list(self.uninit_nodes))

        # override any initialization with defaults
        for node, value in defaults.items():
            self.parser.RULE_SETVALUE(self.parser.old, node, value, None)
            self.parser.RULE_SETVALUE(self.parser.new, node, value, None)

        # will be populated upon the first call
        self.lazy_data = {}

    @property
    def first(self):
        """Returns the first state"""
        return self.states[0]

    @property
    def last(self):
        """Returns the last state"""
        return self.states[-1]

    @property
    def data(self):
        """
        Allows access to states via a dictionary keyed by the nodes
        """
        # this is an expensive operation so it loads lazily
        assert self.states, 'States are empty'
        if not self.lazy_data:
            nodes = self.first.keys()
            for state in self.states:
                for node in nodes:
                    self.lazy_data.setdefault(node, []).append(state[node])
        return self.lazy_data

    def state_update(self):
        """Internal update function"""
        p = self.parser
        p.old = p.new
        p.new = p.new.copy()
        p.states.append(p.new)

    def local_parse(self, line):
        """Used like such only to keep track of the last parsed line"""
        global LAST_LINE
        LAST_LINE = line
        return self.parser.parse(line)

    def iterate(self, steps, **kwds):
        """
        Iterates over the lines 'steps' times. Allows other parameters for compatibility with the plde mode
        """

        # needs to be reset in case the data changes
        self.lazy_data = {}

        if self.parser.mode == 'wasync' or self.parser.mode == 'async':
            update_lines = pd.DataFrame(self.update_lines.items()).explode(1)
            lines = util.weighted_shuffler(list(update_lines[1]), list(update_lines[0]), steps=steps)

        for index in range(1, steps):
            self.parser.RULE_START_ITERATION(index, self)
            self.state_update()
            if self.parser.mode == 'wasync' or self.parser.mode == 'async':
                self.local_parse(lines[index])
            elif self.parser.mode == 'wroa':
                update_lines = pd.DataFrame(self.update_lines.items()).explode(1)

                ranks = []
                lines = []

                for i in range(0, update_lines.shape[0]):
                    rank = update_lines.iloc[i, 0]
                    line = update_lines.iloc[i, 1]
                    p = (sum(self.update_lines.keys())-rank)/sum(self.update_lines.keys())
                    if random.choices([0, 1], weights=[1-p, p])[0] == 1:
                        ranks.append(rank)
                        lines.append(line)

                lines = util.default_shuffler(lines)
                list(map(self.local_parse, lines))
            else:
                for rank in self.ranks:
                    lines = self.update_lines[rank]
                    lines = util.default_shuffler(lines)
                    list(map(self.local_parse, lines))


    def save_states(self, fname):
        """
        Saves the states into a file
        """
        if self.states:
            fp = open(fname, 'wt')
            cols = ['STATE'] + self.first.keys()
            hdrs = util.join(cols)
            fp.write(hdrs)
            for state in self.states:
                cols = [state.fp()] + state.values()
                line = util.join(cols)
                fp.write(line)
            fp.close()
        else:
            util.error('no states have been created yet')

    def trajectory(self):
        """
        Create dictionary containing node changes.
        """
        LAST_STATE = None
        self.trajecotry = {}

        for state in self.states:
            if LAST_STATE is not None:
                keys = [key for (key, value) in state.items() if value != getattr(LAST_STATE, key)]
                if len(keys) != 0: self.trajecotry[state.fp()] = keys
            LAST_STATE = state

    def detect_attractors(self):
        """Detect the cycles in the current states of the model"""
        return util.detect_cycles(data=self.fp())

    def report_attractors(self):
        """
        Convenience function that reports on steady states
        """
        index, size = self.detect_attractors()

        if size == 0:
            print("No cycle or steady state could be detected from the %d states" % len(self.states))
        elif size == 1:
            print("Steady state starting at index %s -> %s" % (index, self.states[index]))
        else:
            print("Cycle of length %s starting at index %s" % (size, index))

    def fp(self):
        """The models current fingerprint"""
        return [s.fp() for s in self.states]


if __name__ == '__main__':
    text = """
    A  =  B = C =  False
    D  = E  =  True
    
    5: A <= 2*C and (2*not B or 2*D or 2*E)
    10: B <= 1*A
    15: C <= 1*D
    20: D <= 1*B 
    5: E <= 3*A xor 2*D
    """

    model = BoolModel(mode='sync', text=text)

    model.initialize(missing=util.false)

    print('>>>', model.first)

    model.iterate(steps=2)

    print(model.fp())
    model.report_attractors()
    model.save_states(fname='states.txt')

    # detect cycles from a list of states
    states = ['S1', 'S2', 'S1', 'S2', 'S1', 'S2']
    print()
    print('States %s -> Detect cycles %s' % (states, util.detect_cycles(states)))
