import os
import sys
from copy import deepcopy

from PyQt5.QtCore import *
from PyQt5.QtGui import *
from PyQt5.QtWidgets import *

import __init__
import simulations
import util
import tokenizer

sim_modes = {"sync": "Synchronous", "time": "Time", "async": "General asynchronous (GA)",
             "wasync": "Weighted general asynchronous (wGA)", "roa": "Random order asynchronous (ROA)",
             "wroa": "Weighted random order asynchronous (wROA)", "rank": "Ranked random order asynchronous (rROA)",
             "plde": "Piece-wise linear differential equations (PLDE)"}
perturb_type = ["None", "Noise", "KI/KO"]
nodes = []


class NewPheno(QDialog):
    """
    This "window" is a QWidget. If it has no parent, it
    will appear as a free-floating window as we want.
    """

    def __init__(self, parent: QWidget = None):
        super().__init__(parent)

        self.layout = QGridLayout()
        self.setWindowTitle("New phenotype")

        self.pheno_text = QLabel("Phenotype")
        self.pheno_lable = QLineEdit(self)

        self.node_name_1 = QComboBox(self)
        self.node_name_1.addItems(["Select nodes"] + nodes)
        self.node_state_1 = QComboBox(self)
        self.node_state_1.addItems(["Node state", "True", "False"])

        self.node_name_2 = QComboBox(self)
        self.node_name_2.addItems(["Select nodes"] + nodes)
        self.node_state_2 = QComboBox(self)
        self.node_state_2.addItems(["Node state", "True", "False"])

        self.submit = QPushButton("Add new phenotype", self)
        self.submit.clicked.connect(self.message)

        self.layout.addWidget(self.pheno_text, 0, 0)
        self.layout.addWidget(self.pheno_lable, 0, 1)

        self.layout.addWidget(self.node_name_1, 1, 0)
        self.layout.addWidget(self.node_state_1, 1, 1)

        self.layout.addWidget(self.node_name_2, 2, 0)
        self.layout.addWidget(self.node_state_2, 2, 1)

        self.layout.addWidget(self.submit, 3, 1)

        self.setLayout(self.layout)

    def setMessage(self, text: str):
        self.pheno_lable.setText(text)

    def message(self) -> dict:
        pheno_type = self.pheno_lable.text()
        node_1_name = self.node_name_1.currentText()
        node_1_state = self.node_state_1.currentText()
        node_2_name = self.node_name_2.currentText()
        node_2_state = self.node_state_2.currentText()

        super().accept()

        return dict(zip([pheno_type], [dict(zip([node_1_name, node_2_name], [node_1_state, node_2_state]))]))


