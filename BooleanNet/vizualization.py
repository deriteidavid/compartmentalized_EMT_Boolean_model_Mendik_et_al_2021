# importing necessary packages
import os

import numpy as np
import pandas as pd
import seaborn as sns

import matplotlib.pyplot as plt


def heatmap(final_states, attractors, folder, distance_from):

    final_states = final_states.loc[:, final_states.columns.str.startswith('E')]

    attractor_map = pd.concat([final_states, attractors[["E", "M"]]], axis=1)

    attractor_map.loc["dist_from_" + distance_from, "E"] = 0
    attractor_map.loc["dist_from_" + distance_from, "M"] = len(attractor_map.index)
    attractor_map = attractor_map.sort_values("dist_from_" + distance_from, axis=1)
    attractor_map = attractor_map.loc[np.any(final_states.isin(['True', 'False']).values, axis=1)]

    attr_data = attractor_map.replace('True', 'TRUE')
    attr_data = attr_data.replace('False', 'FALSE')

    c_attr_data = attractor_map.copy()

    for col in attractor_map.columns:
        c_attr_data[col] = np.where(attractor_map[col] == attractor_map[distance_from], False, True)

    c_attr_data.columns = c_attr_data.columns.str.replace("E_", "")

    # A4 heatmap
    a4_dims = (11.7, 8.27)
    f, axes = plt.subplots(1, 1, figsize=a4_dims)

    cmap = sns.color_palette(['#6db1bf', '#ffb249'])
    sns.set(font_scale=0.4)
    emt_hm = sns.heatmap(c_attr_data, cmap=cmap, annot=attr_data, linewidths=.5, linecolor='white', fmt='',
                         square=True, cbar_kws={"shrink": .8})
    emt_hm.set_ylabel('Nodes', fontsize=10)
    emt_hm.set_xlabel('Perturbed nodes ( _ attractor name)', fontsize=10)
    emt_hm.set_title('Attractor states', fontsize=10, loc='left')
    emt_hm.set_xticklabels(emt_hm.get_xmajorticklabels(), fontsize=8, rotation=90)
    emt_hm.set_yticklabels(emt_hm.get_ymajorticklabels(), size=8)

    # exporting the figure to .png
    file = os.path.normpath(folder + "/Attractor_states.png")
    f.savefig(file, dpi=400, bbox_inches='tight')
    plt.close(f)

def pathway_activation(node_activation, node_to_pathway_map, folder):
    pathway_members = pd.read_excel(node_to_pathway_map)

    for i in node_activation:

        perturb_node = str(i)

        activations = node_activation[i].copy()

        # activations.to_csv(perturb_node+".csv")

        node_list = pathway_members.loc[pathway_members['node_state_E'] == True, 'node'].to_list()

        ded_act = activations[~(activations.shift() == activations).all(axis=1)].copy()
        ded_act.loc[:, node_list] = 1 - ded_act[node_list]

        ded_act_t = ded_act.T.copy()

        ded_act_t["nodes"] = ded_act_t.index.to_list()
        activations2 = ded_act_t.merge(pathway_members, how="left", left_on='nodes', right_on='node')
        activations2 = activations2[activations2['include'] == 1]
        activations2.drop(['nodes', 'node', 'include', 'node_state_E'], axis=1, inplace=True)
        pathway_activations = activations2.groupby([activations2.pathway]).mean()
        # gb.droplevel()

        f, axes = plt.subplots(1, 1, figsize=(8, 5))

        # sns.set(font_scale=2)
        pth_plot = sns.lineplot(data=pathway_activations.T, linewidth=2.0)
        pth_plot.set_ylabel('Relative activity', fontsize=10)
        pth_plot.set_xlabel('Time steps', fontsize=10)
        pth_plot.set_title('Signaling pathway activities during ' + perturb_node + ' perturbation', fontsize=11,
                           loc='left')
        pth_plot.set(ylim=(-0.1, 1.1))
        pth_plot.legend(bbox_to_anchor=(1.05, 1), loc=2, borderaxespad=0.)

        try:
            os.makedirs(os.path.normpath(folder + "/pathway_activities"))
        except:
            pass

        if perturb_node[0] == "E":
            f.savefig(os.path.normpath(folder + "/pathway_activities/" + perturb_node + '_pertubation_pathway_activities.png'), dpi=400, bbox_inches='tight')
        plt.close(f)