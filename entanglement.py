# General
import numpy as np

# Qiskit imports
from qiskit import QuantumCircuit
from qiskit.circuit import Parameter
from qiskit.quantum_info import SparsePauliOp

# Qiskit Runtime imports
from qiskit_ibm_runtime import QiskitRuntimeService
from qiskit_ibm_runtime import EstimatorV2 as Estimator

# Plotting routines
import matplotlib.pyplot as plt
import matplotlib.ticker as tck

# Take API key from IBM composer
QiskitRuntimeService.save_account(overwrite=True, channel="ibm_quantum", token="e169403d0ac08a5e1b5b8e4aba15586ae07ce44f61062f76203dc7b6a659c8b42b2e60fea9b34d03c1b2a1d96c09cd6e9a62cafd389309d3e070ead34d3326f2")

# To run on hardware, select the backend with the fewest number of jobs in the queue
service = QiskitRuntimeService(channel="ibm_quantum")
backend = service.least_busy(operational=True, simulator=False, min_num_qubits=127)
print(backend.name)

# ISA Optimization, circuit must conform to specific instructions
from qiskit.transpiler.preset_passmanagers import generate_preset_pass_manager
target = backend.target
pm = generate_preset_pass_manager(target=target, optimization_level=3)

# Variables
theta = Parameter("$\\theta$")
number_of_phases = 21
phases = np.linspace(0, 2 * np.pi, number_of_phases)
individual_phases = [[ph] for ph in phases]

# Observables
observable1 = SparsePauliOp.from_list([("ZZ", 1), ("ZX", -1), ("XZ", 1), ("XX", 1)])
observable2 = SparsePauliOp.from_list([("ZZ", 1), ("ZX", 1), ("XZ", -1), ("XX", 1)])

# Setup circuit
chsh_circuit = QuantumCircuit(2)
chsh_circuit.h(0)
chsh_circuit.cx(0, 1)
chsh_circuit.ry(theta, 0)
fig = chsh_circuit.draw(output="mpl", idle_wires=False, style="iqp")
fig.savefig('bell_inequality.png')

# ISA Optimized Circuit
chsh_isa_circuit = pm.run(chsh_circuit)
isa_observable1 = observable1.apply_layout(layout=chsh_isa_circuit.layout)
isa_observable2 = observable2.apply_layout(layout=chsh_isa_circuit.layout)

# Save the circuit as an image
fig = chsh_isa_circuit.draw(output="mpl", idle_wires=False, style="iqp")
fig.savefig('bell_inequality_optimized.png')

# Execute using Qiskit primitives
estimator = Estimator(mode=backend)
pub = (
    chsh_isa_circuit, # ISA circuit
    [[isa_observable1], [isa_observable2]], # ISA Observables
    individual_phases, # Parameter values
)
job_result = estimator.run(pubs=[pub]).result()

# Use the estimator to return expectation values for both of the observables
chsh1_est = job_result[0].data.evs[0]
chsh2_est = job_result[0].data.evs[1]

# Print graph of 
fig, ax = plt.subplots(figsize=(10, 6))

# results from hardware
ax.plot(phases / np.pi, chsh1_est, "o-", label="CHSH1", zorder=3)
ax.plot(phases / np.pi, chsh2_est, "o-", label="CHSH2", zorder=3)

# classical bound +-2
ax.axhline(y=2, color="0.9", linestyle="--")
ax.axhline(y=-2, color="0.9", linestyle="--")

# quantum bound, +-2√2
ax.axhline(y=np.sqrt(2) * 2, color="0.9", linestyle="-.")
ax.axhline(y=-np.sqrt(2) * 2, color="0.9", linestyle="-.")
ax.fill_between(phases / np.pi, 2, 2 * np.sqrt(2), color="0.6", alpha=0.7)
ax.fill_between(phases / np.pi, -2, -2 * np.sqrt(2), color="0.6", alpha=0.7)

# set x tick labels to the unit of pi
ax.xaxis.set_major_formatter(tck.FormatStrFormatter("%g $\\pi$"))
ax.xaxis.set_major_locator(tck.MultipleLocator(base=0.5))

# set labels, and legend
plt.xlabel("Theta")
plt.ylabel("CHSH witness")
plt.legend()

# Save as png
fig.savefig('results_graph.png')