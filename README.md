# compartmentalized_EMT_Boolean_model_Mendik_et_al_2021

This repository contains the supporting python code to the paper by Mendik and Kerestély et al. detailed below, currently under submission. 

# Translocating proteins compartment-specifically alter the fate of epithelial-mesenchymal transition in a compartmentalized Boolean network model
Péter Mendik<sup>1#</sup>, Márk Kerestély<sup>1#</sup>, Sebestyén Kamp<sup>2</sup>, Dávid Deritei<sup>1</sup>, Nina Kunšič<sup>1</sup>, Péter Csermely<sup>1</sup>, Dániel V. Veres<sup>1,2</sup>

<sup>1</sup>Department of Molecular Biology, Institute of Biochemistry and Molecular Biology, Semmelweis University, Budapest, Hungary<br>
<sup>2</sup>Turbine Inc. Budapest, Hungary<br>
Corresponding author: D.V.V. (daniel.veres@turbine.ai)<br>
<sup>#</sup>The authors wish it to be known, that the first two authors should be regarded as Joint First Authors. <br>

## Abstract


Regulation of translocating proteins is crucial in defining cellular behaviour. Epithelial-mesenchymal transition (EMT) is important in cellular processes, such as cancer progression. Several orchestrators of EMT, such as key transcription factors, are known to translocate. We show that translocating proteins become enriched in EMT-signalling. To simulate the compartment-specific functions of translocating proteins we created a compartmentalized Boolean network model. This model successfully reproduced known biological traits of EMT and as a novel feature it also captured organelle-specific functions of proteins. Our results predicted that glycogen synthase kinase-3 beta (GSK3B) compartment-specifically alters the fate of EMT, amongst others the activation of nuclear GSK3B halts transforming growth factor beta-1 (TGFB) induced EMT. Moreover, our results recapitulated that the nuclear activation of glioma associated oncogene transcription factors (GLI) is needed to achieve a complete EMT. Compartmentalized network models will be useful to uncover novel biomarkers and to create more complex therapeutic targeting strategies.

## Code modules

The code is divided into different modules responsible for different parts of the analysis, organized into sub-folders in the repository:

### BooleanNet modified
This module contains the code, which was extensively used for the KI/KO in silico experiments described in the paper.  
Original code source: https://github.com/ialbert/booleannet <br>
Modifications:
- graphical user interface
- addition of different updating schemes (e.g. weighted general asynchronous, random order asynchronous, weighted random order asynchronous)
- implementation of short term perturbations to model noise and long term perturbations to model in silico KI/KO experiments
### Attractor repertoire and stable motif analysis
This module contains two Jupyter notebooks, which contain the step-by-step analysis of identifying the attractors and stable motif succession of the original 19 node EMT model of Steinway et al. and the new 30 node compartmentalized EMT model respectively. The code is using the latest algorithms by Rozum et al. The original tool is available at: https://github.com/jcrozum/StableMotifs.

### Attractor probabilities
The module contains code of for the numerical analysis for the stationary probability of the attractors in the presence of noise. The method uses a noisy update, scheme, where node updates can return the wrong node state with probability _p_. The models then are run for a large number of steps, initiated from each attractor state (which they can leave due to the noise) and finally the visitation probabilities are calculated from the simulation trajectories. The analysis is done in a step-by-step manner in a Jupyter notebook and summerized in an exported excel table.

### EMT heatmap
The module consists of a Jupyter notebook and data files that are needed for the visualisation of stable states of the different EMT models after single node perturbations.
(Supplementary Figure S1, S2, S3)