class App(QMainWindow):
    def __init__(self):
        super(App, self).__init__()
        self.title = 'BooleanNet'
        self.left = 0
        self.top = 30
        self.width = 1820
        self.height = 770
        self.initUI()

    def initUI(self):
        self.setWindowTitle(self.title)
        self.setGeometry(self.left, self.top, self.width, self.height)

        self.folder_button = QPushButton('Select model directory', self)
        self.folder_button.setShortcut('Ctrl+O')
        self.folder_button.clicked.connect(self.open_directory)
        self.folder_button.setGeometry(QRect(20, 25, 170, 25))
        self.folder_button.setToolTip(
            "<td align='justify'; width=400>Select model directory containing initial state and "
            "Boolean rule definitions</td>")
        self.folder_line = QLineEdit(self)
        self.folder_line.setGeometry(QRect(200, 25, 1600, 25))
        self.folder_line.setToolTip("<td align='justify'; width=400>Input the model directory location or select model "
                                    "directory containing initial state and Boolean rule definitions by clicking on the "
                                    "button on the left</td>")

        # Set fonds
        Bfont = QFont()
        Bfont.setBold(True)
        Bfont.setWeight(50)

        # Create box containing input file data
        self.input_box = QGroupBox("Input files", self)
        self.input_box.setGeometry(QRect(20, 70, 580, 680))
        self.input_box.setFont(Bfont)
        self.input_box.setAutoFillBackground(False)
        self.input_box.setFlat(True)
        self.input_box.setCheckable(True)
        self.input_box.setChecked(False)
        self.input_box.setStyleSheet("QGroupBox {border: 1px solid gray; border-radius: 5px;  }")

        self.attractor_file_button = QPushButton('Select attractor file', parent=self.input_box)
        self.attractor_file_button.setShortcut('Ctrl+O')
        self.attractor_file_button.clicked.connect(self.select_file)
        self.attractor_file_button.setGeometry(QRect(10, 20, 170, 25))
        self.attractor_file_button.setToolTip(
            "<td align='justify'; width=400>Select file in which attractors are saved if it "
            "exists</td>")
        self.attractor_file_line = QLineEdit(parent=self.input_box)
        self.attractor_file_line.setGeometry(QRect(190, 20, 380, 25))
        self.attractor_file_line.setToolTip(
            "<td align='justify'; width=400>Input the model directory location or select model "
            "directory containing initial state and Boolean rule definitions by clicking on the "
            "button on the left</td>")
        self.init_file_table = QTableWidget(parent=self.input_box)
        self.init_file_table.setGeometry(QRect(10, 50, 560, 620))
        self.init_file_table.setColumnCount(2)
        self.init_file_table.setHorizontalHeaderLabels(["Phenotype", "Input file"])
        self.init_file_table.setColumnWidth(0, int(self.init_file_table.width() / 2))
        self.init_file_table.setColumnWidth(1, int(self.init_file_table.width() / 2))

        # Create box containing simulation information
        self.sim_box = QGroupBox("Simulation information", self)
        self.sim_box.setGeometry(QRect(620, 70, 580, 180))
        self.sim_box.setFont(Bfont)
        self.sim_box.setAutoFillBackground(False)
        self.sim_box.setFlat(True)
        self.sim_box.setCheckable(True)
        self.sim_box.setChecked(False)
        self.sim_box.setStyleSheet("QGroupBox {border: 1px solid gray; border-radius: 5px;  }")

        self.sim_mode_text = QLabel("Update mode", parent=self.sim_box)
        self.sim_mode_text.setGeometry(QRect(10, 60, 300, 25))
        self.sim_mode_combo = QComboBox(parent=self.sim_box)
        self.sim_mode_combo.setGeometry(QRect(275, 60, 300, 25))
        self.sim_mode_combo.addItems(sim_modes.values())
        self.sim_mode_combo.setItemData(0, "<td align='justify'; width=400><b>Synchronous</b> updating mode assumes "
                                           "that all components of the system take the same amount of time to change "
                                           "and updates all nodes simultaneously</td>", Qt.ToolTipRole)
        self.sim_mode_combo.setItemData(2, "<td align='justify'; width=400>Asynchronous updating mode allows for nodes "
                                           "with different time scales associated with different types of processes in "
                                           "biological systems<br><br>"
                                           "By selecting <b>Deterministic asynchronous (DA)</b> updating mode at each "
                                           "time step all nodes whose rank equals the multiple of the time step is "
                                           "updated</td>", Qt.ToolTipRole)
        self.sim_mode_combo.setItemData(2, "<td align='justify'; width=400>Asynchronous updating mode allows for nodes "
                                           "with different time scales associated with different types of processes in "
                                           "biological systems<br><br>"
                                           "By selecting <b>General asynchronous (GA)</b> updating mode at each time "
                                           "step one node will be selected at random and updated</td>", Qt.ToolTipRole)
        self.sim_mode_combo.setItemData(3, "<td align='justify'; width=400>Asynchronous updating mode allows for nodes "
                                           "with different time scales associated with different types of processes in "
                                           "biological systems<br><br>"
                                           "By selecting <b>Weighted general asynchronous (wGA)</b> updating mode at "
                                           "each time step one node will be selected at random based on its rank and "
                                           "updated</td>", Qt.ToolTipRole)
        self.sim_mode_combo.setItemData(4, "<td align='justify'; width=400>Asynchronous updating mode allows for nodes "
                                           "with different time scales associated with different types of processes in "
                                           "biological systems<br><br>"
                                           "By selecting <b>Random order asynchronous (ROA)</b> updating mode at each "
                                           "time step all nodes will be updated in a random order</td>", Qt.ToolTipRole)
        self.sim_mode_combo.setItemData(5, "<td align='justify'; width=400>Asynchronous updating mode allows for nodes "
                                           "with different time scales associated with different types of processes in "
                                           "biological systems<br><br>"
                                           "By selecting <b>Weighted random order asynchronous (wROA)</b> updating mode"
                                           " at each time step nodes are selected at random based on its rank and "
                                           "updated</td>", Qt.ToolTipRole)
        self.sim_mode_combo.setItemData(6, "<td align='justify'; width=400>Asynchronous updating mode allows for nodes "
                                           "with different time scales associated with different types of processes in "
                                           "biological systems<br><br>"
                                           "By selecting <b>Ranked random order asynchronous (rROA)</b> updating mode"
                                           " at each time step nodes are selected based on their rank and nodes with "
                                           "the same rank are updated in a random order before moving to higher rank"
                                           "</td>", Qt.ToolTipRole)
        self.sim_mode_combo.setItemData(7, "<td align='justify'; width=400><b>Piece-wise linear differential equations "
                                           "(PLDE)</b> updating mode translates Boolean values to a set of continuous "
                                           "variables (concentrations, decay rates and thresholds) and Boolean rules "
                                           "to linear system of piecewise differential equations</td>", Qt.ToolTipRole)

        self.iterate_text = QLabel("Number of iterations", parent=self.sim_box)
        self.iterate_text.setGeometry(QRect(10, 100, 300, 25))
        self.iterate_spin = QSpinBox(parent=self.sim_box)
        self.iterate_spin.setGeometry(QRect(275, 100, 300, 25))
        self.iterate_spin.setToolTip("<td align='justify'; width=400>Number of <b>iterations</b> represent the number "
                                     "of times the simulation, starting from the initial state and ending in an "
                                     "attractor or after reaching the maximum number of steps, should be repeated.<br><br>"
                                     "Due to deterministic nature of <b>synchronous</b> update, just one iteration "
                                     "suffices for simulations run in synchronous updating mode, however due to "
                                     "stochasticity of the <b>asynchronous</b> simulations it is necessary to rerun the "
                                     "simulation multiple times to get representative results for asynchronous updating"
                                     " mode</td>")
        if self.sim_mode_combo.currentIndex() > 0:
            self.iterate_spin.setRange(5, 1000)
            self.iterate_spin.setSingleStep(50)
        else:
            self.iterate_spin.setRange(1, 1000)
        self.sim_mode_combo.currentTextChanged.connect(self.change_iterations)

        self.steps_text = QLabel("Number of steps", parent=self.sim_box)
        self.steps_text.setGeometry(QRect(10, 140, 300, 25))
        self.steps_spin = QSpinBox(parent=self.sim_box)
        self.steps_spin.setGeometry(QRect(275, 140, 300, 25))
        self.steps_spin.setToolTip("<td align='justify'; width=400>Number of <b>steps</b> represents the maximum number"
                                   " of time steps in each simulation deemed sufficient for the simulation to converge"
                                   "on an attractor</td>")
        self.steps_spin.setRange(1, 50000)
        self.steps_spin.setSingleStep(50)
        self.steps_spin.setValue(20000)

        # Create box containing simulation information
        self.perturb_box = QGroupBox("Perturbation information", self)
        self.perturb_box.setGeometry(QRect(620, 260, 580, 180))
        self.perturb_box.setFont(Bfont)
        self.perturb_box.setAutoFillBackground(False)
        self.perturb_box.setFlat(True)
        self.perturb_box.setCheckable(True)
        self.perturb_box.setChecked(False)
        self.perturb_box.setStyleSheet("QGroupBox {border: 1px solid gray; border-radius: 5px;  }")

        self.perturb_type_text = QLabel("Perturbation type", parent=self.perturb_box)
        self.perturb_type_text.setGeometry(QRect(10, 30, 300, 25))
        self.perturb_type_combo = QComboBox(parent=self.perturb_box)
        self.perturb_type_combo.setGeometry(QRect(275, 30, 300, 25))
        self.perturb_type_combo.addItems(perturb_type)
        self.perturb_type_combo.setItemData(0, "<td align='justify'; width=400>Select <b>None</b> if you want to run "
                                               "the simulation without any perturbations.<br><br>"
                                               "This option can be used to study the stability of initial states in "
                                               "single cell model or to check how different initial states will affect "
                                               "the final state of the network in the intercellular model</td>",
                                            Qt.ToolTipRole)
        self.perturb_type_combo.setItemData(1, "<td align='justify'; width=400>Select <b>Noise</b> if you want to "
                                               "simulate the effect of short term noise on the network.<br><br>"
                                               "This option can be used to study the stability of initial states to "
                                               "short term noise in which the initial state of a node is flipped for "
                                               "percentage of total simulation steps</td>",
                                            Qt.ToolTipRole)
        self.perturb_type_combo.setItemData(2, "<td align='justify'; width=400>Select <b>KI/KO</b> if you want to run"
                                               "in silico node knockout or over-expression experiments.<br><br>"
                                               "This option can be used to study the effects of node knockout or "
                                               "over-expression on network network state</td>", Qt.ToolTipRole)

        self.perturb_combo_text = QLabel("Number of node perturbation combinations", parent=self.perturb_box)
        self.perturb_combo_text.setGeometry(QRect(10, 70, 300, 25))
        self.perturb_combo_spin = QSpinBox(parent=self.perturb_box)
        self.perturb_combo_spin.setGeometry(QRect(275, 70, 300, 25))
        self.perturb_combo_spin.setToolTip(
            "<td align='justify'; width=400>Number of <b>node perturbation combinations</b>"
            " represent the number of nodes that should be perturbed simultaneously</td>")
        self.perturb_combo_spin.setRange(1, len(nodes))

        self.noise_text = QLabel("Length of perturbation", parent=self.perturb_box)
        self.noise_text.setGeometry(QRect(10, 110, 300, 25))
        self.noise_spin = QDoubleSpinBox(parent=self.perturb_box)
        self.noise_spin.setGeometry(QRect(275, 110, 300, 25))
        self.noise_spin.setDecimals(3)
        self.noise_spin.setToolTip("<td align='justify'; width=400>Number of <b>steps</b> represents the maximum number"
                                   " of time steps in each simulation deemed sufficient for the simulation to converge"
                                   "on an attractor</td>")
        if self.sim_mode_combo.currentIndex() > 0:
            self.noise_spin.setValue(0.02)
        else:
            self.noise_spin.setValue(100 / self.steps_spin.value())

        if self.perturb_type_combo.currentIndex() == 0:
            self.perturb_combo_text.setEnabled(False)
            self.perturb_combo_spin.setEnabled(False)
        else:
            self.perturb_combo_text.setEnabled(True)
            self.perturb_combo_spin.setEnabled(True)

        if self.perturb_type_combo.currentIndex() == 1:
            self.noise_text.setEnabled(True)
            self.noise_spin.setEnabled(True)
        else:
            self.noise_text.setEnabled(False)
            self.noise_spin.setEnabled(False)

        self.perturb_type_combo.currentTextChanged.connect(self.perturb_info)

        self.node_box = QGroupBox("Node perturbation information", self)
        self.node_box.setGeometry(QRect(620, 450, 580, 300))
        self.node_box.setFont(Bfont)
        self.node_box.setAutoFillBackground(False)
        self.node_box.setFlat(True)
        self.node_box.setCheckable(True)
        self.node_box.setChecked(False)
        self.node_box.setStyleSheet("QGroupBox {border: 1px solid gray; border-radius: 5px;  }")

        self.node_table = QTableWidget(parent=self.node_box)
        self.node_table.setGeometry(QRect(10, 20, 560, 270))
        self.node_table.setColumnCount(2)
        self.node_table.setHorizontalHeaderLabels(["Node", "Perturbed"])
        self.node_table.setColumnWidth(0, int(self.init_file_table.width() / 2))
        self.node_table.setColumnWidth(1, int(self.init_file_table.width() / 2))

        # Create box containing input file data
        self.pheno_box = QGroupBox("Phenotype", self)
        self.pheno_box.setGeometry(QRect(1220, 70, 580, 440))
        self.pheno_box.setFont(Bfont)
        self.pheno_box.setAutoFillBackground(False)
        self.pheno_box.setFlat(True)
        self.pheno_box.setCheckable(True)
        self.pheno_box.setChecked(False)
        self.pheno_box.setStyleSheet("QGroupBox {border: 1px solid gray; border-radius: 5px;  }")

        self.pheno_table = QTableWidget(parent=self.pheno_box)
        self.pheno_table.setGeometry(QRect(10, 20, 560, 370))
        self.pheno_table.setColumnCount(2)
        self.pheno_table.setRowCount(4)
        self.pheno_table.setHorizontalHeaderLabels(["AJ", "VIM"])
        self.pheno_table.setVerticalHeaderLabels(["E", "H", "M", "I"])
        self.pheno_table.setItem(0, 0, QTableWidgetItem("True"))
        self.pheno_table.setItem(0, 1, QTableWidgetItem("False"))
        self.pheno_table.setItem(1, 0, QTableWidgetItem("True"))
        self.pheno_table.setItem(1, 1, QTableWidgetItem("True"))
        self.pheno_table.setItem(2, 0, QTableWidgetItem("False"))
        self.pheno_table.setItem(2, 1, QTableWidgetItem("True"))
        self.pheno_table.setItem(3, 0, QTableWidgetItem("False"))
        self.pheno_table.setItem(3, 1, QTableWidgetItem("False"))
        self.pheno_table.setColumnWidth(0, int(self.pheno_table.width() / 2))
        self.pheno_table.setColumnWidth(1, int(self.pheno_table.width() / 2))

        self.clear_phenotype = QPushButton('Clear table', parent=self.pheno_box)
        self.clear_phenotype.clicked.connect(self.clear)
        self.clear_phenotype.setGeometry(QRect(400, 400, 170, 30))
        self.clear_phenotype.setEnabled(False)

        self.add_phenotype = QPushButton('Add new phenotype', parent=self.pheno_box)
        self.add_phenotype.clicked.connect(self.add_row)
        self.add_phenotype.setGeometry(QRect(220, 400, 170, 30))
        self.add_phenotype.setEnabled(False)

        # Create box containing heatmap settings
        self.heatmap_box = QGroupBox("Heatmap showing KI/KO perturbation results", self)
        self.heatmap_box.setGeometry(QRect(1220, 520, 580, 110))
        self.heatmap_box.setFont(Bfont)
        self.heatmap_box.setAutoFillBackground(False)
        self.heatmap_box.setFlat(True)
        self.heatmap_box.setCheckable(True)
        self.heatmap_box.setChecked(False)
        self.heatmap_box.setStyleSheet("QGroupBox {border: 1px solid gray; border-radius: 5px;  }")

        self.dist_from_text = QLabel("Distance from", parent=self.heatmap_box)
        self.dist_from_text.setGeometry(QRect(10, 30, 300, 25))
        self.dist_from_combo = QComboBox(parent=self.heatmap_box)
        self.dist_from_combo.setGeometry(QRect(275, 30, 300, 25))
        self.dist_from_combo.setToolTip("<td align='justify'; width=400><b>Initial state</b>  from which Hamming"
                                        " distance will be calculated and used in to order the histogram columns</td>")

        self.omit_text = QLabel("Omit attractor perturbation", parent=self.heatmap_box)
        self.omit_text.setGeometry(QRect(10, 70, 300, 25))
        self.omit_combo = QComboBox(parent=self.heatmap_box)
        self.omit_combo.setGeometry(QRect(275, 70, 300, 25))
        self.omit_combo.setToolTip("<td align='justify'; width=400>Perturbations of <b>initial states</b>"
                                   " omited from the histogram </td>")

        # Create box containing pathway activation visualization settings
        self.path_activ_box = QGroupBox("Pathway activation plot", self)
        self.path_activ_box.setGeometry(QRect(1220, 640, 580, 60))
        self.path_activ_box.setFont(Bfont)
        self.path_activ_box.setAutoFillBackground(False)
        self.path_activ_box.setFlat(True)
        self.path_activ_box.setCheckable(True)
        self.path_activ_box.setChecked(False)
        self.path_activ_box.setStyleSheet("QGroupBox {border: 1px solid gray; border-radius: 5px;  }")

        self.path_map_button = QPushButton("Node-to-pathway mapping file", parent=self.path_activ_box)
        self.path_map_button.clicked.connect(self.select_path_map_file)
        self.path_map_button.setGeometry(QRect(10, 20, 180, 25))
        self.path_map_button.setToolTip("<td align='justify'; width=400>Select <b>pathway mapping file</b>  mapping "
                                        "nodes to pathways to be use for pathway activation plotting</td>")

        self.path_map_line = QLineEdit(self.path_activ_box)
        self.path_map_line.setGeometry(QRect(195, 20, 370, 25))
        self.path_map_line.setToolTip("<td align='justify'; width=400>Input file mapping nodes to pathways to be used"
                                      "for pathway activation plotting</td>")

        self.run_button = QPushButton('Run simulation', self)
        self.run_button.clicked.connect(self.get_output)
        self.run_button.setShortcut('Ctrl+R')
        self.run_button.setGeometry(QRect(1235, 710, 550, 30))
        self.run_button.setEnabled(False)
        self.show()

    def open_directory(self):
        directory = QFileDialog.getExistingDirectory(self, "Get Dir Path")
        self.pheno_box.setChecked(True)
        self.input_box.setChecked(True)
        self.sim_box.setChecked(True)
        self.perturb_box.setChecked(True)
        self.run_button.setEnabled(True)
        self.add_phenotype.setEnabled(True)
        self.clear_phenotype.setEnabled(True)
        self.folder_line.setText(directory)
        self.input_file_table(directory)

        files = list()
        for (dirpath, dirnames, filenames) in os.walk(directory):
            if "01_Attractors" in dirpath:
                files += [file for file in filenames if ".txt" in file]

        if "attractorList.txt" in files:
            self.attractor_file_line.setText("attractorList.txt")

    def select_file(self):
        fname, _ = QFileDialog.getOpenFileName(self, 'Open file', self.folder_line.text())
        self.attractor_file_line.setText(fname.split("/")[-1])

    def select_path_map_file(self):
        fname, _ = QFileDialog.getOpenFileName(self, 'Open file', self.folder_line.text())
        self.path_map_line.setText(fname)

    def change_iterations(self):
        if self.sim_mode_combo.currentIndex() > 0:
            self.iterate_spin.setRange(5, 100000)
            self.iterate_spin.setSingleStep(50)
            self.noise_spin.setValue(0.02)
        else:
            self.iterate_spin.setRange(1, 100000)
            self.noise_spin.setValue(100 / self.steps_spin.value())

    def input_file_table(self, path):
        files = list()
        for (dirpath, dirnames, filenames) in os.walk(path):
            if "02_Initial states" in dirpath:
                files += [file for file in filenames if ".txt" in file]

        # Create table
        for file in files:
            rowPosition = self.init_file_table.rowCount()
            self.init_file_table.insertRow(rowPosition)
            self.init_file_table.setItem(rowPosition, 1, QTableWidgetItem(file))
            if "_" in file:
                pheno = file.split("_")[1].split(".txt")[0]
            else:
                pheno = file.split(".txt")[0]

            self.init_file_table.setItem(rowPosition, 0, QTableWidgetItem(pheno))
            self.dist_from_combo.addItem(pheno)
            self.omit_combo.addItem(pheno)
        if self.omit_combo.currentText() == self.dist_from_combo.currentText():
            self.omit_combo.setCurrentIndex(1)

        text = util.fopen(file, path)

        model = __init__.Model(text, mode="sync")
        model.initialize(missing=util.false)
        model.iterate(steps=1)
        global nodes
        nodes = model.nodes
        nodes = sorted(nodes)

        self.change_node_box()

        if "AJ" in nodes and "VIM" in nodes:
            self.pheno_table.setHorizontalHeaderLabels(["AJ", "VIM"])
        elif "AJ" in nodes and "Vimentin" in nodes:
            self.pheno_table.setHorizontalHeaderLabels(["AJ", "Vimentin"])
        elif "Ecadherin" in nodes and "Vimentin" in nodes:
            self.pheno_table.setHorizontalHeaderLabels(["Ecadherin", "Vimentin"])
        elif "Ecadherin" in nodes:
            self.pheno_table.setHorizontalHeaderLabels(["Ecadherin", "SNAI1_nuc"])

    def change_node_box(self):
        global nodes
        self.node_table.setColumnCount(2)
        self.node_table.setHorizontalHeaderLabels(["Node", "Perturbed"])
        for node in nodes:
            rowPosition = self.node_table.rowCount()
            self.node_table.insertRow(rowPosition)
            self.node_table.setItem(rowPosition, 0, QTableWidgetItem(node))
            self.node_table.setCellWidget(rowPosition, 1, QCheckBox())

        header = self.node_table.horizontalHeader()
        header.setSectionResizeMode(1, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(0, QHeaderView.Stretch)
        self.perturb_combo_spin.setRange(1, len(nodes))

    def contextMenuEvent(self, event):
        self.menu = QMenu(self.node_table)

        select_all = self.menu.addAction("Select all")
        reset_all = self.menu.addAction("Reset")

        action = self.menu.exec_(self.mapToGlobal(event.pos()))

        if action == select_all:
            for i in range(0, self.node_table.rowCount()):
                self.node_table.cellWidget(i, 1).setChecked(True)
        elif action == reset_all:
            for i in range(0, self.node_table.rowCount()):
                self.node_table.cellWidget(i, 1).setChecked(False)

    def perturb_info(self):
        if self.perturb_type_combo.currentIndex() == 0:
            self.perturb_combo_text.setEnabled(False)
            self.perturb_combo_spin.setEnabled(False)
        else:
            self.perturb_combo_text.setEnabled(True)
            self.perturb_combo_spin.setEnabled(True)
            self.node_box.setChecked(True)

        if self.perturb_type_combo.currentIndex() == 1:
            self.noise_text.setEnabled(True)
            self.noise_spin.setEnabled(True)
        else:
            self.noise_text.setEnabled(False)
            self.noise_spin.setEnabled(False)
            self.heatmap_box.setChecked(True)
            self.heatmap_box.setChecked(True)

    def clear(self):
        self.pheno_table.clear()

    def add_row(self):
        pheno_dialog = NewPheno(self)
        out = pheno_dialog.exec_()
        if out == QDialog.Accepted:
            pheno = pheno_dialog.message()
            pheno_dialog.deleteLater()

    # To-do: add data to table

    def get_output(self):
        self.run_button.setEnabled(False)

        folder = self.folder_line.text()
        init_files = {}
        for row in range(self.init_file_table.rowCount()):
            if self.init_file_table.item(row, 0) is not None:
                init_files[str(self.init_file_table.item(row, 0).text())] = str(
                    self.init_file_table.item(row, 1).text())
        sim_mode = list(sim_modes.keys())[list(sim_modes.values()).index(self.sim_mode_combo.currentText())]
        perturb_type = self.perturb_type_combo.currentText()
        perturb_comb = self.perturb_combo_spin.value()
        iterations = self.iterate_spin.value()
        steps = self.steps_spin.value()
        if self.noise_spin.isEnabled():
            noise = self.noise_spin.value()
        else:
            noise = None
        attractor_file = self.attractor_file_line.text()

        if len(attractor_file) == 0:
            attractor_folder = os.path.normpath(folder + "/01_Attractors")
            attractor_file = "attractorList.txt"
            try:
                os.makedirs(attractor_folder)
            except:
                pass

            with open(os.path.normpath(attractor_folder + "/" + attractor_file), 'w') as fp:
                pass

        node_perturbations = []
        for i in range(0, self.node_table.rowCount()):
            if self.node_table.cellWidget(i, 1).isChecked():
                node = str(self.node_table.item(i, 0).text())
                node_perturbations.append(node)

        pheno = []
        nodes = []
        node_states = []
        for i in range(0, self.pheno_table.rowCount()):
            pheno.append(deepcopy(self.pheno_table.takeVerticalHeaderItem(i).text()))
            states = []
            for j in range(0, self.pheno_table.columnCount()):
                if len(nodes) < self.pheno_table.columnCount():
                    nodes.append(deepcopy(self.pheno_table.takeHorizontalHeaderItem(j).text()))
                states.append(deepcopy(self.pheno_table.item(i, j).text()))

            node_states.append(dict(zip(nodes, states)))

        phenotypes = dict(zip(pheno, node_states))

        if self.heatmap_box.isChecked():
            dist_from = self.dist_from_combo.currentText()
            omit = self.omit_combo.currentText()
        else:
            dist_from = None
            omit = None
        
        if self.path_activ_box.isChecked() and len(self.path_map_line.text()) != 0:
            node_to_pathway_map = self.path_map_line.text()
        else:
            node_to_pathway_map = None

        simulations.simulation(folder, init_files, sim_mode, perturb_type, perturb_comb, iterations, steps,
                               phenotype=phenotypes, attractor_file=attractor_file, noise=noise,
                               perturbed_nodes=node_perturbations, dist_from=dist_from, omit=omit,
                               pathway_mapping_file=node_to_pathway_map)
        self.close()


if __name__ == '__main__':
    app = QApplication(sys.argv)
    dark_palette = QPalette()

    dark_palette.setColor(QPalette.Window, QColor(53, 53, 53))
    dark_palette.setColor(QPalette.WindowText, Qt.white)
    dark_palette.setColor(QPalette.Base, QColor(25, 25, 25))
    dark_palette.setColor(QPalette.AlternateBase, QColor(53, 53, 53))
    dark_palette.setColor(QPalette.ToolTipBase, Qt.white)
    dark_palette.setColor(QPalette.ToolTipText, Qt.white)
    dark_palette.setColor(QPalette.Text, Qt.white)
    dark_palette.setColor(QPalette.Button, QColor(53, 53, 53))
    dark_palette.setColor(QPalette.ButtonText, Qt.white)
    dark_palette.setColor(QPalette.BrightText, Qt.red)
    dark_palette.setColor(QPalette.Link, QColor(42, 130, 218))
    dark_palette.setColor(QPalette.Highlight, QColor(42, 130, 218))
    dark_palette.setColor(QPalette.HighlightedText, Qt.black)

    app.setStyle('Fusion')
    # app.setPalette(dark_palette)
    ex = App()
    sys.exit(app.exec_())
