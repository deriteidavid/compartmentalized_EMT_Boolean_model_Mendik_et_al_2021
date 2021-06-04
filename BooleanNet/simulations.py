import itertools as it
import pandas as pd
import __init__, util, tokenizer
import os


def simulation(folder, init_files, simulation_mode, perturbation_type, perturbed_comb, iterate, steps,
               phenotype, attractor_file=None, noise=None, perturbed_nodes=None):
    coll = util.Collector(dir=folder, **dict(init_files, **{"attractors": str(attractor_file)}))

    if noise is not None:
        step = int(steps * noise)
    else:
        step = int(steps * 0.02)
    if step == 0: step = steps + 1

    print(init_files)

    for state, file in init_files.items():
        print(state)
        text = util.fopen(file, folder)

        model = __init__.Model(text, mode="sync")
        model.initialize(missing=util.false)
        model.iterate(steps=1)
        init_state = model.first

        # create perturbation combination list; if type is None, use phenotype names
        if perturbation_type != "None":
            if perturbed_nodes is None: perturbed_nodes = model.nodes
            perturbations = []
            for i in range(1, perturbed_comb + 1):
                for subset in it.combinations(perturbed_nodes, i):
                    perturbations.append(list(subset))
        else:
            perturbations = [[state]]

        for perturbation in perturbations:
            if perturbation[0] == state:
                name = "_".join(perturbation)
            else:
                name = state + "_" + "_".join(perturbation)

            # for Noise/KI_KO sim find nodes that have to be turned on or off
            if perturbation_type != "None":
                on = [node for node in perturbation if getattr(init_state, node) == False]
                off = [node for node in perturbation if getattr(init_state, node) == True]

                print("on:", on, "off:", off)

            for iteration in range(0, iterate):
                # for Noise/KI_KO sim change node state and comment out Boolean rule
                if perturbation_type != "None":
                    new_text = tokenizer.modify_rules(text, turnon=on, turnoff=off)
                else:
                    new_text = text

                model = __init__.Model(new_text, mode=simulation_mode)
                model.initialize(missing=util.false)
                if simulation_mode == "plde":
                    model.iterate(steps=steps, fullt=step)
                else:
                    model.iterate(steps=step)

                if perturbation_type == "Noise":
                    new_text = text
                elif util.detect_point_attractor(new_text, model.states, simulation_mode):
                    index = util.point_attractor_index(model.fp())
                    coll.attractors(states=model.states, name=name, index=index, pheno=phenotype)
                    continue
                elif step == steps + 1:
                    coll.attractors(states=model.states, name=name, index=1, pheno=phenotype)
                    continue

                for i in range(step, steps, step):
                    model_temp = __init__.Model(new_text, mode=simulation_mode)
                    model_temp.initialize(missing=util.false, defaults=model.last)
                    model_temp.iterate(steps=step)

                    model.states = model.states + model_temp.states[1:]

                    if util.detect_point_attractor(new_text, model.states, simulation_mode):
                        index = util.point_attractor_index(model.fp())
                        coll.attractors(states=model.states, name=name, index=index, pheno=phenotype)
                        break
                    elif i == steps - step:
                        if simulation_mode == "sync":
                            index, size = util.detect_cycles(model.states)
                            if index == 0:
                                index = len(model.states)-1
                            else:
                                model.states = model.states[0:(index+2*size)]
                        else:
                            index = len(model.states)-1
                        coll.attractors(states=model.states, name=name, index=index, pheno=phenotype)
                        break

    # save results
    util.fsave(pd.DataFrame(coll.attractor).T, fname=attractor_file, dir=folder)
    dir = util.output_dir(folder, simulation_mode, perturbation_type, iterate, steps)
    trajectories = util.reshape_trajectory_info(coll.trajectory)

    if perturbation_type == "Noise":
        attactor_stability = pd.DataFrame(columns=init_files.keys())
        for key in coll.final_state.keys():
            state = key.split("_")[0]
            attractor = key.split("_")[-1]
            if attractor in attactor_stability.index:
                attactor_stability.loc[attractor, state] = attactor_stability.loc[attractor, state] + \
                                                           coll.final_state[key]["count"]
            else:
                attactor_stability.loc[attractor, state] = coll.final_state[key]["count"]
                attactor_stability = attactor_stability.fillna(0)

        util.fsave(attactor_stability, fname=os.path.normpath(dir + "/Attractor_stability.xlsx"))


    util.fsave(pd.DataFrame(coll.init_state), fname=os.path.normpath(dir + "/Initial_states.xlsx"))
    util.fsave(pd.DataFrame(coll.final_state), fname=os.path.normpath(dir + "/Final_states.xlsx"))
    util.fsave(trajectories, fname=os.path.normpath(dir + "/Trajectories.xlsx"))

